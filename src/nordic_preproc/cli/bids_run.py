from __future__ import annotations

import argparse
import os
from pathlib import Path

import nibabel as nib

from ..backends import NordicArgs
from ..backends.matlab_engine import MatlabEngineBackend
from ..backends.mcr import MCRBackend
from ..noise import find_noise_scans
from ..nifti_ops import split_4d_nifti, gzip_nii
from ..bids import (
    write_dataset_description,
    iter_bids_func_files,
    corresponding_phase_file,
    DerivativePaths,
    outputs_exist,
    save_with_json,
)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Run NORDIC preprocessing on a BIDS dataset.")
    p.add_argument("bids_root", help="Path to BIDS root directory")

    backend = p.add_mutually_exclusive_group(required=True)
    backend.add_argument("--matlab", action="store_true", help="Use MATLAB engine backend")
    backend.add_argument("--mcr", action="store_true", help="Use MATLAB Compiler Runtime backend")

    p.add_argument("--nordic_path", default="", help="Path to the NORDIC MATLAB scripts (for --matlab)")
    p.add_argument("--mcr_path", default="", help="Path to MATLAB Compiler Runtime directory (for --mcr)")
    p.add_argument("--nordic_mcr_path", default="./nordic_mcr/", help="Path to compiled NORDIC directory (for --mcr)")

    p.add_argument("--temporal_phase", type=int, default=1, help="Temporal phase argument for NORDIC")
    p.add_argument("--phase_filter_width", type=float, default=10.0, help="Phase filter width argument for NORDIC")
    p.add_argument("--mad_thresh", type=float, default=50, help="MAD multiplier for noise scan detection")
    p.add_argument("--overwrite", action="store_true", help="Overwrite existing outputs")
    return p


def main(argv=None) -> None:
    args = build_parser().parse_args(argv)
    bids_root = Path(args.bids_root)
    p.add_argument(
    "--participant-label",
    nargs="+",
    default=None,
    help="One or more participant labels (e.g., 01 02 or sub-01 sub-02). If omitted, processes all participants.",
    )
    p.add_argument(
        "--session-label",
        nargs="+",
        default=None,
        help="One or more session labels (e.g., 01 or ses-01). If omitted, processes all sessions.",
    )
    deriv_root = bids_root / "derivatives" / "nordic"
    deriv_root.mkdir(parents=True, exist_ok=True)
    write_dataset_description(deriv_root)

    if args.matlab:
        backend = MatlabEngineBackend(nordic_path=args.nordic_path)
    else:
        backend = MCRBackend(mcr_path=args.mcr_path, nordic_mcr_path=args.nordic_mcr_path)

    func_files = list(
        iter_bids_func_files(
            bids_root,
            participant_labels=args.participant_label,
            session_labels=args.session_label,
        )
    )

    if not func_files:
        print("No functional files found matching: sub-*/ses-*/func/*_bold.nii.gz")
        return

    for m_im in func_files:
        ph_im = corresponding_phase_file(m_im)
        if not ph_im.exists():
            print(f"Skipping {m_im}, no phase file found")
            continue

        rel_path = m_im.relative_to(bids_root)
        out_dir = deriv_root / rel_path.parent
        out_dir.mkdir(parents=True, exist_ok=True)

        base = m_im.name.replace("_bold.nii.gz", "")
        paths = DerivativePaths(out_dir=out_dir, base=base)

        det = find_noise_scans(str(m_im), mad_thresh=args.mad_thresh)
        noise_inds = det.noise_indices
        noise_present = len(noise_inds) > 0

        if (not args.overwrite) and outputs_exist(paths, noise_present=noise_present):
            print(f"Skipping {m_im}, outputs already exist.")
            continue

        nordic_args = NordicArgs(
            temporal_phase=args.temporal_phase,
            phase_filter_width=args.phase_filter_width,
            noise_volume_last=int(len(noise_inds)),
            dirout=str(out_dir) + "/",
        )

        backend.run(str(m_im), str(ph_im), base, nordic_args)

        nordic_out_gz = out_dir / f"{base}.nii.gz"
        nordic_out = out_dir / f"{base}.nii"
        if nordic_out.exists():
            nordic_file = gzip_nii(nordic_out)
        elif nordic_out_gz.exists():
            nordic_file = nordic_out_gz
        else:
            raise FileNotFoundError(f"No NORDIC output found for {base}")

        func_data, noise_data = split_4d_nifti(str(m_im), noise_inds)
        func_data_nordic, noise_data_nordic = split_4d_nifti(str(nordic_file), noise_inds)

        # Remove full NORDIC file after splitting (preserves original behavior)
        if nordic_file.exists():
            nordic_file.unlink()

        affine = nib.load(str(m_im)).affine
        json_file = m_im.with_suffix("").with_suffix(".json")

        if noise_data is not None:
            save_with_json(func_data, affine, paths.functional_raw, json_file,
                           "Functional volumes (noise removed, raw)")
            save_with_json(func_data_nordic, affine, paths.functional_nordic, json_file,
                           "Functional volumes (noise removed, NORDIC denoised)")
            save_with_json(noise_data, affine, paths.noise_raw, json_file,
                           "Noise volumes (raw, split by variance threshold)")
            save_with_json(noise_data_nordic, affine, paths.noise_nordic, json_file,
                           "Noise volumes (NORDIC denoised)")
        else:
            print(f"No noise scans detected for {m_im}")
            save_with_json(func_data_nordic, affine, paths.functional_nordic, json_file,
                           "Functional volumes (NORDIC denoised, no noise scans detected)")

if __name__ == "__main__":
    main()

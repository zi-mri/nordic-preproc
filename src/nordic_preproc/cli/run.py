from __future__ import annotations

import argparse
import os
from pathlib import Path

import nibabel as nib

from ..noise import find_noise_scans
from ..nifti_ops import split_4d_nifti, save_nifti, gzip_nii
from ..backends import NordicArgs
from ..backends.matlab_engine import MatlabEngineBackend
from ..backends.mcr import MCRBackend


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Run NORDIC preprocessing on a single magnitude+phase pair.")
    p.add_argument("magnitude_image", help="Path to the magnitude NIfTI image (.nii or .nii.gz)")
    p.add_argument("phase_image", help="Path to the phase NIfTI image (.nii or .nii.gz)")

    backend = p.add_mutually_exclusive_group(required=True)
    backend.add_argument("--matlab", action="store_true", help="Use MATLAB engine backend")
    backend.add_argument("--mcr", action="store_true", help="Use MATLAB Compiler Runtime backend")

    p.add_argument("--nordic_path", default="", help="Path to NORDIC MATLAB scripts (for --matlab)")
    p.add_argument("--mcr_path", default="", help="Path to MATLAB Compiler Runtime directory (for --mcr)")
    p.add_argument("--nordic_mcr_path", default="./nordic_mcr/", help="Path to compiled NORDIC directory (for --mcr)")

    p.add_argument("--temporal_phase", type=int, default=1, help="Temporal phase argument for NORDIC")
    p.add_argument("--phase_filter_width", type=float, default=10.0, help="Phase filter width argument for NORDIC")
    p.add_argument("--mad_thresh", type=float, default=50, help="MAD multiplier for noise scan detection")

    p.add_argument("--output_dir", default=None, help="Output directory (default: magnitude image directory)")
    p.add_argument("--output_prefix", default="NORDIC_", help="Prefix for NORDIC base output name")
    return p


def main(argv=None) -> None:
    args = build_parser().parse_args(argv)

    m_im = args.magnitude_image
    ph_im = args.phase_image

    if args.output_dir is None:
        out_dir = Path(os.path.dirname(m_im))
    else:
        out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    base = args.output_prefix + Path(m_im).name.replace(".nii.gz", "").replace(".nii", "")
    # Detect noise scans from magnitude
    det = find_noise_scans(m_im, mad_thresh=args.mad_thresh)
    noise_inds = det.noise_indices
    print(f"Found {len(noise_inds)} noise scans: {noise_inds}")

    nordic_args = NordicArgs(
        temporal_phase=args.temporal_phase,
        phase_filter_width=args.phase_filter_width,
        noise_volume_last=int(len(noise_inds)),
        dirout=str(out_dir) + "/",
    )

    if args.matlab:
        backend = MatlabEngineBackend(nordic_path=args.nordic_path)
    else:
        backend = MCRBackend(mcr_path=args.mcr_path, nordic_mcr_path=args.nordic_mcr_path)

    backend.run(m_im, ph_im, base, nordic_args)

    # NORDIC output may be .nii or .nii.gz depending on MATLAB script settings
    nordic_nii = out_dir / f"{base}.nii"
    nordic_niigz = out_dir / f"{base}.nii.gz"
    if nordic_nii.exists():
        nordic_file = gzip_nii(nordic_nii)
    elif nordic_niigz.exists():
        nordic_file = nordic_niigz
    else:
        raise FileNotFoundError(f"Expected NORDIC output not found at {nordic_nii} or {nordic_niigz}")

    functional_raw, noise_raw = split_4d_nifti(m_im, noise_inds)
    functional_nordic, noise_nordic = split_4d_nifti(str(nordic_file), noise_inds)

    affine = nib.load(m_im).affine
    if noise_raw is not None:
        save_nifti(functional_raw, affine, out_dir / "functional_data_raw.nii.gz")
        save_nifti(functional_nordic, affine, out_dir / "functional_data_nordic.nii.gz")
        save_nifti(noise_raw, affine, out_dir / "noise_data_raw.nii.gz")
        save_nifti(noise_nordic, affine, out_dir / "noise_data_nordic.nii.gz")
    else:
        print("No noise scans detected; outputs will contain only NORDIC functional split.")
        save_nifti(functional_nordic, affine, out_dir / "functional_data_nordic.nii.gz")

    # Optional: remove the full NORDIC output after splitting (BIDS script did this)
    # Commented out by default for single-run mode to aid debugging.
    # nordic_file.unlink()

if __name__ == "__main__":
    main()

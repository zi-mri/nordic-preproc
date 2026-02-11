from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import nibabel as nib

from .noise import find_noise_scans
from .nifti_ops import split_4d_nifti, save_nifti, gzip_nii


@dataclass(frozen=True)
class DerivativePaths:
    out_dir: Path
    base: str

    @property
    def functional_raw(self) -> Path:
        return self.out_dir / f"{self.base}_desc-functional_bold.nii.gz"

    @property
    def functional_nordic(self) -> Path:
        return self.out_dir / f"{self.base}_desc-functional-nordic_bold.nii.gz"

    @property
    def noise_raw(self) -> Path:
        return self.out_dir / f"{self.base}_desc-noise_bold.nii.gz"

    @property
    def noise_nordic(self) -> Path:
        return self.out_dir / f"{self.base}_desc-noise-nordic_bold.nii.gz"


def write_dataset_description(deriv_root: Path) -> None:
    desc_file = deriv_root / "dataset_description.json"
    if desc_file.exists():
        return
    desc = {
        "Name": "NORDIC Denoising",
        "BIDSVersion": "1.9.0",
        "PipelineDescription": {
            "Name": "NORDIC",
            "Version": "1.0",
            "Description": "NORDIC denoising applied to fMRI magnitude/phase images",
        },
        "GeneratedBy": [
            {
                "Name": "nordic-preproc",
                "Version": "0.1.0",
                "Description": "Custom Python wrapper for MATLAB NIFTI_NORDIC pipeline",
            }
        ],
        "SourceDatasets": [{"URL": "file://../..", "Description": "Raw BIDS dataset"}],
    }
    desc_file.parent.mkdir(parents=True, exist_ok=True)
    with open(desc_file, "w") as f:
        json.dump(desc, f, indent=4)


def save_with_json(data, affine, out_path: Path, json_file: Path, description: str) -> None:
    save_nifti(data, affine, out_path)
    meta = {}
    if json_file.exists():
        with open(json_file, "r") as f:
            meta = json.load(f)
    meta["Description"] = description
    json_out = out_path.with_suffix("").with_suffix(".json")
    with open(json_out, "w") as f:
        json.dump(meta, f, indent=4)


def outputs_exist(paths: DerivativePaths, noise_present: bool) -> bool:
    expected = [paths.functional_nordic] if not noise_present else [
        paths.functional_raw,
        paths.functional_nordic,
        paths.noise_raw,
        paths.noise_nordic,
    ]
    return all(p.exists() for p in expected)


def iter_bids_func_files(bids_root: Path):
    # Mirrors original: sub-*/ses-*/func/*_bold.nii.gz
    for m_im in sorted(bids_root.glob("sub-*/ses-*/func/*_bold.nii.gz")):
        if "part-phase" in m_im.name:
            continue
        yield m_im


def corresponding_phase_file(magnitude_file: Path) -> Path:
    return magnitude_file.with_name(magnitude_file.name.replace("_bold.nii.gz", "_part-phase_bold.nii.gz"))

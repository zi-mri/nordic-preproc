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


from typing import Iterable, Optional, Sequence

def _normalize_bids_labels(labels: Optional[Sequence[str]], prefix: str) -> Optional[list[str]]:
    """Normalize labels so user can pass either '01' or 'sub-01' (or 'ses-01')."""
    if not labels:
        return None
    out = []
    for lab in labels:
        lab = lab.strip()
        if not lab:
            continue
        if lab.startswith(prefix):
            out.append(lab)
        else:
            out.append(f"{prefix}{lab}")
    return out or None


def iter_bids_func_files(
    bids_root: Path,
    participant_labels: Optional[Sequence[str]] = None,
    session_labels: Optional[Sequence[str]] = None,
) -> Iterable[Path]:
    """Yield magnitude BOLD files in a BIDS dataset, optionally filtered by sub/ses.

    - Handles datasets with sessions (sub-*/ses-*/func) and without sessions (sub-*/func)
    - Skips phase files (part-phase) automatically
    """
    subs = _normalize_bids_labels(participant_labels, "sub-")
    sess = _normalize_bids_labels(session_labels, "ses-")

    # Build candidate patterns
    patterns: list[str] = []

    if subs is None:
        sub_patterns = ["sub-*"]
    else:
        sub_patterns = subs

    # If session labels not provided, include both "with ses" and "no ses" patterns
    if sess is None:
        for s in sub_patterns:
            patterns.append(f"{s}/ses-*/func/*_bold.nii.gz")
            patterns.append(f"{s}/func/*_bold.nii.gz")
    else:
        for s in sub_patterns:
            for se in sess:
                patterns.append(f"{s}/{se}/func/*_bold.nii.gz")

    # Yield files
    for pat in patterns:
        for m_im in sorted(bids_root.glob(pat)):
            if "part-phase" in m_im.name:
                continue
            yield m_im



def corresponding_phase_file(magnitude_file: Path) -> Path:
    return magnitude_file.with_name(magnitude_file.name.replace("_bold.nii.gz", "_part-phase_bold.nii.gz"))

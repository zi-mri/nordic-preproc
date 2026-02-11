from __future__ import annotations

from pathlib import Path
from typing import Optional, Tuple

import gzip
import nibabel as nib
import numpy as np
import shutil


def split_4d_nifti(nifti_file: str, noise_inds: np.ndarray) -> Tuple[np.ndarray, Optional[np.ndarray]]:
    """Split a 4D NIfTI into functional volumes and noise volumes.

    The original scripts assume noise volumes (if present) are appended at the end.
    We preserve that behavior by splitting at noise_inds[0].

    Parameters
    ----------
    nifti_file:
        Path to 4D NIfTI.
    noise_inds:
        Indices of noise volumes along the 4th dimension.

    Returns
    -------
    (functional_data, noise_data or None)
    """
    img = nib.load(nifti_file)
    data = img.get_fdata()
    if len(noise_inds) > 0:
        noise_start_index = int(noise_inds[0])
        functional_data = data[..., :noise_start_index]
        noise_data = data[..., noise_start_index:]
        return functional_data, noise_data
    return data, None


def save_nifti(data: np.ndarray, affine, out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    nib.save(nib.Nifti1Image(data, affine), str(out_path))


def gzip_nii(nii_path: Path) -> Path:
    """Compress a .nii file to .nii.gz and remove the original .nii."""
    if str(nii_path).endswith(".gz"):
        return nii_path
    gz_path = Path(str(nii_path) + ".gz")
    with open(nii_path, "rb") as f_in, gzip.open(gz_path, "wb") as f_out:
        shutil.copyfileobj(f_in, f_out)
    nii_path.unlink()
    return gz_path

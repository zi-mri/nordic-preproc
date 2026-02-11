import numpy as np
import nibabel as nib
from pathlib import Path

from nordic_preproc.noise import find_noise_scans


def test_find_noise_scans_detects_low_variance(tmp_path: Path):
    # Make a 4D dataset where last 3 vols are near-constant (low variance)
    rng = np.random.default_rng(0)
    data = rng.normal(size=(5, 5, 5, 10))
    data[..., 7:] = 0.001  # low variance noise volumes
    img = nib.Nifti1Image(data, affine=np.eye(4))
    p = tmp_path / "test.nii.gz"
    nib.save(img, str(p))

    res = find_noise_scans(str(p), mad_thresh=10)
    assert len(res.noise_indices) >= 1
    assert res.noise_indices[0] >= 7

import numpy as np
import nibabel as nib
from pathlib import Path

from nordic_preproc.nifti_ops import split_4d_nifti


def test_split_4d_nifti(tmp_path: Path):
    data = np.zeros((2, 2, 2, 6))
    data[..., :4] = 1.0
    data[..., 4:] = 2.0
    img = nib.Nifti1Image(data, affine=np.eye(4))
    p = tmp_path / "test.nii.gz"
    nib.save(img, str(p))

    func, noise = split_4d_nifti(str(p), noise_inds=np.array([4, 5]))
    assert func.shape[-1] == 4
    assert noise.shape[-1] == 2

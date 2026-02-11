from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import nibabel as nib
import numpy as np


@dataclass(frozen=True)
class NoiseDetectionResult:
    noise_indices: np.ndarray
    variances: np.ndarray
    threshold: float
    mad: float
    median_variance: float


def find_noise_scans(nifti_file: str, mad_thresh: float = 50) -> NoiseDetectionResult:
    """Detect noise scans in a 4D NIfTI by low variance.

    This implements the logic used in the original scripts:
      - compute variance across x/y/z for each volume
      - compute MAD of the variances
      - threshold = median_variance - mad_thresh * mad
      - volumes with variance < threshold are treated as noise scans

    Parameters
    ----------
    nifti_file:
        Path to a 4D NIfTI (typically the magnitude BOLD series).
    mad_thresh:
        Multiplier on MAD for the detection threshold.

    Returns
    -------
    NoiseDetectionResult
        Includes noise indices and diagnostic values.
    """
    img = nib.load(nifti_file)
    data = img.get_fdata()
    variances = np.var(data, axis=(0, 1, 2))
    median_variance = float(np.median(variances))
    mad = float(np.median(np.abs(variances - median_variance)))
    threshold = median_variance - float(mad_thresh) * mad
    noise_indices = np.where(variances < threshold)[0]
    return NoiseDetectionResult(
        noise_indices=noise_indices,
        variances=variances,
        threshold=threshold,
        mad=mad,
        median_variance=median_variance,
    )

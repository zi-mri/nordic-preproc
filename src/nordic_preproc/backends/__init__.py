from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Protocol, Dict, Any


@dataclass(frozen=True)
class NordicArgs:
    temporal_phase: int = 1
    phase_filter_width: float = 10.0
    noise_volume_last: int = 0
    dirout: str = "./"


class NordicBackend(Protocol):
    def run(self, magnitude_nii: str, phase_nii: str, output_base: str, args: NordicArgs) -> None:
        """Run the NORDIC pipeline.

        Parameters
        ----------
        magnitude_nii:
            Path to magnitude image.
        phase_nii:
            Path to phase image.
        output_base:
            Base name used by NORDIC output (no extension).
        args:
            NordicArgs controlling the pipeline.
        """
        ...


def to_matlab_struct_dict(args: NordicArgs) -> Dict[str, Any]:
    # Keep keys compatible with the original MATLAB function signature.
    return {
        "temporal_phase": int(args.temporal_phase),
        "phase_filter_width": float(args.phase_filter_width),
        "DIROUT": str(args.dirout),
        "noise_volume_last": int(args.noise_volume_last),
    }

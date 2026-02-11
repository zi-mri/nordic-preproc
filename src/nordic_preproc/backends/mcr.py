from __future__ import annotations

import subprocess
from pathlib import Path

from . import NordicArgs, to_matlab_struct_dict


class MCRBackend:
    """Backend that runs a compiled NORDIC pipeline using MATLAB Compiler Runtime.

    This mirrors the original preprocess_nordic_mcr.py behavior:
      - calls <nordic_mcr_path>/run_nifti_nordic_pipeline.sh
      - passes MCR directory and other args as positional parameters
    """

    def __init__(self, mcr_path: str, nordic_mcr_path: str):
        self.mcr_path = mcr_path
        self.nordic_mcr_path = nordic_mcr_path

    def run(self, magnitude_nii: str, phase_nii: str, output_base: str, args: NordicArgs) -> None:
        arg_dict = to_matlab_struct_dict(args)
        script_path = str(Path(self.nordic_mcr_path) / "run_nifti_nordic_pipeline.sh")

        command = [
            script_path,
            self.mcr_path,
            magnitude_nii,
            phase_nii,
            output_base,
            str(arg_dict["temporal_phase"]),
            str(arg_dict["phase_filter_width"]),
            str(arg_dict["DIROUT"]),
            str(arg_dict["noise_volume_last"]),
        ]

        try:
            subprocess.run(command, check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as e:  # pragma: no cover
            raise RuntimeError(
                "NORDIC (MCR) failed. See captured stdout/stderr for details."
                f"\nSTDOUT:\n{e.stdout}\nSTDERR:\n{e.stderr}"
            ) from e
        except FileNotFoundError as e:  # pragma: no cover
            raise FileNotFoundError(
                f"Could not find the compiled NORDIC runner script at: {script_path}"
            ) from e

from __future__ import annotations

from . import NordicArgs, to_matlab_struct_dict


class MatlabEngineBackend:
    """Backend that calls MATLAB via matlab.engine.

    Note: we import matlab.engine lazily so the package can be installed on
    machines without MATLAB, as long as this backend isn't used.
    """

    def __init__(self, nordic_path: str):
        self.nordic_path = nordic_path

    def run(self, magnitude_nii: str, phase_nii: str, output_base: str, args: NordicArgs) -> None:
        try:
            import matlab.engine  # type: ignore
        except Exception as e:  # pragma: no cover
            raise RuntimeError(
                "Failed to import matlab.engine. Install/configure the MATLAB Engine API for Python, "
                "or use the MCR backend."
            ) from e

        eng = matlab.engine.start_matlab()
        eng.addpath(self.nordic_path, nargout=0)
        arg_struct = eng.struct(to_matlab_struct_dict(args))
        eng.NIFTI_NORDIC(magnitude_nii, phase_nii, output_base, arg_struct, nargout=0)
        eng.quit()

# nordic-preproc

Lightweight Python wrappers for the **MATLAB NORDIC** denoising pipeline (`NIFTI_NORDIC.m`).

This repo turns the original scripts into:
- a small installable Python package
- two command-line tools:
  - `nordic-run` (single magnitude+phase pair)
  - `nordic-bids` (walk a BIDS dataset and write BIDS-derivatives)

## Installation (recommended for your team)

```bash
conda env create -f env/conda.yml
conda activate nordic-preproc
pip install -e .
```

> `pip install -e .` makes the commands available and keeps edits immediately usable.

## Backends

You must choose a backend for each command:

- **MATLAB engine** (`--matlab`): requires MATLAB + MATLAB Engine API for Python.
- **MCR** (`--mcr`): requires MATLAB Compiler Runtime + compiled NORDIC runner
  (expects `run_nifti_nordic_pipeline.sh` in `--nordic_mcr_path`).

## Usage

### Single run

**MATLAB engine:**
```bash
nordic-run mag_bold.nii.gz phase_part-phase_bold.nii.gz \
  --matlab --nordic_path /path/to/NORDIC_MATLAB/ \
  --output_dir /tmp/nordic_out
```

**MCR:**
```bash
nordic-run mag_bold.nii.gz phase_part-phase_bold.nii.gz \
  --mcr --mcr_path /path/to/MCR --nordic_mcr_path /path/to/compiled_nordic/ \
  --output_dir /tmp/nordic_out
```

Outputs (single-run mode) follow the original scripts:
- `functional_data_nordic.nii.gz`
- and, if noise scans are detected:
  - `functional_data_raw.nii.gz`
  - `noise_data_raw.nii.gz`
  - `noise_data_nordic.nii.gz`

### BIDS dataset

Writes to: `derivatives/nordic/sub-*/ses-*/func/`

```bash
nordic-bids /path/to/bids_root \
  --matlab --nordic_path /path/to/NORDIC_MATLAB/
```

(Use `--mcr ...` similarly.)

By default, it skips runs where outputs already exist; use `--overwrite` to re-run.

## Noise scan detection

Noise volumes are detected using low variance across space:
- variance is computed per-volume (over x/y/z)
- MAD thresholding: `threshold = median(variance) - mad_thresh * MAD(variance)`
- volumes with variance < threshold are treated as noise scans (assumed appended at end)

Tune with `--mad_thresh` if needed.

## Notes

- This repo **does not** redistribute NORDIC itself; it only wraps your local MATLAB code.
- If you want CI later, focus tests on the pure-Python helpers (noise detection, splitting, naming).

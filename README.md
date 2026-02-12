# nordic-preproc

Lightweight Python wrappers for the **MATLAB NORDIC** denoising pipeline (`NIFTI_NORDIC.m`).

This repo includes:
- a small installable Python package
- two command-line tools:
  - `nordic-run` (single magnitude+phase pair)
  - `nordic-bids` (input a BIDS dataset and write BIDS-derivatives)


# Installation

```bash
conda env create -f env/conda.yml
conda activate nordic-preproc
pip install -e .
```

---

# Backend selection

There are two ways to run NORDIC:

---

## 1️⃣ MATLAB backend (`--matlab`) — recommended for most users

Use this if you already have MATLAB installed.

- Works on **macOS, Linux, and Windows**
- Does **not** require WSL on Windows
- Requires installation of the MATLAB Engine API for Python

Example:

```bash
nordic-run mag.nii.gz phase_part-phase_bold.nii.gz \
  --matlab --nordic_path /path/to/NORDIC_MATLAB/
```

### Installing the MATLAB Engine API

Locate your MATLAB installation directory (`MATLABROOT`), then run:

```bash
cd "<MATLABROOT>/extern/engines/python"
python -m pip install .
```

Verify installation:

```bash
python -c "import matlab.engine; print('MATLAB engine OK')"
```

---

## 2️⃣ MATLAB Compiler Runtime backend (`--mcr`)

Use this if you do **not** have a MATLAB license.

- Works on **macOS and Linux**
- On **Windows**, use **WSL** (Windows Subsystem for Linux)
- Requires:
  - MATLAB Compiler Runtime (MCR)
  - Compiled NORDIC distribution containing `run_nifti_nordic_pipeline.sh`

Example:

```bash
nordic-run mag.nii.gz phase_part-phase_bold.nii.gz \
  --mcr \
  --mcr_path /path/to/MCR \
  --nordic_mcr_path /path/to/compiled_nordic/
```

---

# Windows users

- If you have MATLAB → use `--matlab` (recommended).
- If you do not have MATLAB → install WSL and run the `--mcr` backend inside WSL.

Native Windows support for the `.sh` MCR runner is not currently provided.


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

Outputs follow the original scripts:
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

## MATLAB engine (optional)

Most users should use the **MCR** backend. If you prefer `--matlab`, you must install the MATLAB Engine API for Python.

1. Locate your MATLAB installation directory (`MATLABROOT`).

2. Install the engine:

```bash
cd "<MATLABROOT>/extern/engines/python"
python -m pip install .
```

3. Verify:

```bash
python -c "import matlab.engine; print('MATLAB engine OK')"
```


## Notes

- This repo **does not** redistribute NORDIC itself; it only wraps your local MATLAB code.

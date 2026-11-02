# COAST
Collateral Assessment for Strokes via Tabulation, a generic framework for collateral scoring for ischemic stroke incidents
# ISLES-2024 CTA Collateral Labels
[![License: CC BY-NC 4.0](https://img.shields.io/badge/License-CC%20BY--NC%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by-nc/4.0/)
This repository provides ground-truth `MITEFF` and `TAN` scores for leptomeningeal collateral assessment, annotated by two neurologists with 3 and 7 years of experience respectively, on the multimodal [ISLES 2024](https://isles-24.grand-challenge.org/) dataset.

It also provides a script pipeline to (optionally) download the ISLES-2024 stroke CTA dataset, locate each subject's `.nii.gz` volume on disk, join it with the corresponding row from the label CSV, and serialize the result into a ready-to-use manifest (`manifest.pkl`).

This is a contribution from the authors of **COAST: Collateral Assessment for Strokes via Tabulation, a generic framework for collateral scoring in ischemic stroke**.

---

## Table of Contents

- [1. Environment Setup](#1-environment-setup)
- [2. Label CSV Placement](#2-label-csv-placement)
- [3. Usage](#3-usage)
- [4. Output: `manifest.pkl`](#4-output-manifestpkl)

---

## 1. Environment Setup

Create and activate a dedicated conda environment (Python 3.9):

```bash
conda create -n coast_isles24 python=3.9
conda activate coast_isles24
pip install -r requirements.txt
```

---

## 2. Label CSV Placement

> [!CAUTION]
> `labels.csv` must live **in the same directory as the script itself** for `script.py` to work as intended. Do not move it elsewhere (e.g. into the data/output folder), the script will not find it there.

`labels.csv` contains:
- An `ID` column (subject identifier, e.g. `sub-stroke0001`)
- `MITEFF` and `TAN` labels

---

## 3. Usage

### Option A — Download the dataset, then build the manifest

```bash
python build_manifest.py /path/to/output_folder --download
```

With `--download` set, the script first downloads `train.7z` from ISLES-2024 Zenodo record [17652035](https://zenodo.org/records/17652035) into `/path/to/output_folder` and extracts it, before matching files and building the manifest. After extraction, expect the following structure under the target folder:

```
/path/to/output_folder/
├── train.7z
├── raw_data/
│   ├── sub-stroke0001/
│   │   └── ses-01/
│   │       └── sub-stroke0001_ses-01_cta.nii.gz
│   ├── sub-stroke0002/
│   │   └── ses-01/
│   │       └── sub-stroke0002_ses-01_cta.nii.gz
│   └── ...
└── manifest.pkl          <- created by this script
```

### Option B — Data already present locally, build the manifest only

```bash
python build_manifest.py /path/to_existing_data_folder
```

Omitting `--download` skips the fetch/extract step entirely and goes straight to CSV parsing + file matching, searching for `.nii.gz` files under `/path/to_existing_data_folder` (whatever structure it already has).

### CLI Arguments

| Argument     | Required | Description                                                        |
|--------------|----------|----------------------------------------------------------------------|
| `folder`     | Yes      | Path to the target data directory (download destination and/or search root for `.nii.gz` files). |
| `--download` | No       | Flag; if set, downloads and extracts `train.7z` from Zenodo before building the manifest. |

---

## 4. Output: `manifest.pkl`

Saved to `<folder>/manifest.pkl`, where `<folder>` is the same target directory passed on the command line (i.e. `/path/to/output_folder/manifest.pkl` in Option A above).

It is a pickled Python `dict` keyed by integer subject ID. Each value is itself a dict with:
- `cta_path`: absolute path (string) to the subject's `*_cta.nii.gz` file, or an empty string if no match was found.
- One key per label column present in the source CSV (e.g. `MITEFF`, `TAN`), with values as strings taken verbatim from the CSV.

### Example Structure

```python
{
    1: {
        "cta_path": "/Path/to/sub-stroke0001_ses-01_cta.nii.gz",
        "MITEFF": "2.0",
        "TAN": "2.0",
    },
    2: {
        "cta_path": "/Path/to/sub-stroke0002_ses-01_cta.nii.gz",
        "MITEFF": "3.0",
        "TAN": "3.0",
    },
    # ... one entry per subject ...
    189: {
        "cta_path": "/Path/to/sub-stroke0189_ses-01_cta.nii.gz",
        "MITEFF": "3.0",
        "TAN": "3.0",
    },
}
```

### Loading the Manifest

```python
import pickle

with open("manifest.pkl", "rb") as f:
    manifest = pickle.load(f)

sample = manifest[1]
print(sample["cta_path"], sample["MITEFF"], sample["TAN"])
```

## 5. Citation

If you use these labels or this code in your research, please cite our paper:

> **COAST: Collateral Assessment for Strokes via Tabulation, a generic framework for collateral scoring in ischemic stroke.**
> Author A, Author B, Author C. *Journal/Conference Name*, Year. [DOI/arXiv link]

```bibtex
@article{coast2026,
  title   = {COAST: Collateral Assessment for Strokes via Tabulation, a generic framework for collateral scoring in ischemic stroke},
  author  = {Lastname, Firstname and Lastname, Firstname and Lastname, Firstname},
  journal = {Journal Name},
  year    = {2026},
  doi     = {xx.xxxx/xxxxx}
}
```

## 6. License

The collateral labels (`labels.csv`) and the code in this repository are released under the [Creative Commons Attribution-NonCommercial 4.0 International License (CC BY-NC 4.0)](https://creativecommons.org/licenses/by-nc/4.0/).

You are free to:
- **Share**: copy and redistribute the material in any medium or format.
- **Adapt**: remix, transform, and build upon the material.

Under the following terms:
- **Attribution**: You must give appropriate credit by citing the paper above, provide a link to the license, and indicate if changes were made.
- **NonCommercial**: You may not use the material for commercial purposes.

The ISLES 2024 imaging data is **not** redistributed here and remains subject to its own license and terms of use. Please refer to the [Zenodo record](https://zenodo.org/records/17652035) before using it.

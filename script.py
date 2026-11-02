import argparse
import csv
import logging
import os
import pickle
import re
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Union

import py7zr
import requests
from tqdm import tqdm

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def retrieve_and_uncompress(
    url: str, output_folder: Path, filename: str = "train.7z"
) -> None:
    """Download a .7z file from a URL with a progress bar and extract its contents.

    Args:
        url (str): Remote URL of the archive file.
        output_folder (Path): Destination directory for download and extraction.
        filename (str, optional): Name of the archive file. Defaults to "train.7z".
    """
    file_path = output_folder / filename

    if not output_folder.exists():
        output_folder.mkdir(parents=True, exist_ok=True)
        logger.info("Created output directory: %s", output_folder)

    logger.info("Downloading %s from Zenodo...", filename)
    response = requests.get(url, stream=True)
    response.raise_for_status()

    total_size = int(response.headers.get("content-length", 0))

    with open(file_path, "wb") as f, tqdm(
        desc=filename,
        total=total_size,
        unit="B",
        unit_scale=True,
        unit_divisor=1024,
    ) as bar:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)
                bar.update(len(chunk))

    logger.info("Download complete. Extracting %s...", filename)

    shutil.register_unpack_format("7zip", [".7z"], py7zr.unpack_7zarchive)

    try:
        shutil.unpack_archive(file_path, extract_dir=output_folder)
        logger.info("Extraction successful!")
    except Exception as e:
        logger.error("Error during extraction: %s", e)
        logger.warning(
            "Fallback command if memory is exceeded:\n  7z x %s -o%s",
            file_path,
            output_folder,
        )


def get_file_paths(
    path: Union[str, Path],
    file_extensions: List[str] = [".dcm"],
    keyword: Optional[str] = None,
    only_one_per_dir: bool = True,
    case_sensitive: bool = False,
) -> List[Path]:
    """Recursively find matching files with single/compound extensions.

    Args:
        path (Union[str, Path]): Base directory path to search recursively.
        file_extensions (List[str], optional): Extensions to match. Defaults to ['.dcm'].
        keyword (Optional[str], optional): Substring required in the path. Defaults to None.
        only_one_per_dir (bool, optional): Limit to 1 sample per folder. Defaults to True.
        case_sensitive (bool, optional): Case sensitivity for keyword. Defaults to False.

    Returns:
        List[Path]: List of matching resolved Path objects.
    """
    # PEP 308 conditional expression for extension normalization
    normalized_exts = tuple(
        (ext if ext.startswith(".") else f".{ext}").lower()
        for ext in file_extensions
    )

    base_path = Path(path).resolve()
    matched_files: List[Path] = []
    visited_dirs = set()

    # PEP 308 conditional expression for keyword processing
    kw_check = (
        keyword.lower() if (keyword and not case_sensitive) else keyword
    )

    for file_path in base_path.rglob("*"):
        if file_path.is_file():
            parent_dir = file_path.parent

            if only_one_per_dir and parent_dir in visited_dirs:
                continue

            if not file_path.name.lower().endswith(normalized_exts):
                continue

            if kw_check:
                # PEP 308 conditional expression for target string format
                target_str = (
                    str(file_path) if case_sensitive else str(file_path).lower()
                )
                if kw_check not in target_str:
                    continue

            matched_files.append(file_path.resolve())
            visited_dirs.add(parent_dir)

    return matched_files


def get_number(label_name: str) -> int:
    """Extract the first integer sequence found in a string.

    Args:
        label_name (str): Input string containing digits.

    Returns:
        int: Parsed integer value.

    Raises:
        ValueError: If no digit sequence is found.
    """
    match = re.search(r"\d+", label_name)
    if not match:
        raise ValueError(f"No integer found in label_name: '{label_name}'")
    return int(match.group())


def main(path: str, download: bool = False) -> None:
    """Main pipeline execution function.

    Args:
        path (str): Target directory path string.
        download (bool, optional): Whether to download the dataset first. Defaults to False.
    """
    record_id = "17652035"
    filename = "train.7z"
    file_url = (
        f"https://zenodo.org/api/records/{record_id}/files/{filename}/content"
    )

    folder_name = Path(path).resolve()

    if download:
        retrieve_and_uncompress(
            url=file_url, output_folder=folder_name, filename=filename
        )

    script_dir = Path(__file__).resolve().parent
    matching_csvs = get_file_paths(
        path=script_dir, file_extensions=[".csv"], keyword="label"
    )

    if not matching_csvs:
        logger.error("No matching label CSV found in script directory.")
        return

    csv_path = matching_csvs[0]
    logger.info("Using label CSV at: %s", csv_path)

    csv_dict: Dict[str, Dict[str, str]] = {}
    with open(csv_path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            key = row.pop("ID")
            csv_dict[key] = row

    final_dict: Dict[int, Dict[str, str]] = {}

    for key, subdict in tqdm(csv_dict.items(), desc="Constructing manifest"):
        number = get_number(label_name=key)
        found_files = get_file_paths(
            path=folder_name,
            file_extensions=[".nii.gz"],
            keyword=key,
            only_one_per_dir=False,
        )

        # PEP 308 conditional expression to pick path string or empty
        cta_path_str = str(found_files[0]) if found_files else ""

        if number not in final_dict:
            final_dict[number] = {"cta_path": cta_path_str}
            for label, val in subdict.items():
                final_dict[number][label] = val

    pickle_save_path = folder_name / "manifest.pkl"

    with open(pickle_save_path, "wb") as file:
        # Fixed bug: dumped final_dict object instead of file path variable
        pickle.dump(final_dict, file)

    logger.info("Manifest saved successfully to: %s", pickle_save_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Pass a folder path for manifest construction and optionally download ISLES 2024 dataset."
    )
    parser.add_argument("folder", type=str, help="Folder path")
    parser.add_argument(
        "--download", action="store_true", help="Flag for downloading ISLES 24"
    )

    args = parser.parse_args()
    main(path=args.folder, download=args.download)

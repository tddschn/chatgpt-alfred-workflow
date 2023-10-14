#!/usr/bin/env python3
"""
Author : Xinyuan Chen <45612704+tddschn@users.noreply.github.com>
Date   : 2023-05-11
Purpose: Remove ChatGPT data export archives and extracted dirs (in ~/Downloads, by default)
"""

import argparse
from itertools import tee
import sys
from config import (
    downloads_dir,
    chatgpt_data_export_zip_regex_pattern,
    chatgpt_data_export_zip_glob_pattern,
)
from utils import find_files
import zipfile


def get_args():
    """Get command-line arguments"""

    parser = argparse.ArgumentParser(
        description='Remove ChatGPT data export archives and extracted dirs (in ~/Downloads, by default)',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        '-l', '--list-only', help='List only, do not remove', action='store_true'
    )

    return parser.parse_args()


def main():
    """Make a jazz noise here"""

    args = get_args()
    export_data_archive_paths = find_files(
        downloads_dir,
        chatgpt_data_export_zip_glob_pattern,
        regex_pattern=chatgpt_data_export_zip_regex_pattern,
    )
    # zip_file_extracted_dir = (x.parent / x.stem for x in export_data_archive_paths)

    zip_file_extracted_dir = find_files(
        downloads_dir,
        chatgpt_data_export_zip_glob_pattern.removesuffix('.zip'),
        regex_pattern=chatgpt_data_export_zip_regex_pattern.removesuffix('.zip'),
    )
    # print the paths to be removed, ask for confirmation, then remove if confirmed

    f1, f2 = tee(export_data_archive_paths)
    d1, d2 = tee(zip_file_extracted_dir)
    for archive_path, extracted_dir in zip(f1, d1):
        print(archive_path)
        print(extracted_dir)
        # print()

    if args.list_only:
        return

    # ask for confirmation
    confirm_removal = input('Remove the above files and dirs? [y/N] ')
    if confirm_removal.lower() != 'y':
        print('Aborted.')
        return

    # remove
    import shutil

    for archive_path, extracted_dir in zip(f2, d2):
        archive_path.unlink()
        print(f'Removed {archive_path}', file=sys.stderr)
        shutil.rmtree(extracted_dir)
        print(f'Removed {extracted_dir}', file=sys.stderr)


if __name__ == '__main__':
    main()

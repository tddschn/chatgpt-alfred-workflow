#!/usr/bin/env python3
"""
Author : Xinyuan Chen <45612704+tddschn@users.noreply.github.com>
Date   : 2023-05-11
Purpose: Copy the conversations.json latest downloaded ChatGPT data export to destinations
"""

import argparse
from config import (
    chatgpt_exported_conversations_json_path,
    downloads_dir,
    chatgpt_data_export_zip_regex_pattern,
    chatgpt_data_export_zip_glob_pattern,
)
from utils import find_last_added_file
import zipfile


def get_args():
    """Get command-line arguments"""

    parser = argparse.ArgumentParser(
        description='Copy the conversations.json latest downloaded ChatGPT data export to destinations',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    return parser.parse_args()


def main():
    """Make a jazz noise here"""

    get_args()
    zip_file_path = find_last_added_file(
        downloads_dir,
        chatgpt_data_export_zip_glob_pattern,
        regex_pattern=chatgpt_data_export_zip_regex_pattern,
    )
    zip_file_extracted_dir = zip_file_path.parent / zip_file_path.stem
    zip_file_extracted_dir.mkdir(exist_ok=True)

    # unzip the zip file, copy the conversations.json to chatgpt_exported_conversations_json_path
    with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
        zip_ref.extractall(zip_file_extracted_dir)

    conversations_json_path = zip_file_extracted_dir / 'conversations.json'
    # copy the conversations.json to chatgpt_exported_conversations_json_path
    import shutil

    shutil.copyfile(conversations_json_path, chatgpt_exported_conversations_json_path)
    print(
        f'Copied {conversations_json_path} to {chatgpt_exported_conversations_json_path}'
    )


if __name__ == '__main__':
    main()

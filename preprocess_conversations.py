#!/usr/bin/env python3
"""
Author : Xinyuan Chen <45612704+tddschn@users.noreply.github.com>
Date   : 2023-09-12
Purpose: Pre-compute attributes and other data for the conversations
"""

import argparse
import json
from config import (
    pre_computed_rows_json,
    pre_computed_rows_msgpack,
    chatgpt_linear_conversations_json_path,
    alfred_title_max_length,
    generated_dir,
)
from utils import (
    model_slug_to_model_name,
    chatgpt_conversation_id_to_url,
    iso_to_month_day,
    get_model_short_subtitle_suffix_update_item3_kwargs,
)


def get_rows() -> list[dict]:
    linear_conversations: list[dict] = json.loads(
        chatgpt_linear_conversations_json_path.read_text()
    )
    for conversation in linear_conversations:
        conversation['concatenated_messages'] = '\n---\n'.join(
            conversation.pop('linear_messages')
        )
        conversation['model'] = model_slug_to_model_name(conversation.pop('model_slug'))
    return linear_conversations


def search_key_for_rows(row: dict) -> str:
    return ' '.join(
        x
        for _, x in row.items()
        if x
        and isinstance(x, str)
        and not _.startswith('non_key_')
        and not _.startswith('_')
    ).lower()


def get_and_process_rows() -> list[dict]:
    rows = get_rows()
    for row in rows:
        date_short = iso_to_month_day(row['update_time'])
        model = row['model']
        chatgpt_url = chatgpt_conversation_id_to_url(row['id'], 'chatgpt')
        typingmind_url = chatgpt_conversation_id_to_url(row['id'], 'typingmind')
        item3_kwargs = {}
        (
            model_short,
            subtitle_prefix,
        ) = get_model_short_subtitle_suffix_update_item3_kwargs(
            date_short, model, item3_kwargs
        )
        title_suffix = f"""{date_short}{f' ({model_short})' if model_short else ''}"""
        row_title = row.get('title', '') or ''
        num_white_spaces = max(
            2, alfred_title_max_length - len(row_title) - len(title_suffix)
        )
        title = f"""{row_title}{' ' * num_white_spaces}{title_suffix}"""
        # subtitle_remaining_length = (
        #     alfred_subtitle_max_length - len(subtitle_prefix) - 3
        # )
        # message_preview = get_message_preview(alfred_subtitle_max_length)
        row['_title'] = title
        row['_quicklookurl'] = (str(generated_dir / f"{row['id']}.md"),)
        row['_chatgpt_url'] = chatgpt_url
        row['_typingmind_url'] = typingmind_url
        row['_item3_kwargs'] = item3_kwargs
        row['_search_key'] = search_key_for_rows(row)
    return rows


def get_args():
    """Get command-line arguments"""

    parser = argparse.ArgumentParser(
        description='Pre-compute attributes and other data for the conversations',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    return parser.parse_args()


def main():
    """Make a jazz noise here"""

    get_args()
    rows = get_and_process_rows()
    pre_computed_rows_json.write_text(json.dumps(rows, indent=2, ensure_ascii=False))
    print(f'Wrote pre-computed rows to {pre_computed_rows_json}')
    try:
        import msgpack

        pre_computed_rows_msgpack.write_bytes(msgpack.packb(rows))  # type: ignore
        print(f'Wrote pre-computed rows to {pre_computed_rows_msgpack}')
    except ImportError:
        pass


if __name__ == '__main__':
    main()

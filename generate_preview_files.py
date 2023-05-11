#!/usr/bin/env python3
"""
Author : Xinyuan Chen <45612704+tddschn@users.noreply.github.com>
Date   : 2023-05-11
Purpose: Generate preview files for Alfred list filter preview
"""

from textwrap import dedent
from tqdm import tqdm
import argparse
from pathlib import Path
from config import chatgpt_linear_conversations_json_path, generated_dir
from utils import model_slug_to_model_name


def generate_preview_markdown(conversation: dict) -> str:
    title = conversation['title']
    # date_short = iso_to_month_day(conversation['update_time'])
    date_short = conversation['update_time']
    model = model_slug_to_model_name(conversation['model_slug'])
    match model:
        case 'gpt-3.5-turbo':
            model_short = ''
        case 'gpt-4':
            model_short = 'GPT-4'
        case 'plugins':
            model_short = 'Plugins'
        case _:
            model_short = model
    title_suffix = f"""{date_short}{f' ({model_short})' if model_short else ''}"""

    template = """
    # {title}

    <link rel="stylesheet" href="../css/markdown_preview.css">

    {title_suffix}

    ---

    {formatted_messages}
    """.strip()
    template = dedent(template)

    processed_lm: list[str] = conversation['linear_messages']
    # processed_lm[::2] = [f'<pre>\n{m}\n</pre>' for m in processed_lm[::2]]
    processed_lm[::2] = [f'<pre class="user">\n{m}\n</pre>' for m in processed_lm[::2]]
    processed_lm[1::2] = [
        f'<pre class="assistant">\n{m}\n</pre>' for m in processed_lm[1::2]
    ]
    formatted_messages = '\n\n---\n\n'.join(processed_lm)
    return template.format(
        title=title,
        title_suffix=title_suffix,
        formatted_messages=formatted_messages,
    )


def get_args():
    parser = argparse.ArgumentParser(
        description='Generate preview files for Alfred list filter preview',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    return parser.parse_args()


def main():
    """Make a jazz noise here"""

    args = get_args()
    import json

    linear_conversations: list[dict] = json.loads(
        chatgpt_linear_conversations_json_path.read_text()
    )
    for conversation in tqdm(linear_conversations):
        output_path = generated_dir / f'{conversation["id"]}.md'
        output_path.write_text(generate_preview_markdown(conversation))


if __name__ == '__main__':
    main()

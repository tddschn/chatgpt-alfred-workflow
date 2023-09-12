#!/usr/bin/env python3
"""
Author : Xinyuan Chen <45612704+tddschn@users.noreply.github.com>
Date   : 2023-05-11
Purpose: Generate preview files for Alfred list filter preview
"""

from textwrap import dedent
from tqdm import tqdm
import argparse
from config import chatgpt_linear_conversations_json_path, generated_dir
from utils import (
    model_slug_to_model_name,
    chatgpt_conversation_id_to_url,
    get_model_short_subtitle_suffix_update_item3_kwargs,
)


def generate_preview_markdown(conversation: dict) -> str:
    title = conversation['title']
    # date_short = iso_to_month_day(conversation['update_time'])
    date_short = conversation['update_time']
    model = model_slug_to_model_name(conversation['model_slug'])
    # match model:
    #     case 'gpt-3.5-turbo':
    #         model_short = ''
    #     case 'gpt-4':
    #         model_short = 'GPT-4'
    #     case 'plugins':
    #         model_short = 'Plugins'
    #     case _:
    #         model_short = model
    model_short, _ = get_model_short_subtitle_suffix_update_item3_kwargs(
        model=model, date_short=date_short, item3_kwargs={}
    )
    title_suffix = f"""{date_short}{f' ({model_short})' if model_short else ''}"""

    template = """
    <link rel="stylesheet" href="../css/markdown_preview.css">

    # {title}

    [ChatGPT]({chatgpt_url})

    [TypingMind]({typingmind_url})

    {title_suffix}

    ---

    {formatted_messages}
    """
    template = dedent(template).strip()

    processed_lm: list[str] = conversation['linear_messages']
    # processed_lm[::2] = [f'<pre>\n{m}\n</pre>' for m in processed_lm[::2]]
    processed_lm[::2] = [f'<pre class="user">\n{m}\n</pre>' for m in processed_lm[::2]]
    processed_lm[1::2] = [
        f'<pre class="assistant">\n{m}\n</pre>\n' for m in processed_lm[1::2]
    ]
    formatted_messages = '\n\n---\n\n'.join(processed_lm)
    return template.format(
        title=title,
        title_suffix=title_suffix,
        formatted_messages=formatted_messages,
        chatgpt_url=chatgpt_conversation_id_to_url(conversation['id'], 'chatgpt'),
        typingmind_url=chatgpt_conversation_id_to_url(conversation['id'], 'typingmind'),
    )


def get_args():
    parser = argparse.ArgumentParser(
        description='Generate preview files for Alfred list filter preview',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    return parser.parse_args()


def main():
    """Make a jazz noise here"""

    get_args()
    import json

    linear_conversations: list[dict] = json.loads(
        chatgpt_linear_conversations_json_path.read_text()
    )
    for conversation in tqdm(linear_conversations):
        output_path = generated_dir / f'{conversation["id"]}.md'
        output_path.write_text(generate_preview_markdown(conversation))


if __name__ == '__main__':
    main()

#!/usr/bin/env python3

from pprint import pformat
import json
import sys
from workflow import Workflow3
from workflow.workflow3 import Item3
from config import (
    chatgpt_linear_conversations_json_path,
    message_preview_len,
    alfred_subtitle_max_length,
    alfred_title_max_length,
    generated_dir,
    assets_dir,
    gpt_4_icon_path,
)
from utils import (
    model_slug_to_model_name,
    search_and_extract_preview,
    chatgpt_conversation_id_to_url,
    iso_to_month_day,
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
        x for _, x in row.items() if x and not _.startswith('non_key_')
    ).lower()


def filter_query(rows: list[dict], query: str) -> list[dict]:
    new_rows = []
    for row in rows:
        long_str = search_key_for_rows(row)
        for subquery in query.lower().split('|'):
            if '=' in subquery:
                k, _, v = subquery.partition('=')
                if not k in row:
                    break
                if v.strip().lower() not in row[k].lower():
                    break
            else:
                if subquery not in long_str:
                    break
        else:
            new_rows.append(row)
    return new_rows


def main(wf: Workflow3):
    if len(wf.args):
        query = wf.args[0]
    else:
        query = None
    rows = wf.cached_data('rows', get_rows, max_age=3600)
    if not rows:
        wf.add_item('No results found')
        wf.send_feedback()
        return
    if query:
        rows = filter_query(rows, query)

    if not rows:
        wf.add_item('No matching results found')
        wf.send_feedback()
        return
    for row in rows:
        date_short = iso_to_month_day(row['update_time'])
        model = row['model']
        chatgpt_url = chatgpt_conversation_id_to_url(row['id'], 'chatgpt')
        typingmind_url = chatgpt_conversation_id_to_url(row['id'], 'typingmind')
        item3_kwargs = {}

        def get_message_preview(preview_len: int = message_preview_len) -> str:
            if query:
                message_preview = search_and_extract_preview(
                    query,
                    row['concatenated_messages'].strip(),
                    message_preview_len,
                    False,
                )
            else:
                message_preview = row['concatenated_messages'].strip()[
                    :message_preview_len
                ]
            return message_preview

        match model:
            case 'gpt-3.5-turbo':
                model_short = ''
                model_shorthand = '3.5'
                subtitle_prefix = date_short
            case 'gpt-4':
                model_shorthand = '4'
                model_short = 'GPT-4'
                subtitle_prefix = f"GPT-4 | {date_short}"
                item3_kwargs |= {'icon': str(gpt_4_icon_path)}
            case 'plugins':
                model_shorthand = 'Plugins'
                model_short = 'Plugins'
                subtitle_prefix = f"{model_shorthand} | {date_short}"
            case _:
                model_shorthand = model
                model_short = model
                subtitle_prefix = f"{model_shorthand} | {date_short}"
        title_suffix = f"""{date_short}{f' ({model_short})' if model_short else ''}"""
        row_title = row.get('title', '') or ''
        num_white_spaces = max(
            2, alfred_title_max_length - len(row_title) - len(title_suffix)
        )
        title = f"""{row_title}{' ' * num_white_spaces}{title_suffix}"""
        subtitle_remaining_length = (
            alfred_subtitle_max_length - len(subtitle_prefix) - 3
        )
        message_preview = get_message_preview(alfred_subtitle_max_length)
        item = Item3(
            title=title,
            # subtitle=f"{subtitle_prefix} | {message_preview}",
            subtitle=f"{message_preview}",
            # subtitle=' | '.join(
            #     (
            #         model_shorthand,
            #         date_short,
            #         message_preview.replace('\n', ' '),
            #     )
            # ),
            quicklookurl=str(generated_dir / f"{row['id']}.md"),
            arg=chatgpt_url,
            valid=True,
            **item3_kwargs,
        )
        item.add_modifier(
            'cmd',
            subtitle='Open on TypingMind',
            arg=typingmind_url,
            valid=True,
            **item3_kwargs,
        )
        # item.add_modifier(
        #     'alt',
        #     subtitle='Search Google',
        #     arg=row['non_key_google_search_url'],
        #     valid=True,
        # )
        # item.add_modifier(
        #     'shift', subtitle='Search 133', arg=row['non_key_133_url'], valid=True
        # )
        # item.add_modifier(
        #     'ctrl',
        #     subtitle='View row',
        #     arg=pformat(
        #         {
        #             k: v
        #             for k, v in row.items()
        #             if v
        #             and v not in ('USD', 'CAD')
        #             and not re.match(r'(/|http|0.00)', v)
        #         }
        #     ),
        #     valid=True,
        # )
        # from icecream import ic

        # ic(row)
        # wf.add_item(item)
        wf._items.append(item)

    # Send the results to Alfred as XML
    wf.send_feedback()


if __name__ == '__main__':
    wf = Workflow3()
    sys.exit(wf.run(main))

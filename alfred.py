#!/usr/bin/env python3

from pprint import pformat
import json
import re
import sys, csv
from workflow import Workflow3
from workflow.workflow3 import Item3
from config import chatgpt_linear_conversations_json_path, message_preview_len
from utils import model_slug_to_model_name, search_and_extract_preview, get_chatgpt_url
from pathlib import Path


# from tabulate import tabulate


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
        date_short = row['update_time'][2:11]
        model = row['model']
        chatgpt_url = get_chatgpt_url(row['id'])
        if query:
            message_preview = search_and_extract_preview(
                query, row['concatenated_messages'], message_preview_len, False
            )
        else:
            message_preview = row['concatenated_messages'][:message_preview_len]
        match model:
            case 'gpt-3.5-turbo':
                model_shorthand = '3.5'
            case 'gpt-4':
                model_shorthand = '4'
            case _:
                model_shorthand = model
        item = Item3(
            title=row['title'],
            subtitle=' | '.join(
                (
                    model_shorthand,
                    date_short,
                    message_preview,
                )
            ),
            # quicklookurl=row['non_key_markdown_source'],
            arg=chatgpt_url,
            valid=True,
        )
        # item.add_modifier(
        #     'cmd',
        #     subtitle='Search 1p3a',
        #     arg=row['non_key_1p3a_search_url'],
        #     valid=True,
        # )
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

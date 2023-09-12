#!/usr/bin/env python3

import sys
from workflow import Workflow3
from workflow.workflow3 import Item3
from config import (
    pre_computed_rows_json,
    pre_computed_rows_msgpack,
    message_preview_len,
    alfred_subtitle_max_length,
    alfred_workflow_cache_key,
)
from utils import (
    search_and_extract_preview,
)


def filter_query(rows: list[dict], query: str) -> list[dict]:
    new_rows = []
    for row in rows:
        long_str = row['_search_key']
        for subquery in query.lower().split('|'):
            if '=' in subquery:
                k, _, v = subquery.partition('=')
                if k not in row:
                    break
                if v.strip().lower() not in row[k].lower():
                    break
            else:
                if subquery not in long_str:
                    break
        else:
            new_rows.append(row)
    return new_rows


def get_rows() -> list[dict]:
    try:
        import msgpack

        return msgpack.unpackb(pre_computed_rows_msgpack.read_bytes())
    except ImportError:
        import json

        return json.loads(pre_computed_rows_json.read_text())


def main(wf: Workflow3):
    if len(wf.args):
        query = wf.args[0]
    else:
        query = None
    rows = wf.cached_data(alfred_workflow_cache_key, get_rows, max_age=3600)
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

        message_preview = get_message_preview(alfred_subtitle_max_length)
        item = Item3(
            title=row['_title'],
            # subtitle=f"{subtitle_prefix} | {message_preview}",
            subtitle=f"{message_preview}",
            # subtitle=' | '.join(
            #     (
            #         model_shorthand,
            #         date_short,
            #         message_preview.replace('\n', ' '),
            #     )
            # ),
            quicklookurl=row['_quicklookurl'],
            arg=row['_chatgpt_url'],
            valid=True,
            **row['_item3_kwargs'],
        )
        item.add_modifier(
            'cmd',
            subtitle='Open on TypingMind',
            arg=row['_typingmind_url'],
            valid=True,
            **row['_item3_kwargs'],
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

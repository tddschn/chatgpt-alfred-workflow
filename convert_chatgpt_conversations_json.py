#!/usr/bin/env python3
"""
Author : Xinyuan Chen <45612704+tddschn@users.noreply.github.com>
Date   : 2023-05-10
Purpose: Convert conversations.json to a linear conversation format
"""

import argparse
import json
from pathlib import Path
from typing import Any, Literal, Union
from utils import date_from_chatgpt_unix_timestamp
from config import (
    chatgpt_exported_conversations_json_path,
    chatgpt_linear_conversations_json_path,
    dalle_non_sense_messages,
)


class ChatGPTChatHistoryMessage:
    id: str
    parent_id: str | None = None
    children_ids: list[str] = []
    parent: Union['ChatGPTChatHistoryMessage', None] = None
    children: list['ChatGPTChatHistoryMessage'] = []
    role: Literal['system', 'assistant', 'user', 'tool'] | None = None
    content_type: Literal['text', 'multimodal_text'] | None = None
    content: str | None = None

    # None when role == user or system, not none when role == assistant
    # text-davinci-002-render: text-davinci-002-render-sha
    # gpt-4: gpt-4
    model_slug: str = 'text-davinci-002-render'

    plugin: bool = False
    # None, 'all', 'kayak.whatever' etc
    recipient: str | None = None

    # <|im_end|> if it's a message to a tool (always json)
    # tool response could be json or text
    # <|diff_marker|> if it's the final response to the user
    finish_details_marker: Literal['<|im_end|>', '<|diff_marker|>'] | None = None
    finish_details_type: Literal['stop', 'interrupted'] | None = None

    response_message_type: Literal['request', 'tool', 'finish'] | None = None
    message_type: Literal[
        'system', 'user', 'non_plugin_response', 'request', 'tool', 'finish'
    ] | None = None
    # like 'rentable_apartments.getApartments'
    # not none when role == tool
    tool_name: str | None = None

    def set_response_message_type(self):
        if not self.plugin:
            return
        match self.role:
            case 'tool':
                self.response_message_type = 'tool'
            case 'assistant':
                match self.finish_details_marker:
                    case '<|im_end|>':
                        self.response_message_type = 'request'
                    case '<|diff_marker|>':
                        self.response_message_type = 'finish'


def chatgpt_conversation_to_linear_chat_history(
    chatgpt_conversation: dict,
) -> dict[str, Any]:
    """Convert a single conversation in the exported json to linear chat messages"""
    conversation_id: str = chatgpt_conversation['id']
    title: str = chatgpt_conversation['title']
    messages = chatgpt_conversation['mapping']
    update_time_dt = date_from_chatgpt_unix_timestamp(
        chatgpt_conversation['update_time']
    )
    update_time_iso = update_time_dt.isoformat()
    create_time_iso = date_from_chatgpt_unix_timestamp(
        int(chatgpt_conversation['create_time'])  # type: ignore
    ).isoformat()

    model_slug = "text-davinci-002-render"
    plugin_enabled: bool = bool(chatgpt_conversation['plugin_ids'])

    id_to_m: dict[str, ChatGPTChatHistoryMessage] = {}
    for msg_id, message in messages.items():
        m = ChatGPTChatHistoryMessage()
        m.id = msg_id
        m.parent_id = message['parent']
        m.children_ids = message['children']
        id_to_m[msg_id] = m
        msg = message['message']

        if msg is not None:
            m.content_type = msg['content']['content_type']
            # if m.content_type == 'multimodal_text':
            #     # dalle output or image input
            #     # images on azure, sigs in url, generated upon requests
            #     if
            #     continue
            m.role = msg['author']['role']
            if m.role == 'tool':
                m.tool_name = msg['author']['name']
            if m_parts := msg['content'].get('parts'):
                m.content = m_parts[-1]
                if m.content_type == 'multimodal_text':
                    if isinstance(m.content, str):
                        # image input prompt
                        pass
                    else:
                        # dalle image output
                        m.content = None
            elif m_content := msg['content'].get('text'):
                m.content = m_content
            m.recipient = msg['recipient']
            if metadata := msg.get('metadata'):
                m.model_slug = metadata.get('model_slug')
                if m.model_slug is not None:
                    model_slug = m.model_slug
                    if model_slug == 'gpt-4-dalle':
                        # the image prompts, or 'DALL·E returned some images. They are already displayed to the user. DO NOT UNDER ANY CIRCUMSTANCES list the DALL·E prompts or images in your response.'
                        # assert m.content
                        # if m.content.startswith('{'):
                        #     # m.content = json.loads(m.content)
                        #     m.content = '\n'.join(
                        #         [
                        #             '```json',
                        #             m.content,
                        #             '```',
                        #         ]
                        #     )
                        if m.content and m.content in dalle_non_sense_messages:
                            m.content = None
                            continue
                if finish_details := metadata.get('finish_details'):
                    m.finish_details_marker = finish_details.get('stop', None)
                    m.finish_details_type = finish_details.get('type', None)
                m.set_response_message_type
        else:
            m.role = None
            m.content = None

    for msg_id, message in id_to_m.items():
        if message.parent_id:
            message.parent = id_to_m[message.parent_id]
        message.children = [id_to_m[child_id] for child_id in message.children_ids]

    # in id_to_m, find the root message, that has role None and content None
    root_message = [
        x for x in id_to_m.values() if x.role is None and x.content is None
    ][0]

    # starting from the root message, go down the tree; if a message has more than 1 children, only go for the last one.
    # if a message has no children, stop.
    linear_messages: list[ChatGPTChatHistoryMessage] = []
    while True:
        if len(root_message.children) == 0:
            break
        elif len(root_message.children) == 1:
            root_message = root_message.children[0]
        else:
            root_message = root_message.children[-1]
        linear_messages.append(root_message)

    return {
        'id': conversation_id,
        'title': title,
        'update_time': update_time_iso,
        'create_time': create_time_iso,
        'model_slug': model_slug,
        'plugin_enabled': plugin_enabled,
        'linear_messages': [m.content for m in linear_messages if m.content],
    }


def get_args():
    """Get command-line arguments"""

    parser = argparse.ArgumentParser(
        description='Convert conversations.json to a linear conversation format',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        '-i',
        '--input',
        help='Input conversations.json file',
        metavar='PATH',
        type=Path,
        default=chatgpt_exported_conversations_json_path,
    )

    parser.add_argument(
        '-o',
        '--output',
        help='Output linear chat history json file',
        metavar='PATH',
        type=Path,
        default=chatgpt_linear_conversations_json_path,
    )

    return parser.parse_args()


def main():
    """Make a jazz noise here"""

    args = get_args()
    conversations = json.loads(args.input.read_text())
    linear_conversations = [
        chatgpt_conversation_to_linear_chat_history(c) for c in conversations
    ]
    args.output.write_text(
        json.dumps(
            linear_conversations,
            indent=2,
            ensure_ascii=False,
        )
    )
    print(f'Done! {len(linear_conversations)} conversations written to {args.output} .')


if __name__ == '__main__':
    main()

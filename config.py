#!/usr/bin/env python3


from pathlib import Path

from utils import model_slug_to_model_name

parent_dir = Path(__file__).parent
chatgpt_exported_conversations_json_path = parent_dir / 'conversations.json'
chatgpt_linear_conversations_json_path = parent_dir / 'linear_conversations.json'

message_preview_len = 100

model_slug_to_model_name_map = {
    # gpt-3.5-turbo: text-davinci-002-render-sha
    # gpt-4: gpt-4
    'text-davinci-002-render-sha': 'gpt-3.5-turbo',
    'gpt-4': 'gpt-4',
}

#!/usr/bin/env python3


from pathlib import Path

from utils import model_slug_to_model_name

parent_dir = Path(__file__).parent
chatgpt_exported_conversations_json_path = parent_dir / 'conversations.json'
chatgpt_linear_conversations_json_path = parent_dir / 'linear_conversations.json'

message_preview_len = 100

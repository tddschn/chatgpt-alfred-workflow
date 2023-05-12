#!/usr/bin/env python3


from pathlib import Path

from utils import model_slug_to_model_name

downloads_dir = Path.home() / 'Downloads'

parent_dir = Path(__file__).parent
chatgpt_exported_conversations_json_path = parent_dir / 'conversations.json'
chatgpt_linear_conversations_json_path = parent_dir / 'linear_conversations.json'

alfred_title_max_length = 74
alfred_subtitle_max_length = 108
message_preview_len = 100

chatgpt_data_export_zip_glob_pattern = r'*[0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f]-????-??-??-??-??-??.zip'
chatgpt_data_export_zip_regex_pattern = (
    r'[0-9a-f]{64}-\d{4}-\d{2}-\d{2}-\d{2}-\d{2}-\d{2}.zip'
)

generated_dir = parent_dir / 'generated'
assets_dir = parent_dir / 'assets'
gpt_4_icon_path = assets_dir / 'GPT-4.png'

alfred_workflow_cache_key = 'chatgpt-alfred-workflow'

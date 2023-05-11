#!/usr/bin/env bash

./update_conversations_json.py &&
    ./convert_chatgpt_conversations_json.py

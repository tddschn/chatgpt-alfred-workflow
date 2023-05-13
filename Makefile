update-workflow:
	rsync -au --progress -h ./ ~/gui/Alfred.alfredpreferences/workflows/user.workflow.chatgpt-alfred-workflow --exclude .git

update-repo-from-workflow:
	rsync -au --progress -h ~/gui/Alfred.alfredpreferences/workflows/user.workflow.chatgpt-alfred-workflow/ ./ --exclude __pycache__ --exclude .git

update-conversations-json:
	./update_conversations_json.sh
	./generate_preview_files.py

workflow-delcache:
	./alfred.py 'workflow:delcache'

update-conversations-json-and-workflow: update-conversations-json update-workflow workflow-delcache

cspell:
	cspell --words-only --unique '{*.py,{**/*.{html,py,js,ts,css,md,yaml,yml,txt,code-snippets,ipynb},.github/**/*.{md,yaml,yml}}}' | LC_ALL='C' sort --ignore-case > project-words.txt

get-5:
	jq '.[0:5]' conversations.json > input.json
	./convert_chatgpt_conversations_json.py -i input.json -o converted.json

.PHONY: *
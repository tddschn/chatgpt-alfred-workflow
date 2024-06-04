VERCEL_PROJECT_NAME := chatgpt-datasette-vercel
THIRD_LEVEL_DOMAIN := pdata-chatgpt
VERCEL_PROJECT_DOMAIN_SETTINGS_URL := https://vercel.com/tddschn/$(VERCEL_PROJECT_NAME)/settings/domains
DB_FILENAME := chatgpt.db
DATASETTE_METADATA_FILE := metadata.yml

ingest: ## ingest linear_conversations.json into chatgpt.db
	[[ -f $(DB_FILENAME) ]] && rm -v $(DB_FILENAME) || true
	# add link field
	<linear_conversations.json jq 'map(. + {"link": ("https://chatgpt.com/c/" + .id)})' > chatgpt-db.json
	# sqlite-utils insert $(DB_FILENAME) linear_conversations chatgpt-db.json --pk id
	# don't wanna sort by id by default
	sqlite-utils insert $(DB_FILENAME) linear_conversations chatgpt-db.json
	sqlite-utils transform $(DB_FILENAME) linear_conversations -o 'id' -o 'title' -o 'link' -o 'linear_messages' -o 'model_slug'
	~/.local/pipx/venvs/sqlite-utils/bin/python ~/config/scripts/sqlite_utils_enable_fts_all.py $(DB_FILENAME)

publish-db: ## publish chatgpt.db to Vercel
	datasette publish vercel --metadata $(DATASETTE_METADATA_FILE) --project $(VERCEL_PROJECT_NAME) $(DB_FILENAME) --install datasette-search-all --install datasette-render-timestamps --install datasette-render-images --install datasette-uptime --install datasette-render-html \
	--install datasette-pretty-json

db-all: ingest publish-db ## ingest and publish chatgpt.db to Vercel
	@echo 'Domain settings: $(VERCEL_PROJECT_DOMAIN_SETTINGS_URL)'

open-vercel-project-domain-settings: ## open the Vercel project domain settings
	open $(VERCEL_PROJECT_DOMAIN_SETTINGS_URL)

add-dns-record: ## add a DNS record for pdata-chatgpt.teddysc.me
	# https://developers.cloudflare.com/api/operations/dns-records-for-a-zone-create-dns-record
	cli4 --post 'content=cname.vercel-dns.com.' 'name=$(THIRD_LEVEL_DOMAIN)' 'proxied=true' 'type=CNAME' 'comment=$(VERCEL_PROJECT_DOMAIN_SETTINGS_URL)' /zones/:teddysc.me/dns_records

CHATGPT_EXPORT_CONVERSATIONS_FILE = conversations.json
LINEAR_CONVERSATIONS_FILE = linear_conversations.json
PRE_COMPUTED_ROWS_FILES = $(wildcard generated/pre_computed_rows.{json,msgpack})
PRE_COMPUTED_ALFRED_JSON_FILE = generated/pre_computed_alfred.json

update-workflow: ## syncs the workflow files from the repo to the Alfred prefs, this installs / updates the workflow in Alfred.
	# NOTE: my Alfred prefs are saved at ` ~/gui/Alfred.alfredpreferences`, you may need to change this path to match your own
	rsync -au --progress -h ./ ~/gui/Alfred.alfredpreferences/workflows/user.workflow.chatgpt-alfred-workflow --exclude .git

update-repo-from-workflow: ## syncs the workflow files from the Alfred prefs to the repo, this is useful if you've made changes to the workflow in Alfred and want to save them to the repo.
	rsync -au --progress -h ~/gui/Alfred.alfredpreferences/workflows/user.workflow.chatgpt-alfred-workflow/ ./ --exclude __pycache__ --exclude .git

update-conversations-json: ## get the latest conversations.json from ~/Downloads, generate linear convos and markdown previews
	./update_conversations_json.sh
	./convert_chatgpt_conversations_json.py
	./generate_preview_files.py

convert-conversations-json: $(CHATGPT_EXPORT_CONVERSATIONS_FILE) ## convert conversations.json to linear conversations and save to linear_conversations.json
	./convert_chatgpt_conversations_json.py

workflow-delcache: $(LINEAR_CONVERSATIONS_FILE) ## clear the Alfred cache for this workflow
	./alfred.py 'workflow:delcache'

regen-and-update-all: convert-conversations-json pre-process update-workflow workflow-delcache ## use this if you want to import and process a new conversations.json file automatically

update-conversations-json-and-workflow: update-conversations-json pre-process update-workflow ## same as regen-and-update-all, but doesn't clear cache

cspell:
	cspell --words-only --unique '{*.py,{**/*.{html,py,js,ts,css,md,yaml,yml,txt,code-snippets,ipynb},.github/**/*.{md,yaml,yml}}}' | LC_ALL='C' sort --ignore-case > project-words.txt

get-5:
	@# just for testing purposes
	jq '.[0:5]' conversations.json > input.json
	./convert_chatgpt_conversations_json.py -i input.json -o converted.json
	
get-20-raw:
	@# just for testing purposes
	jq '.[0:20]' conversations.json > raw20.json
	# ./convert_chatgpt_conversations_json.py -i input.json -o converted.json

get-length:
	<conversations.json jq 'keys | length'

get-linear-conversations-without-linear-messages:
	jq 'map(del(.linear_messages))' linear_conversations.json > linear_conversations_without_linear_messages.json

.DEFAULT_GOAL := help

lint:
	ruff check . --fix

# $(PRE_COMPUTED_ROWS_FILES): $(LINEAR_CONVERSATIONS_FILE)
# 	./preprocess_conversations.py


# $(PRE_COMPUTED_ALFRED_JSON_FILE): $(PRE_COMPUTED_ROWS_FILES)
# 	./alfred.py -g

# pre-process: $(PRE_COMPUTED_ROWS_FILES) $(PRE_COMPUTED_ALFRED_JSON_FILE) ## pre-process linear-conversations.json for Alfred to speed things up
pre-process: ## pre-process linear-conversations.json for Alfred to speed things up
	./preprocess_conversations.py
	./alfred.py -g
	
cgupdate: ## same as the cgupdate command in the Alfred workflow
	# cd ~/testdir/chatgpt-alfred-workflow && /usr/bin/make update-conversations-json-and-workflow && /usr/bin/make workflow-delcache
	/usr/bin/make update-conversations-json-and-workflow && /usr/bin/make workflow-delcache

help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

# all target except the $() ones
# hardcode this
.PHONY: *


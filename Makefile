update-workflow:
	rsync -au --progress -h ./ ~/gui/Alfred.alfredpreferences/workflows/user.workflow.chatgpt-alfred-workflow --exclude .git

update-repo-from-workflow:
	rsync -au --progress -h ~/gui/Alfred.alfredpreferences/workflows/user.workflow.chatgpt-alfred-workflow/ ./ --exclude __pycache__ --exclude .git

cspell:
	cspell --words-only --unique '{*.py,{**/*.{html,py,js,ts,css,md,yaml,yml,txt,code-snippets,ipynb},.github/**/*.{md,yaml,yml}}}' | LC_ALL='C' sort --ignore-case > project-words.txt
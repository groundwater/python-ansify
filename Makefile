VENV=venv/bin/activate

${VENV}:
	@echo "Creating virtual environment..."
	@python3 -m venv venv
	@echo "Installing dependencies..."
	@source venv/bin/activate && pip install .
	@echo "Virtual environment created. To activate it, run 'source venv/bin/activate'."

google:
	@bash -c 'ansify comp \
		<(ansify img src/img/google.png) \
		<(ansify text o --background=255,255,255 --color=255,0,0 --font-size=28) \
		<(ansify text o --background=255,255,255 --color=255,255,0 --font-size=28) \
		<(ansify text g --background=255,255,255 --color=0,0,255 --font-size=28) \
		<(ansify text l --background=255,255,255 --color=0,255,0 --font-size=28) \
		<(ansify text e --background=255,255,255 --color=255,0,0 --font-size=28)'


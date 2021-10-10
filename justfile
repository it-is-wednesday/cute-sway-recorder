# Run the script without installing
run:
	poetry run python cute_sway_recorder/main.py

# Build wheel and tar artifacts
build:
	poetry build

# Delete files created during build
clean:
	rm -rf *.egg-info dist

# Install to system outside the venv, adding a menu entry as well
system-install: clean build
	@echo "please make sure you are not inside a virtual env :)"
	if ! command -v pipx; then pip install pipx; fi
	pipx install --force dist/*.whl
	@# using : instead of / because $HOME will contain slashes. turns out you can use any delimiter
	@# for the `s` command is sed! whatever comes after the `s` character will be used as the
	@# delimiter.
	sed "s:HOME:$HOME:" cute-sway-recorder.desktop > ~/.local/share/applications/cute-sway-recorder.desktop

# Local Variables:
# mode: makefile
# End:
# vim: set ft=make :

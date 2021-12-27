# Run the program without installing it system-wide
run:
	poetry run python cute_sway_recorder/main.py

# Run the program, restart when any .py file changes
watch:
	watchexec --restart --exts py just run

# Build wheel and tar artifacts
build:
	poetry build

# Delete files created during build
clean:
	rm -rf *.egg-info dist

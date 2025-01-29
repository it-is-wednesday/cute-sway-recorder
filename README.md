# Cute Sway Recorder

Screen recorder for [`wlroots`](https://gitlab.freedesktop.org/wlroots/wlroots/)-based compositors like `Sway` and `Hyperland`. For other compositors, it falls back to using [wlr-randr](https://sr.ht/~emersion/wlr-randr/) to get outputs.

More specifically, this project is merely a graphical [Qt](https://www.qt.io/) wrapper for [`wf-recorder`](https://github.com/ammen99/wf-recorder), leveraging [`slurp`](https://github.com/emersion/slurp) for selecting screen regions.

![](assets/screenshots/recording.png)
![](assets/screenshots/done.png)

## Installation

Do note that you will need to have [`wf-recorder`](https://github.com/ammen99/wf-recorder) and [`slurp`](https://github.com/emersion/slurp) accessible via `$PATH` =)

### Using pip

```shell
pip install cute-sway-recorder
```

You might prefer using [pipx](https://pypa.github.io/pipx/):

```shell
pipx install cute-sway-recorder
```

### Arch Linux

For Arch Linux users, you can install the `cute-sway-recorder-git` package from the [AUR](https://aur.archlinux.org/packages/cute-sway-recorder-git) using an AUR helper like `paru`:

```shell
paru -S cute-sway-recorder-git
```

## Configuration

Default configuration is stored in the file `$HOME/.config/cute-sway-recorder/config.ini`
in [ini](https://docs.python.org/3/library/configparser.html#supported-ini-file-structure) format.

Here is an example configuration which saves recordings as gifs:

```ini
[wf-recorder-defaults]
# Default file save location (location must exist)
# Type: string, default: "~/Videos/cute-{id}.mp4"
file_dest = ~/Gifs/gif.gif

# Whether to include audio in recording
# Type: bool, default: off
include_audio = off

# Delay before recording starts 
# Type: integer, default: 0
delay = 0

# Additional flags to pass to wf-recorder
# Type: string, default: ""
flags = -c gif -r 10
```

## Contributing

PRs are welcome!

1. After forking this repository, make sure to install the project dependencies locally:

```bash
poetry install
```

This will create a virtual environment and install all the required dependencies.

2. Make sure `cute-sway-recorder` runs locally:

```bash
poetry run python -m cute_sway_recorder.main
```

## Alternatives

- [green-recorder](https://github.com/dvershinin/green-recorder) is a recent fork of the [project abandoned in 2019](https://github.com/mhsabbagh/green-recorder). It doesn't use `wf-recorder` under
    the hood. It currently has more features than this project; you might want to try it first, and come back here if it gives you a hard time.


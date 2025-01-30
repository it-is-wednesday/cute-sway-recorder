from typing import List, Optional
import json
import re
import os
import subprocess
import random
import string


PATTERN_SELECTED_AREA = re.compile(r"\d+,\d+ \d+x\d+")
CONFIG_BUTTON_WIDTH = 130


def detect_compositor() -> Optional[str]:
    """
    Detects the running Wayland compositor.
    """
    if "SWAYSOCK" in os.environ:
        return "sway"
    elif "HYPRLAND_INSTANCE_SIGNATURE" in os.environ:
        return "hyprland"
    else:
        try:
            subprocess.run(
                "wlr-randr",
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return "wlr-randr"
        except FileNotFoundError:
            raise ValueError(
                "Unsupported Wayland compositor. Please install wlr-randr for additional support."
            )


def apply_compositor_rules(compositor: str):
    """
    Applies compositor-specific window rules.
    """
    if compositor == "sway":
        subprocess.run(
            ["swaymsg", 'for_window [app_id="cute-sway-recorder"] floating enable']
        )
    elif compositor == "hyprland":
        subprocess.run(
            ["hyprctl", "keyword", "windowrulev2", "float,class:^(cute-sway-recorder)$"]
        )
    elif compositor == "wlr-randr":
        # No specific window rules for wlr-randr
        return
    else:
        raise ValueError(f"Unsupported Wayland compositor: {compositor}")


def get_available_screens(compositor: str) -> List[str]:
    """
    Returns a list of available outputs based on the compositor,
    e.g., ['eDP-1', 'HDMI-A-1']
    """
    if compositor == "sway":
        command = ["swaymsg", "-t", "get_outputs"]
    elif compositor == "hyprland":
        command = ["hyprctl", "-j", "monitors"]
    elif compositor == "wlr-randr":
        command = ["wlr-randr", "--json"]
    else:
        raise ValueError(f"Unsupported Wayland compositor: {compositor}")

    try:
        output = subprocess.check_output(command, text=True)
        screens = json.loads(output)
        return [screen["name"] for screen in screens]
    except (subprocess.CalledProcessError, json.JSONDecodeError) as e:
        raise RuntimeError(f"Failed to retrieve available screens: {str(e)}") from e


class SelectedScreen(str):
    """
    Textual representation of one of your monitors. Raises ValueError if instantiated with a string
    which isn't one of the monitors. List of monitors is decided by `get_available_screens()`.
    """

    def __init__(self, s):
        try:
            compositor = detect_compositor()
            apply_compositor_rules(compositor)
            screens = get_available_screens(compositor)
            if s not in screens:
                raise ValueError(
                    f"Screen '{s}' isn't one of the available screens: {screens}"
                )
        except Exception as e:
            raise RuntimeError(f"An unexpected error occurred: {str(e)}") from e


class SelectedArea(str):
    """
    Textual description of a rectangular area on the screen, of the
    following format: <x>,<y> <width>x<height>
    Same output as the `slurp` command (https://github.com/emersion/slurp).

    Raises ValueError if instantiated with a string not of the specified format

    >>> SelectedArea("10,10 40x40")
    '10,10 40x40'
    >>> SelectedArea("hey")
    Traceback (most recent call last):
    ...
    ValueError: Area 'hey' isn't of format: 'x,y width,height'
    """

    def __init__(self, s):
        if not PATTERN_SELECTED_AREA.match(s):
            raise ValueError(f"Area '{s}' isn't of format: 'x,y width,height'")


def make_random_file_stem() -> str:
    """
    Create a default basename (no extension, no path) for default videos to be used by
    make_default_file_dest and "Random Name"
    Example result: cute-sbh42
    """
    identifier = "".join(random.choices(string.ascii_letters, k=5))
    return f"cute-{identifier}"

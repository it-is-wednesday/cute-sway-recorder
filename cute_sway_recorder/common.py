import json
import re
import subprocess
from typing import List

from PySide6.QtCore import QSize

PATTERN_SELECTED_AREA = re.compile(r"\d+,\d+ \d+x\d+")
CONFIG_BUTTON_WIDTH = 130


def available_screens() -> List[str]:
    """
    Returns a list of all available outputs via `swaymsg -t get_outputs`, e.g.:
    ['eDP-1', 'HDMI-A-1']
    """
    out = subprocess.check_output(["swaymsg", "-t", "get_outputs"], text=True)
    return [o["name"] for o in json.loads(out)]


class SelectedScreen(str):
    """
    Textual representation of one of your monitors. Raises ValueError if instantiated with a string
    which isn't one of the monitors. List of monitors is decided by `available_screens()`.
    """

    def __init__(self, s):
        screens = available_screens()
        if s not in screens:
            raise ValueError(f"Screen {s} isn't one of available screens: {screens}")


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

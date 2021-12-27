import json
import re
import subprocess
from typing import List

PATTERN_SELECTED_AREA = re.compile(r"\d+,\d+ \d+x\d+")


def available_screens() -> List[str]:
    """
    Returns a list of all available outputs via `swaymsg -t get_outputs`, e.g.:
    ['eDP-1', 'HDMI-A-1']
    """
    out = subprocess.check_output(["swaymsg", "-t", "get_outputs"], text=True)
    return [o["name"] for o in json.loads(out)]


class SelectedScreen(str):
    def __init__(self, s):
        screens = available_screens()
        if s not in screens:
            raise ValueError(f"Screen {s} isn't one of available screens: {screens}")


class SelectedArea(str):
    def __init__(self, s):
        if not PATTERN_SELECTED_AREA.match(s):
            raise ValueError(f"Area {s} isn't of format: 'x,y width,height'")


def set_buttons_state(*btns, enabled: bool):
    for b in btns:
        b.setEnabled(enabled)

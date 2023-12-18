import io
import re
import sys
from typing import Any


def no_ansi_string(ansi_string: str) -> str:
    """Remove ANSI escape sequences from a string.

    Args:
        ansi_string (str): String with ANSI escape sequences.

    Returns:
        str: String without ANSI escape sequences.
    """
    ansi_escape = re.compile(r"\x1b[^m]*m")
    return ansi_escape.sub("", ansi_string)


class CaptureStdout:
    def __init__(self) -> None:
        self.new_stdout = io.StringIO()
        self.old_stdout = sys.stdout

    def __enter__(self) -> "CaptureStdout":
        sys.stdout = self.new_stdout
        return self

    def __exit__(self, *args: Any) -> None:
        self.value = self.new_stdout.getvalue()
        self.new_stdout.close()
        sys.stdout = self.old_stdout

    def getvalue(self) -> str:
        return self.value.strip()

import platform
import sys
from pathlib import Path


def system_status() -> str:
    return (
        f"OS: {platform.system()} {platform.release()}\n"
        f"Python: {sys.version.split()[0]}\n"
        f"Project: {Path.cwd()}\n"
        "Access level: READ_ONLY"
    )

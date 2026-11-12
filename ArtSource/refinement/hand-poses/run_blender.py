"""Serialize this combat-source lane's Blender jobs on the shared host."""

import fcntl
import os
import sys
import tempfile
from pathlib import Path

BLENDER = Path('/Users/yupeng/Applications/Blender-4.5.15-LTS.app/Contents/MacOS/Blender')
REPO = Path(__file__).resolve().parents[3]
LOCK = Path(tempfile.gettempdir()) / 'pico-wuxia-arena-combat01-blender.lock'

def main():
    arguments = sys.argv[1:]
    if '-b' not in arguments and '--background' not in arguments:
        raise SystemExit('Combat asset jobs require Blender background mode')
    if not BLENDER.is_file():
        raise SystemExit('The reviewed Blender 4.5.15 binary is unavailable')
    os.chdir(REPO)
    with LOCK.open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        os.set_inheritable(lock.fileno(), True)
        os.execv(str(BLENDER), [str(BLENDER), *arguments])


if __name__ == '__main__':
    main()

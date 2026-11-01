"""Build public/vela-linux.zip from linux/. Same files in, same bytes out.

    python3 linux/make_zip.py
"""

from __future__ import annotations

import sys
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
TARGET = HERE.parent / "public" / "vela-linux.zip"
EPOCH = (1980, 1, 1, 0, 0, 0)


def members():
    files = [HERE / "README.md", HERE / "install.sh"]
    files += sorted((HERE / "share").rglob("*"))
    files += sorted((HERE / "vela").glob("*.py"))
    return [path for path in files if path.is_file()]


def build(target=TARGET):
    target.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_STORED) as archive:
        for path in members():
            info = zipfile.ZipInfo(path.relative_to(HERE).as_posix(), date_time=EPOCH)
            info.create_system = 3  # unix, so the mode below is honoured
            mode = 0o755 if path.stat().st_mode & 0o111 else 0o644
            info.external_attr = mode << 16
            archive.writestr(info, path.read_bytes())
    return target


if __name__ == "__main__":
    print(build(Path(sys.argv[1]) if len(sys.argv) > 1 else TARGET))

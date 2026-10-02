#!/usr/bin/env python3
"""Install a self-contained user launcher; --prefix permits staging validation."""

import argparse
import os
from pathlib import Path
import shutil
import subprocess


def desktop_quote(path):
    # Exec quoting and Desktop Entry string escaping are separate layers.
    value = str(path).replace("%", "%%")
    for character in ('\\', '"', '`', '$'):
        value = value.replace(character, '\\' + character)
    return '"' + value.replace('\\', '\\\\') + '"'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--prefix", type=Path, help="검증용 설치 경로 (바탕화면 복사 생략)")
    args = parser.parse_args()
    source = Path(__file__).resolve().parent
    data = args.prefix or Path(os.environ.get("XDG_DATA_HOME", str(Path.home() / ".local/share")))
    data = data.expanduser().resolve()
    app = data / "youtube-downloader"
    applications = data / "applications"
    app.mkdir(parents=True, exist_ok=True)
    applications.mkdir(parents=True, exist_ok=True)
    for filename in ("yt-dlp.sh", "downloader.py", "gui.py"):
        shutil.copy2(source / filename, app / filename)
    (app / "yt-dlp.sh").chmod(0o755)
    template = (source / "youtube-downloader.desktop").read_text(encoding="utf-8")
    content = "\n".join(
        "Exec=" + desktop_quote(app / "yt-dlp.sh") + " --gui" if line.startswith("Exec=") else line
        for line in template.splitlines()
    ) + "\n"
    launcher = applications / "youtube-downloader.desktop"
    launcher.write_text(content, encoding="utf-8")
    launcher.chmod(0o755)
    print(f"앱 메뉴: {launcher}")
    if not args.prefix:
        (Path.home() / "youtube").mkdir(exist_ok=True)
        if shutil.which("xdg-user-dir"):
            result = subprocess.run(["xdg-user-dir", "DESKTOP"], capture_output=True, text=True)
            desktop = Path(result.stdout.strip())
            if result.returncode == 0 and desktop.is_absolute() and desktop != Path.home():
                desktop.mkdir(parents=True, exist_ok=True)
                shutil.copy2(launcher, desktop / launcher.name)
                print(f"바탕화면: {desktop / launcher.name}")
        if shutil.which("update-desktop-database"):
            subprocess.run(["update-desktop-database", str(applications)], check=False)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Desktop URL prompt and collection-aware yt-dlp output layout."""

import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from urllib.parse import urlsplit


def prompt_url():
    if os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"):
        if shutil.which("kdialog"):
            command = ["kdialog", "--title", "YouTube 다운로드", "--inputbox",
                       "영상 · 재생목록 · 채널 URL을 입력하세요"]
        elif shutil.which("zenity"):
            command = ["zenity", "--entry", "--title=YouTube 다운로드",
                       "--text=영상 · 재생목록 · 채널 URL을 입력하세요", "--width=520"]
        else:
            command = None
        if command:
            result = subprocess.run(command, capture_output=True, text=True)
            if result.returncode == 0:
                return result.stdout.strip()
            if result.returncode == 1:
                return ""  # Cancel must never start a download.
            print("입력창을 열 수 없어 터미널 입력으로 전환합니다.")
    return input("다운로드할 주소: ").strip()


def safe_name(value):
    # Preserve Korean, replace path separators/control characters, limit bytes.
    name = re.sub(r'[\x00-\x1f\x7f/\\:*?"<>|]', "_", str(value))
    name = name.encode("utf-8")[:150].decode("utf-8", errors="ignore").strip(" .")
    return name or "제목 없음"


def is_collection(info):
    return info.get("_type") in ("playlist", "multi_video")


def settings_file():
    config = os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config"
    return Path(config) / "youtube-downloader" / "download_dir"


def download_base():
    # YTD_DOWNLOAD_DIR wins over the folder saved from the GUI.
    configured = os.environ.get("YTD_DOWNLOAD_DIR", "").strip()
    if not configured:
        try:
            configured = settings_file().read_text(encoding="utf-8").strip()
        except FileNotFoundError:
            pass
    return Path(configured).expanduser() if configured else Path.home() / "youtube"


def save_download_base(folder):
    settings_file().parent.mkdir(parents=True, exist_ok=True)
    settings_file().write_text(f"{folder}\n", encoding="utf-8")


def destination(base, info):
    title = info.get("title") or info.get("channel") or "제목 없음"
    # IDs prevent unrelated channels/playlists with the same title from mixing.
    return base / f"{safe_name(title)} [{safe_name(info.get('id') or 'unknown')}]"


def common_options():
    options = ["--ignore-config", "--yes-playlist", "--remote-components", "ejs:github"]
    if shutil.which("deno"):
        options += ["--js-runtimes", "deno"]
    elif shutil.which("node"):
        options += ["--js-runtimes", "node"]
    else:
        raise RuntimeError("YouTube 다운로드에 필요한 Deno 또는 Node.js를 설치해 주세요.")
    return options


def download_options(root, collection):
    stem = "%(title).150B [%(id)s]"
    video = f"{stem}/{stem}.%(ext)s"
    if collection:
        video = "videos/" + video
    else:
        video = f"{stem}.%(ext)s"
    metadata = "metadata/%(title).150B [%(id)s].%(ext)s"
    return [
        "--write-thumbnail", "--embed-thumbnail", "--write-description",
        "--newline", "--progress", "--no-colors",
        "--write-info-json", "--write-playlist-metafiles", "--write-comments",
        "--sub-langs", "all", "--write-subs", "--embed-subs", "--embed-metadata",
        "--embed-chapters", "--embed-info-json", "--audio-multistreams",
        "-f", "bv+(251/mergeall[format_id~=251])/bv+ba/b",
        "--merge-output-format", "mkv", "--remux-video", "mkv",
        "--no-abort-on-error", "-P", str(root), "-o", video,
        "-o", f"pl_infojson:{metadata}",
        "-o", f"pl_description:{metadata}",
        "-o", f"pl_thumbnail:{metadata}",
    ]


def main():
    if len(sys.argv) > 2:
        raise RuntimeError("사용법: yt-dlp.sh [URL]")
    url = sys.argv[1].strip() if len(sys.argv) == 2 else prompt_url()
    if not url:
        print("취소했습니다.")
        return 0
    parsed = urlsplit(url)
    if parsed.scheme not in ("https", "http") or not parsed.hostname:
        raise RuntimeError("http:// 또는 https://로 시작하는 URL을 입력해 주세요.")

    command = [sys.executable, "-m", "yt_dlp", *common_options()]
    print("영상 / 채널 / 재생목록 정보를 확인합니다…", flush=True)
    # Fetch only the collection header here, not every video's formats/comments.
    result = subprocess.run(
        [*command, "--flat-playlist", "--playlist-items", "0", "--dump-single-json", "--", url],
        stdout=subprocess.PIPE, text=True,
    )
    if result.returncode:
        raise RuntimeError("주소 정보를 가져오지 못했습니다. 위의 yt-dlp 오류를 확인해 주세요.")
    info = json.loads(result.stdout)
    root = destination(download_base(), info)
    root.mkdir(parents=True, exist_ok=True)
    collection = is_collection(info)
    if collection:
        metadata_dir = root / "metadata"
        metadata_dir.mkdir(exist_ok=True)
        (root / "videos").mkdir(exist_ok=True)
        # This header records the originally entered channel, even when yt-dlp
        # processes its Videos, Shorts and Streams tabs as nested playlists.
        header = {key: value for key, value in info.items() if key != "entries"}
        header["requested_url"] = url
        header["metadata_scope"] = "collection header only; entries excluded"
        (metadata_dir / "source.info.json").write_text(
            json.dumps(header, ensure_ascii=False, indent=2) + "\n", encoding="utf-8",
        )
    print(f"저장 위치: {root}", flush=True)
    status = subprocess.run([*command, *download_options(root, collection), "--", url]).returncode
    if status:
        print("일부 또는 전체 다운로드가 실패했습니다. 위 오류를 확인해 주세요.", file=sys.stderr)
    else:
        print(f"다운로드가 완료되었습니다.\n{root}")
    return status


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n다운로드를 중단했습니다.", file=sys.stderr)
        sys.exit(130)
    except (RuntimeError, OSError, ValueError, EOFError) as error:
        print(f"오류: {error}", file=sys.stderr)
        sys.exit(1)

#!/usr/bin/env bash
set -uo pipefail

# Desktop sessions do not always inherit the interactive shell's PATH.
export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$HOME/.deno/bin:/home/linuxbrew/.linuxbrew/bin:$PATH"
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

if [[ "${1:-}" == "--gui" ]]; then
    # Homebrew's Python may shadow the system Python that provides Qt.
    for interpreter in python3 /usr/bin/python3; do
        if "$interpreter" -c 'from PySide6.QtCore import QProcess; QProcess.UnixProcessFlag.CreateNewSession' 2>/dev/null; then
            exec "$interpreter" "$SCRIPT_DIR/gui.py"
        fi
    done
    message='다운로드 창을 열려면 Python용 PySide6 6.7 이상이 필요합니다.'
    if command -v kdialog >/dev/null 2>&1; then
        kdialog --error "$message"
    elif command -v zenity >/dev/null 2>&1; then
        zenity --error --text="$message"
    else
        printf '%s\n' "$message" >&2
    fi
    exit 1
fi

finish() {
    local status=$?
    if [[ -t 0 ]]; then
        printf '\nEnter 키를 누르면 창을 닫습니다. '
        read -r _ || true
    fi
    exit "$status"
}
trap finish EXIT

for tool in uvx ffmpeg ffprobe; do
    if ! command -v "$tool" >/dev/null 2>&1; then
        printf '필수 프로그램을 찾을 수 없습니다: %s\n' "$tool" >&2
        exit 1
    fi
done

uvx --refresh --from 'yt-dlp[default]' python -u "$SCRIPT_DIR/downloader.py" "$@"

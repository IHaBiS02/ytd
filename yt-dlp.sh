#!/usr/bin/env bash
set -uo pipefail

# Desktop sessions do not always inherit the interactive shell's PATH.
export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$HOME/.deno/bin:/home/linuxbrew/.linuxbrew/bin:$PATH"
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

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

uvx --refresh --from 'yt-dlp[default]' python "$SCRIPT_DIR/downloader.py" "$@"

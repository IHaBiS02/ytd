# YouTube 다운로드 런처

Linux에서 `.desktop` 아이콘을 클릭하고 영상·재생목록·채널 URL을 입력하면
`~/youtube`에 저장합니다. 팝업창에서 주소를 입력하고 **다운로드**를 누르면
같은 창에 준비·다운로드·병합 로그와 오류가 실시간으로 표시됩니다.
완료 후에도 창이 유지되어 로그를 확인할 수 있습니다. **중단**을 누르거나
진행 중인 창을 닫으면 다운로드와 병합 작업도 종료합니다.
로그 창은 최근 5,000줄을 표시합니다.

## 설치와 실행

필수 프로그램: `uvx`(uv에 포함), FFmpeg(`ffmpeg`, `ffprobe`), Deno 또는
지원되는 Node.js. GUI에는 `python3` 또는 `/usr/bin/python3`에서 불러올 수 있는
PySide6 6.7 이상이 필요합니다(현재 시스템에는 설치되어 있습니다).
터미널에서 주소 없이 실행하면
KDialog 또는 Zenity 입력창을 사용하고, 둘 다 없으면 터미널에서 입력받습니다.
현재 시스템의 Homebrew와 사용자 로컬 설치 경로도 런처가 검색합니다.
yt-dlp는 실행할 때 `uvx --refresh`로 갱신 확인합니다.

이 폴더에서 실행합니다.

```bash
python3 install.py
```

설치하면 앱 메뉴와 XDG 바탕화면에 **YouTube 다운로드**가 생깁니다.
KDE가 처음에 실행 허용을 물으면 허용합니다. 런처와 실행 파일은
`${XDG_DATA_HOME:-~/.local/share}` 아래에 복사되므로 원본 작업 폴더를
옮겨도 설치된 앱은 실행할 수 있습니다. 수정 후에는 설치 명령을 다시 실행합니다.
이 폴더의 `youtube-downloader.desktop`은 설치 없이도 쓸 수 있으며, 자신과 같은
폴더에 있는 `yt-dlp.sh`를 찾아 실행하므로 리포지토리를 어디에 두어도 됩니다.

## 저장 폴더

기본 저장 폴더는 `~/youtube`입니다. 창의 **폴더 선택…**으로 바꿀 수 있고,
선택한 폴더는 `${XDG_CONFIG_HOME:-~/.config}/youtube-downloader/download_dir`에
기록되어 다음 실행과 터미널 실행에도 적용됩니다. 터미널에서는
`YTD_DOWNLOAD_DIR` 환경 변수로 한 번만 다른 폴더를 지정할 수도 있습니다.

터미널 실행도 가능합니다.

```bash
./yt-dlp.sh 'https://www.youtube.com/playlist?list=...'
```

## 저장 구조

```text
저장 폴더/
├── 채널 또는 재생목록 이름 [ID]/
│   ├── metadata/
│   │   ├── source.info.json           # 입력한 대상의 헤더 정보와 원본 URL
│   │   ├── 이름 [ID].info.json        # yt-dlp의 채널/재생목록 정보
│   │   ├── 이름 [ID].description      # 제공되는 경우 설명
│   │   └── 이름 [ID].jpg 또는 webp    # 제공되는 경우 썸네일
│   └── videos/
│       └── 영상 제목 [영상 ID]/
│           ├── 영상 제목 [영상 ID].mkv
│           ├── 영상 제목 [영상 ID].info.json
│           ├── 영상 제목 [영상 ID].description
│           └── 썸네일, 자막
└── 단일 영상 제목 [영상 ID]/
    └── 영상 파일과 해당 영상의 부가 파일
```

동일한 이름의 다른 채널·재생목록이 섞이지 않도록 이름 뒤에 ID를 붙입니다.
파일명에 쓸 수 없는 문자는 바꾸고 긴 제목은 줄입니다.
채널 전체 URL의 영상·Shorts·라이브 탭은 같은 채널 폴더의 `videos`에 모으며,
각 탭의 메타데이터도 같은 `metadata`에 저장합니다. 특정 탭 URL은 그 탭만 받습니다.
실제 다운로드 범위는 yt-dlp가 해당 URL에서 제공하는 항목입니다.
`source.info.json`은 항목 목록을 제외한 헤더이며, 별도 yt-dlp JSON에
처리된 재생목록 정보가 저장됩니다. 비공개·삭제된 영상은 받을 수 없습니다.
영상 URL에 재생목록 매개변수(`list=`)가 있으면 재생목록 전체를 받습니다.

기존 스크립트의 썸네일, 설명, JSON, 댓글, 제공되는 모든 언어의 수동 자막,
메타데이터·챕터·자막·썸네일 삽입 설정을 유지합니다.
`-k`는 사용하지 않아 병합에 성공하면 병합 전 영상·오디오 파일은 삭제됩니다.
기존에 보관해 둔 파일을 일괄 삭제하지는 않습니다.
자동 생성 자막은 기존처럼 별도로 요청하지 않습니다. 댓글은 영상 JSON에 들어갑니다.
기존 251 오디오 선택식을 우선 사용하고, 해당 형식이 없으면 최선의 일반
영상+오디오 또는 통합 형식으로 대체한 뒤 MKV로 저장합니다.
사용자 yt-dlp 설정 파일은 저장 규칙의 일관성을 위해 읽지 않습니다.
실패한 항목이 있으면 오류 상태를 반환하며 완료로 표시하지 않습니다.

옵션 근거: [yt-dlp 공식 문서](https://github.com/yt-dlp/yt-dlp#output-template).

## 검증

```bash
bash -n yt-dlp.sh
desktop-file-validate youtube-downloader.desktop
python3 install.py --prefix /tmp/youtube-downloader-check
QT_QPA_PLATFORM=offscreen /usr/bin/python3 -m unittest -v test_gui
```

이 도구는 독립적인 Linux 다운로드 런처입니다.

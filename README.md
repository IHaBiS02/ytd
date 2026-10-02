# YouTube 다운로드 런처

Linux에서 `.desktop` 아이콘을 클릭하고 영상·재생목록·채널 URL을 입력하면
`~/youtube`에 저장합니다. KDE에서는 KDialog, 그 외에는 Zenity를 사용하며,
둘 다 없으면 터미널에서 입력받습니다. 진행 상황과 오류는 터미널에 표시됩니다.
끝나면 Enter 키로 창을 닫습니다.

## 설치와 실행

필수 프로그램: `uvx`(uv에 포함), FFmpeg(`ffmpeg`, `ffprobe`), Deno 또는
지원되는 Node.js. 입력창에는 KDialog 또는 Zenity가 필요합니다.
현재 시스템의 Homebrew와 사용자 로컬 설치 경로도 런처가 검색합니다.
yt-dlp는 실행할 때 `uvx --refresh`로 갱신 확인합니다.

```bash
python3 /path/to/ytd/install.py
```

설치하면 앱 메뉴와 XDG 바탕화면에 **YouTube 다운로드**가 생깁니다.
KDE가 처음에 실행 허용을 물으면 허용합니다. 런처와 실행 파일은
`${XDG_DATA_HOME:-~/.local/share}` 아래에 복사되므로 원본 작업 폴더를
옮겨도 설치된 앱은 실행할 수 있습니다. 수정 후에는 설치 명령을 다시 실행합니다.
이 폴더의 `youtube-downloader.desktop`은 현재 작업 폴더를 직접 실행합니다.

터미널 실행도 가능합니다.

```bash
/path/to/ytd/yt-dlp.sh 'https://www.youtube.com/playlist?list=...'
```

## 저장 구조

```text
~/youtube/
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
│           └── 썸네일, 자막, 병합 전 원본 파일
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
메타데이터·챕터·자막·썸네일 삽입 및 `-k` 원본 보관 설정을 유지합니다.
자동 생성 자막은 기존처럼 별도로 요청하지 않습니다. 댓글은 영상 JSON에 들어갑니다.
기존 251 오디오 선택식을 우선 사용하고, 해당 형식이 없으면 최선의 일반
영상+오디오 또는 통합 형식으로 대체한 뒤 MKV로 저장합니다.
사용자 yt-dlp 설정 파일은 저장 규칙의 일관성을 위해 읽지 않습니다.
실패한 항목이 있으면 오류 상태를 반환하며 완료로 표시하지 않습니다.

옵션 근거: [yt-dlp 공식 문서](https://github.com/yt-dlp/yt-dlp#output-template).

## 검증

```bash
bash -n /path/to/ytd/yt-dlp.sh
desktop-file-validate /path/to/ytd/youtube-downloader.desktop
python3 /path/to/ytd/install.py --prefix /tmp/youtube-downloader-check
```

이 도구는 독립적인 Linux 다운로드 런처입니다.

# 🎯 Contest Radar — IT/SW 공모전 모아보기

데이콘, 위비티, 링커리어, 씽굿, 컨테스트코리아에서 IT/SW 공모전을 자동으로 수집하고
Discord로 알림을 보내는 프로젝트입니다.

## 🗂️ 구조

```
├── crawler/
│   ├── main.py          # 크롤러 오케스트레이터
│   ├── notify.py        # Discord 웹훅 알림
│   ├── scrapers/        # 각 사이트별 스크래퍼
│   └── utils/           # 날짜 파싱, 중복 제거
├── data/
│   ├── contests.json    # 수집된 공모전 데이터
│   └── notified.json    # 알림 완료된 ID
├── index.html           # 웹 뷰어 (GitHub Pages)
└── .github/workflows/   # 자동화 워크플로우
```

## ⚙️ GitHub 설정

1. 이 레포를 **public**으로 생성
2. `Settings → Secrets → Actions`에서 `DISCORD_WEBHOOK_URL` 추가
3. `Settings → Pages`에서 Source를 **GitHub Actions**로 설정
4. 매일 오전 8시 KST에 자동 실행됩니다

## 🔧 로컬 실행

```bash
pip install -r crawler/requirements.txt
python -m crawler.main    # 크롤링
python -m crawler.notify  # Discord 알림
```

# Slack Scenario Bot

YouTube Short 시나리오를 자동으로 생성하고 한국어 TTS 음성 파일을 제공하는 슬랙 봇입니다.

## 주요 기능

-   🎥 **YouTube Short 시나리오 생성**: 주제와 내용을 입력하면 1분짜리 시나리오를 자동 생성
-   🎵 **한국어 TTS 변환**: 생성된 시나리오를 자연스러운 한국어 음성으로 변환
-   📁 **MP3 파일 생성**: 음성 파일을 MP3 형식으로 생성
-   📤 **슬랙 파일 업로드**: 생성된 MP3 파일을 슬랙 채널에 자동 업로드
-   🌐 **웹 인터페이스**: 로컬에서 시나리오 생성 및 음성 파일 다운로드 가능

## 설정

-   **Command**: `/scenario`
-   **URL**: `${ngrok}/slack/chat`
-   **Port**:
    -   Backend: 5001
    -   Frontend: 3000

## 사용법

### 1. 슬랙 봇 사용

슬랙에서 `/scenario` 명령어를 사용하여 시나리오를 생성할 수 있습니다:

#### 입력 형식

1. **쉼표로 구분**: `주제, 상세내용`

    - 예: `AI의 미래, AI가 경제생활에 미치는 영향`

2. **구조화된 형식**:
    ```
    주제: AI의 미래
    상세내용: AI가 경제생활에 미치는 영향
    ```

#### 출력 결과

-   📝 **텍스트 시나리오**: 시작, 본문, 마무리로 구성된 상세한 시나리오
-   🎵 **음성 파일**: 한국어 TTS로 변환된 MP3 파일 (슬랙에서 다운로드 가능)

### 2. 웹 인터페이스 사용

로컬에서 웹 브라우저를 통해 시나리오를 생성하고 음성 파일을 다운로드할 수 있습니다.

#### 실행 방법

1. **백엔드 서버 실행**:

    ```bash
    python3 slack_app.py
    ```

2. **프론트엔드 실행**:

    ```bash
    cd client
    npm install
    npm start
    ```

3. **브라우저에서 접속**:

    ```
    http://localhost:3000
    ```

#### 웹 인터페이스 기능

-   📝 **주제와 상세 내용 입력**
-   🎵 **시나리오 생성 및 음성 변환**
-   📥 **음성 파일 재생 및 다운로드**
-   📋 **생성된 시나리오 상세 보기**

## 필요한 환경 변수

`.env` 파일에 다음 변수들을 설정해야 합니다:

```env
SLACK_SIGNING_SECRET=your_slack_signing_secret
SLACK_BOT_TOKEN=your_slack_bot_token
OPENAI_API_KEY=your_openai_api_key
```

## 설치 및 실행

### 1. 백엔드 설정

```bash
# 패키지 설치
pip3 install flask slack-bolt flask-cors python-dotenv openai gtts

# 서버 실행
python3 slack_app.py
```

### 2. 프론트엔드 설정

```bash
# client 폴더로 이동
cd client

# 의존성 설치
npm install

# 개발 서버 실행
npm start
```

### 3. ngrok 터널링 (로컬 개발용)

```bash
ngrok http 5001
```

## 기술 스택

-   **Backend**: Flask, Slack Bolt
-   **Frontend**: React, Axios
-   **AI**: OpenAI GPT-4
-   **TTS**: Google Text-to-Speech (gTTS)
-   **Language**: Python 3.11+, JavaScript

## 파일 구조

```
slack_scenario_bot/
├── slack_app.py          # 메인 백엔드 애플리케이션
├── app.py               # 로그 API 서버
├── client/              # React 프론트엔드
│   ├── public/
│   ├── src/
│   └── package.json
├── static/              # 정적 파일 (음성 파일)
│   └── audio/
├── requirements.txt     # Python 패키지 의존성
├── README.md           # 프로젝트 문서
└── .env                # 환경 변수 (gitignore됨)
```

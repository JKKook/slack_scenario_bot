from flask import Flask, request, jsonify, Response
from slack_bolt import App
from slack_bolt.adapter.flask import SlackRequestHandler
import os
from datetime import datetime
from flask_cors import CORS
from dotenv import load_dotenv
from openai import OpenAI
import json
from collections import defaultdict
import re
from typing import Dict

# 환경 변수 로드
load_dotenv()

# Flask 앱 설정
app = Flask(__name__)
CORS(app)

# 환경 변수 디버깅
print(f"SLACK_SIGNING_SECRET: {os.environ.get('SLACK_SIGNING_SECRET')}")
print(f"SLACK_BOT_TOKEN: {os.environ.get('SLACK_BOT_TOKEN')}")
print(f"OPENAI_API_KEY: {os.environ.get('OPENAI_API_KEY')}")

# Slack Bolt 앱 설정 (동기 모드)
slack_app = App(
    signing_secret=os.environ.get("SLACK_SIGNING_SECRET"),
    token=os.environ.get("SLACK_BOT_TOKEN")
)
handler = SlackRequestHandler(slack_app)

# OpenAI 클라이언트 초기화
openai_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# 메시지 히스토리 저장
message_history = defaultdict(list)
MAX_HISTORY = 10

# 로그 데이터 저장 리스트
logs = []

# 주제와 내용을 분석하여 적절한 어조를 결정하는 함수
def analyze_topic_and_content(topic, outline):
    """주제와 내용을 분석하여 적절한 어조를 결정하는 함수"""
    analysis_prompt = f"""다음 주제와 내용을 분석하여 YouTube Short 시나리오에 가장 적합한 어조를 선택해 줘.

주제: {topic}
내용: {outline}

다음 중 가장 적합한 어조를 하나만 선택하고, 그 이유를 간단히 설명해:
1. 친근하고 일상적인 어조: 친구처럼 편하게 소통, 쉬운 단어, 따뜻하고 긍정적인 톤 (기본 선호).
2. 유머러스하고 재미있는 어조: 재치 있고 경쾌한 표현, 가벼운 농담, 밝은 에너지 (엔터테인먼트, 가벼운 주제).
3. 영감을 주고 동기부여가 되는 어조: 열정적이고 감동적, 행동 촉진 (자기계발, 도전 주제).
4. 교육적이고 설명적인 어조: 명확하고 정보 중심, 차분한 톤 (과학, 역사, 심각한 주제).
5. 전문적이고 격식있는 어조: 신뢰감 있는 말투, 공식적인 톤 (경제, 기술 주제, 드물게 사용).

- 기본적으로 '친근하고 일상적인 어조'를 선호해. 주제와 내용의 맥락에 따라 조정:
  - 경제/기술 주제: 친근하되 믿음직스럽게.
  - 환경/사회 문제: 친근하면서 살짝 진지하게.
  - 가벼운 주제: 유머러스하거나 캐주얼하게.
- 선택한 어조와 이유를 JSON 형식으로 응답:
{{
    "tone": "선택한 어조",
    "reason": "선택 이유"
}}
"""

    try:
        response = openai_client.chat.completions.create(
            model="gpt-4.1-nano",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": analysis_prompt}
            ],
            max_tokens=200,
            temperature=0.3
        )
        
        # JSON 응답 파싱
        analysis_result = json.loads(response.choices[0].message.content.strip())
        logs.append({
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'level': 'INFO',
            'message': f"Tone analysis: {analysis_result}"
        })
        return analysis_result
    except Exception as e:
        logs.append({
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'level': 'ERROR',
            'message': f"Tone analysis error: {str(e)}"
        })
        return {
            "tone": "친근하고 일상적인 어조",
            "reason": f"기본값으로 설정: {str(e)}"
        }

# 시나리오 생성을 위한 프롬프트 생성
def generate_scenario_prompt(topic, outline, tone_analysis):
    """시나리오 생성을 위한 프롬프트 생성"""
    tone_guidelines = {
        "친근하고 일상적인 어조": "친구랑 수다 떨듯이 캐주얼하고 따뜻한 말투, 쉬운 단어, '진짜', '완전', '쉽게 말하면' 같은 표현, 긍정적이고 가까운 느낌. 예: '야, 이거 진짜 대박 아니야?'",
        "유머러스하고 재미있는 어조": "재치 있고 경쾌한 표현, 가벼운 농담과 유머, 밝고 에너지 넘치는 톤. 예: '이거 완전 터진다, 진짜 웃겨!'",
        "영감을 주고 동기부여가 되는 어조": "열정적이고 감동적인 문장, '너도 할 수 있어!' 같은 도전적인 메시지, 감정을 고양시키는 톤. 예: '지금 시작하면 너도 바꿀 수 있어!'",
        "교육적이고 설명적인 어조": "명확하고 체계적인 설명, 정보 중심, 차분하고 이해하기 쉬운 톤, 약간 진지한 느낌. 예: '쉽게 말하면, 이건 이렇게 작동해.'",
        "전문적이고 격식있는 어조": "짧고 간결한 문장, 신뢰감 있는 말투, 전문 용어 적절히 사용, 공식적이지만 딱딱하지 않은 톤. 예: '이 기술은 시장을 혁신하고 있습니다.'"
    }
    
    tone_instruction = tone_guidelines.get(tone_analysis['tone'], "친구처럼 편하게, 쉬운 단어로, 따뜻한 톤.")
    
    return f"""다음 정보를 바탕으로 1분짜리 YouTube Short 시나리오를 작성해 줘!

주제: {topic}
상세 내용: {outline}
선택된 어조: {tone_analysis['tone']}
선택 이유: {tone_analysis['reason']}

### 지침
- **주제와 내용 준수**: 주제와 상세 내용에 딱 맞게 써 줘. 관련 없는 이야기는 절대 넣지 마!
  - 예: 주제가 'AI의 미래'이고 상세 내용이 'AI가 경제생활에 미치는 영향'이라면, AI가 경제에 미치는 영향(예: 자동화로 비용 절감, AI 스타트업, 경제적 격차)과 미래 전망에 집중.
- **어조 일관성**: 선택된 어조를 처음부터 끝까지 유지해. 시나리오 말투는 어조에 맞게!
  - 어조 가이드라인: {tone_instruction}
  - 예: 경제/기술 주제는 친근하되 믿음직스럽게, 환경 주제는 친근하면서 살짝 진지하게.
- **응답 형식**: 문장은 한 줄로 깔끔하게, 문장 단위로만 띄어쓰기. 불필요한 줄바꿈이나 단어 분리(예: 'A • I') 절대 안 돼.
- **구체적 사례 포함**: 주제와 관련된 실제 사례나 미래 전망을 넣어서 생동감 있게.
  - 예: AI 스타트업 사례, 경제적 격차 데이터, 특정 산업 변화.
- **유효한 응답 보장**: 모든 섹션(시작, 본문, 마무리)이 비어 있지 않도록 명확히 채워. 비어 있으면 안 돼!

### 시나리오 형식
[시작 부분 (0-10초)]
- 시청자 눈길을 사로잡는 오프닝 (최소 1-2문장).
- 주제와 핵심 메시지 간단히 소개.
- 선택된 어조로 친근하게.

[본문 (10-45초)]
- 주요 포인트 3개 (각 8-10초, 각 최소 1-2문장).
- 각 포인트는 주제와 상세 내용에 맞는 구체적인 사례나 설명 포함.
- 선택된 어조로 자연스럽게.

[마무리 (45-60초)]
- 핵심 메시지 다시 강조 (최소 1-2문장).
- 행동 유도 (예: 구독, 공유, '너도 해봐!').
- 선택된 어조로 마무리.

### 주의사항
- 1분 안에 끝나도록 시간 엄격히 지켜.
- 각 섹션 시간 명시해.
- 구어체로, 친구한테 말하듯이 자연스럽게.
- 시각적 요소 힌트 넣어 (예: 그래픽, 짧은 클립).
- 모든 섹션이 반드시 채워져야 해. 빈 섹션(예: 시작, 본문, 마무리 중 하나라도 비어 있음)은 절대 안 돼.
- 불필요한 줄바꿈, 단어 분리, 관련 없는 내용 절대 넣지 마.

### 예시 (친근하고 일상적인 어조)
[시작 부분 (0-10초)]
"야, AI가 진짜 우리 삶을 어떻게 바꾸는지 궁금하지 않아? 쉽게 말하면, AI 덕에 돈 버는 방식이 완전 달라지고 있어!" (시각: AI 로봇 클립)
[본문 (10-45초)]
- "AI가 물류 창고에서 물건 옮기면 비용이 팍 줄어! 예를 들어, 아마존 창고에서 로봇이 쌩쌩 달리고 있어." (시각: 창고 로봇 영상)
- "AI 스타트업이 완전 뜨고 있어. 병 진단하는 AI 앱도 나왔어!" (시각: 스타트업 로고)
- "근데 AI 때문에 일자리 바뀌고, 못 따라가면 좀 뒤처질 수도 있거든." (시각: 데이터 그래프)
[마무리 (45-60초)]
"AI는 우리 미래를 더 편리하게 만들 거야! 구독 눌러서 더 신기한 이야기 들어볼래?" (시각: 구독 버튼)
"""

# 사용자 입력 파싱
def parse_user_input(text: str) -> Dict[str, str]:
    """
    사용자 입력을 파싱하여 topic과 outline을 추출. 유효성 검증 후 결과 반환.
    
    Args:
        text (str): 슬랙에서 받은 사용자 입력 텍스트
        
    Returns:
        Dict[str, str]: {'topic': str, 'outline': str, 'error': str | None}
            - error가 None이면 유효한 입력, 아니면 오류 메시지 포함
            
    Raises:
        None: 모든 예외는 내부에서 처리
    """
    logs.append({
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'level': 'INFO',
        'message': f"Parsing input: {text[:100]}"  # 긴 입력은 잘라서 로그
    })
    
    result = {'topic': '', 'outline': '', 'error': None}
    
    # 1. 입력 기본 검증
    if not text or not text.strip():
        result['error'] = "입력이 비어있어요! 주제와 내용을 입력해 주세요."
        logs.append({
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'level': 'WARNING',
            'message': "Empty input received"
        })
        return result
    
    # 2. 입력 길이 제한 (예: 1000자 이내)
    MAX_INPUT_LENGTH = 1000
    if len(text) > MAX_INPUT_LENGTH:
        result['error'] = f"입력 길이가 너무 길어요! {MAX_INPUT_LENGTH}자 이내로 입력해 주세요."
        logs.append({
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'level': 'WARNING',
            'message': f"Input too long: {len(text)} characters"
        })
        return result
    
    # 3. 특수 문자 및 비정상 입력 필터링
    if not re.match(r'^[\w\s,.!?:;()\-"\']+$', text, re.UNICODE):
        result['error'] = "허용되지 않은 특수 문자가 포함되어 있어요! 문자, 숫자, 기본 기호만 사용해 주세요."
        logs.append({
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'level': 'WARNING',
            'message': "Invalid characters in input"
        })
        return result
    
    # 4. '주제: ... \n상세내용: ...' 형식 처리
    patterns = {
        "topic": r"주제[:：]?\s*(.*?)(?=\s*상세내용|$)",
        "outline": r"상세내용[:：]?\s*(.*?)$"
    }
    
    for key, pattern in patterns.items():
        match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        if match:
            result[key] = match.group(1).strip()
    
    # 5. 'topic, outline' 형식 처리
    if not result['topic'] and not result['outline']:
        if ',' in text:
            parts = text.split(',', 1)  # 첫 번째 쉼표로 분리
            result['topic'] = parts[0].strip()
            result['outline'] = parts[1].strip() if len(parts) > 1 else ""
        else:
            result['topic'] = text.strip()
            result['outline'] = text.strip()  # outline 없으면 topic과 동일
    
    # 6. 최종 유효성 검증
    MIN_LENGTH = 3
    if not result['topic'] or len(result['topic']) < MIN_LENGTH:
        result['error'] = f"주제가 너무 짧아요! 최소 {MIN_LENGTH}자 이상 입력해 주세요."
        logs.append({
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'level': 'WARNING',
            'message': "Topic too short or empty"
        })
        return result
    
    if not result['outline'] or len(result['outline']) < MIN_LENGTH:
        result['error'] = f"상세 내용이 너무 짧아요! 최소 {MIN_LENGTH}자 이상 입력해 주세요."
        logs.append({
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'level': 'WARNING',
            'message': "Outline too short or empty"
        })
        return result
    
    # 7. 성공 로그
    logs.append({
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'level': 'INFO',
        'message': f"Valid input parsed: {result['topic'][:50]}, {result['outline'][:50]}"
    })
    
    return result

# GPT 응답을 구조화된 형식으로 변환, 빈 응답 검증
def format_scenario_response(response_text):
    """GPT 응답을 구조화된 형식으로 변환, 빈 응답 검증"""
    sections = {
        "opening": "",
        "main_points": [],
        "closing": ""
    }
    
    current_section = None
    current_point = []
    
    # 응답을 줄 단위로 처리
    for line in response_text.split('\n'):
        line = line.strip()
        if not line:
            continue
        if '[시작 부분' in line:
            current_section = 'opening'
            continue
        elif '[본문' in line:
            current_section = 'main_points'
            continue
        elif '[마무리' in line:
            current_section = 'closing'
            continue
        elif current_section:
            if current_section == 'main_points':
                if line.startswith('-') or line.startswith('•'):
                    if current_point:
                        # 이전 포인트 저장
                        sections['main_points'].append(' '.join(current_point).strip())
                        current_point = []
                    current_point.append(line[1:].strip())
                else:
                    current_point.append(line)
            else:
                sections[current_section] += line + ' '
    
    # 마지막 main_points 처리
    if current_point:
        sections['main_points'].append(' '.join(current_point).strip())
    
    # 섹션 정리: 불필요한 공백 제거
    for key in sections:
        if key != 'main_points':
            sections[key] = ' '.join(sections[key].split()).strip()
    
    # 빈 응답 검증
    if not sections['opening'] or not sections['main_points'] or not sections['closing']:
        raise ValueError("빈 응답: 시작, 본문, 마무리 중 하나 이상이 비어 있습니다.")
    
    return sections

# 슬래시 명령어 처리 (/scenario)
@slack_app.command("/scenario")
def handle_scenario_command(ack, say, command):
    try:
        ack()  # 즉시 응답
        user_id = command.get('user_id', 'Unknown')
        user_name = command.get('user_name', 'Unknown')
        text = command.get('text', '').strip()
        
        print(f"Received command from {user_id} ({user_name}): {text}")
        logs.append({
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'level': 'INFO',
            'message': f"Received command from {user_id}: {text[:100]}"
        })

        # 사용자 입력 파싱
        parsed_input = parse_user_input(text)
        if parsed_input['error']:
            say(
                f"앗, 입력이 잘못됐어요! 😅\n"
                f"오류: {parsed_input['error']}\n"
                f"예시:\n"
                f"- topic, outline (예: AI의 미래, AI가 경제생활에 미치는 영향)\n"
                f"- 주제: [주제]\n상세내용: [상세 내용]"
            )
            return

        # 주제와 내용 분석 (OpenAI 호출)
        tone_analysis = analyze_topic_and_content(
            parsed_input['topic'],
            parsed_input['outline']
        )
        
        # 프롬프트 생성
        prompt = generate_scenario_prompt(
            parsed_input['topic'],
            parsed_input['outline'],
            tone_analysis
        )
        
        # OpenAI API 호출 (최대 2번 시도)
        formatted_response = None
        max_attempts = 2
        for attempt in range(max_attempts):
            try:
                response = openai_client.chat.completions.create(
                    model="gpt-4.1-nano",
                    messages=[
                        {"role": "system", "content": "You are a super friendly assistant who talks like a close friend, creating fun and engaging YouTube Short scenarios!"},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=400,
                    temperature=0.6,
                    presence_penalty=0.6,
                    frequency_penalty=0.6
                )
                
                # 응답 포맷팅 및 검증
                formatted_response = format_scenario_response(response.choices[0].message.content.strip())
                break  # 성공 시 루프 종료
            except ValueError as ve:
                logs.append({
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'level': 'WARNING',
                    'message': f"Attempt {attempt + 1} failed: {str(ve)}"
                })
                if attempt == max_attempts - 1:
                    say("앗, 뭔가 잘못됐어! 주제나 내용을 다시 확인해 줘! 😅")
                    return
                continue
            except Exception as e:
                logs.append({
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'level': 'ERROR',
                    'message': f"Attempt {attempt + 1} failed: {str(e)}"
                })
                if attempt == max_attempts - 1:
                    say(f"으잉, 뭔가 꼬였나 봐... 오류: {str(e)} 😓")
                    return
                continue
        
        if not formatted_response:
            say("앗, 뭔가 잘못됐어! 주제나 내용을 다시 확인해 줘! 😅")
            return
        
        # 메시지 히스토리 업데이트
        message_history[user_id].append(json.dumps(formatted_response))
        if len(message_history[user_id]) > MAX_HISTORY:
            message_history[user_id].pop(0)
        
        # Slack 메시지 포맷팅
        slack_message = f"""🎥 *{parsed_input['topic']}* - YouTube Short 시나리오

*어조*: {tone_analysis['tone']}
*왜냐면*: {tone_analysis['reason']}

**시작 (0-10초)**
{formatted_response['opening']}

**본문 (10-45초)**
{chr(10).join(f"• {point}" for point in formatted_response['main_points'] if point)}

**마무리 (45-60초)**
{formatted_response['closing']}

💡 *꿀팁!*
- 시간 딱 맞춰서 연습해 봐!
- 그래픽이나 클립 넣으면 더 폼 나!
- 대본 몇 번 읽어보면 자연스럽게 말할 수 있어.
- 어조 끝까지 유지하면 진짜 멋질 거야!"""
        
        say(slack_message)
        
        logs.append({
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'level': 'INFO',
            'message': f"Generated scenario for {user_id}: {parsed_input['topic']}"
        })
    except Exception as e:
        print(f"Error in handle_scenario_command: {e}")
        logs.append({
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'level': 'ERROR',
            'message': f"Error in handle_scenario_command: {str(e)}"
        })
        say(f"으잉, 뭔가 꼬였나 봐... 오류: {str(e)} 😓")
        
# Flask 라우트로 Slack 요청 처리
@app.route("/slack/chat", methods=["GET", "POST"])
def slack_chat():
    print(f"Received request: {request.method} {request.path}")
    print(f"Headers: {request.headers}")
    print(f"Body: {request.get_data(as_text=True)}")
    print(f"Form data: {request.form}")
    print(f"SLACK_SIGNING_SECRET: {os.environ.get('SLACK_SIGNING_SECRET')}")
    if request.method == "GET":
        return jsonify({"status": "Server is running"}), 200
    try:
        response = handler.handle(request)
        if response is None:
            print("Warning: handler.handle returned None")
            return jsonify({"error": "No response from Slack handler"}), 500
        return response
    except Exception as e:
        print(f"Error in slack_chat: {e}")
        logs.append({
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'level': 'ERROR',
            'message': f"Error in slack_chat: {str(e)}"
        })
        return jsonify({"error": str(e)}), 500

# 로그 조회 API
@app.route("/api/logs", methods=["GET"])
def get_logs():
    return jsonify(logs)

# 로그 초기화 API
@app.route("/api/clear-logs", methods=["POST"])
def clear_logs():
    global logs
    logs = []
    return jsonify({'status': 'success'})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5001, debug=True)

import os
import json
import argparse
from datetime import datetime
from pathlib import Path

import requests
from dotenv import load_dotenv


def validate_date(date_text: str) -> str:
    """
    YYYY-MM-DD 형식 검증
    형식이 맞지 않으면 ValueError 발생
    """
    datetime.strptime(date_text, "%Y-%m-%d")
    return date_text


def parse_args():
    parser = argparse.ArgumentParser(
        description="여행 날짜를 입력받아 LLM으로 국내 여행 추천 JSON을 생성합니다."
    )
    parser.add_argument(
        "-date",
        required=True,
        help='여행 날짜 (형식: YYYY-MM-DD)'
    )

    args = parser.parse_args()

    try:
        validate_date(args.date)
    except ValueError:
        print("[오류] 날짜 형식이 올바르지 않습니다. 예: 2025-10-15\n")
        parser.print_help()
        raise SystemExit(1)

    return args


def get_env_value(key: str) -> str:
    value = os.getenv(key)
    if not value:
        print(f"[오류] 환경변수 {key} 가 설정되지 않았습니다.")
        print("설정 예시:")
        print('  macOS/Linux: export OPENAI_API_KEY="YOUR_KEY"')
        print('  Windows PowerShell: $env:OPENAI_API_KEY="YOUR_KEY"')
        raise SystemExit(1)
    return value


def build_messages(date_str: str, retry: bool = False):
    """
    retry=False : 일반 요청
    retry=True  : JSON 파싱 실패 후 더 강하게 제한한 재요청
    """
    system_prompt = (
        "당신은 국내 여행 추천 도우미입니다. "
        "반드시 JSON 객체만 출력하세요. "
        "설명 문장, 마크다운, 코드블록, ```json 표시를 절대 포함하지 마세요."
    )

    if not retry:
        user_prompt = f"""
사용자가 입력한 여행 날짜는 {date_str} 입니다.

아래 스키마를 만족하는 JSON 객체만 출력하세요.
필수 키:
- recommended_city: string
- weather: string
- events: array of string (1~3개)
- reason: string

조건:
- 국내 여행지만 추천
- reason은 2~4문장 정도
- events는 문자열 배열
- JSON 외 다른 텍스트 금지

예시 형식:
{{
  "recommended_city": "제주",
  "weather": "온화하고 바람이 다소 불 수 있습니다.",
  "events": ["지역 축제", "야시장", "문화 행사"],
  "reason": "이 시기에는 풍경과 먹거리를 함께 즐기기 좋습니다. 여행 동선도 비교적 짜기 쉽습니다."
}}
""".strip()
    else:
        user_prompt = f"""
이전 응답은 JSON 파싱에 실패했습니다.
반드시 아래 4개 키만 포함한 유효한 JSON 객체만 다시 출력하세요.
절대 코드블록, 설명, 주석, 문장 추가 금지.

입력 날짜: {date_str}

필수 스키마:
{{
  "recommended_city": "string",
  "weather": "string",
  "events": ["string", "string"],
  "reason": "string"
}}
""".strip()

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]


def request_openai_chat(api_key: str, model: str, messages: list) -> str:
    """
    OpenAI Chat Completions API 호출
    반환값: 모델이 생성한 텍스트
    """
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.7,
    }

    response = requests.post(url, headers=headers, json=payload, timeout=30)
    response.raise_for_status()

    data = response.json()
    return data["choices"][0]["message"]["content"].strip()


def parse_llm_json(text: str) -> dict:
    """
    LLM 응답 텍스트를 JSON으로 파싱하고,
    최소 스키마를 검사합니다.
    """
    result = json.loads(text)

    required_keys = ["recommended_city", "weather", "events", "reason"]
    for key in required_keys:
        if key not in result:
            raise ValueError(f"필수 키 누락: {key}")

    if not isinstance(result["recommended_city"], str):
        raise ValueError("recommended_city 는 string 이어야 합니다.")
    if not isinstance(result["weather"], str):
        raise ValueError("weather 는 string 이어야 합니다.")
    if not isinstance(result["events"], list):
        raise ValueError("events 는 array(list) 이어야 합니다.")
    if not isinstance(result["reason"], str):
        raise ValueError("reason 는 string 이어야 합니다.")

    return result


def get_travel_recommendation(date_str: str, api_key: str, model: str, errors: list) -> dict:
    """
    LLM 호출 + JSON 파싱
    파싱 실패 시 최대 1회 재시도
    """
    for attempt in range(2):  # 최대 2번: 최초 1회 + 재시도 1회
        retry = (attempt == 1)

        try:
            print(f"[로그] LLM 추천 요청 중... (시도 {attempt + 1}/2)")
            messages = build_messages(date_str, retry=retry)
            content = request_openai_chat(api_key, model, messages)

            print("[로그] LLM 응답 수신 완료")
            result = parse_llm_json(content)
            return result

        except json.JSONDecodeError as e:
            error_msg = f"LLM JSON 파싱 실패 (시도 {attempt + 1}): {str(e)}"
            print(f"[경고] {error_msg}")
            errors.append(error_msg)

        except requests.exceptions.RequestException as e:
            error_msg = f"LLM API 요청 실패 (시도 {attempt + 1}): {str(e)}"
            print(f"[오류] {error_msg}")
            errors.append(error_msg)
            break

        except ValueError as e:
            error_msg = f"LLM 응답 스키마 오류 (시도 {attempt + 1}): {str(e)}"
            print(f"[경고] {error_msg}")
            errors.append(error_msg)

    raise RuntimeError("LLM으로부터 유효한 JSON 응답을 얻지 못했습니다.")


def save_step1_result(date_str: str, recommendation: dict, errors: list):
    results_dir = Path("results")
    results_dir.mkdir(exist_ok=True)

    output_path = results_dir / f"{date_str}_step1_recommendation.json"

    data = {
        "input_date": date_str,
        "recommendation": recommendation,
        "errors": errors
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"[로그] 결과 JSON 저장 완료: {output_path}")


def main():
    load_dotenv()

    args = parse_args()
    date_str = args.date

    api_key = get_env_value("OPENAI_API_KEY")
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    errors = []

    try:
        recommendation = get_travel_recommendation(
            date_str=date_str,
            api_key=api_key,
            model=model,
            errors=errors,
        )

        print("\n[1차 추천 결과]")
        print(json.dumps(recommendation, ensure_ascii=False, indent=2))

        save_step1_result(date_str, recommendation, errors)

    except RuntimeError as e:
        print(f"[오류] {str(e)}")
        print("[종료] 1단계 실행을 중단합니다.")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
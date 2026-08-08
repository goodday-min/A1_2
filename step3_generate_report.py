
import os
import json
import argparse
from pathlib import Path

import requests
from dotenv import load_dotenv


def parse_args():
    parser = argparse.ArgumentParser(
        description="추천 JSON과 맛집 JSON을 바탕으로 최종 여행 Markdown 리포트를 생성합니다."
    )
    parser.add_argument(
        "-date",
        required=True,
        help='여행 날짜 (예: "2025-10-15")'
    )
    return parser.parse_args()


def get_env_value(key: str) -> str:
    value = os.getenv(key)
    if not value:
        print(f"[오류] 환경변수 {key} 가 설정되지 않았습니다.")
        print("설정 예시:")
        print('  macOS/Linux: export OPENAI_API_KEY="YOUR_KEY"')
        print('  Windows PowerShell: $env:OPENAI_API_KEY="YOUR_KEY"')
        raise SystemExit(1)
    return value


def request_openai_chat(api_key: str, model: str, messages: list) -> str:
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


def load_step_files(date_str: str):
    """
    1단계 결과 파일과 2단계 결과 파일을 읽어옵니다.
    1단계 파일은 필수, 2단계 파일은 없을 수도 있습니다.
    """
    results_dir = Path("results")

    step1_path = results_dir / f"{date_str}_step1_recommendation.json"
    if not step1_path.exists():
        raise FileNotFoundError(f"1단계 결과 파일이 없습니다: {step1_path}")

    with open(step1_path, "r", encoding="utf-8") as f:
        step1_data = json.load(f)

    recommendation = step1_data["recommendation"]
    errors = step1_data.get("errors", [])

    city = recommendation["recommended_city"]
    safe_city = city.replace(" ", "_")
    step2_path = results_dir / f"{safe_city}_step2_restaurants.json"

    restaurants = []
    if step2_path.exists():
        with open(step2_path, "r", encoding="utf-8") as f:
            step2_data = json.load(f)
        restaurants = step2_data.get("restaurants", [])
        errors.extend(step2_data.get("errors", []))

    return recommendation, restaurants, errors


def build_report_messages(date_str: str, recommendation: dict, restaurants: list):
    system_prompt = (
        "당신은 국내 여행 리포트를 작성하는 도우미입니다. "
        "반드시 Markdown 형식으로만 출력하세요. "
        "과장된 표현은 피하고, 읽기 쉬운 구조로 작성하세요."
    )

    if restaurants:
        restaurant_text = json.dumps(restaurants, ensure_ascii=False, indent=2)
    else:
        restaurant_text = "[]"

    user_prompt = f"""
여행 날짜: {date_str}

추천 정보:
{json.dumps(recommendation, ensure_ascii=False, indent=2)}

맛집 목록:
{restaurant_text}

아래 항목을 포함한 Markdown 여행 리포트를 작성하세요.

필수 포함 항목:
1. 추천 지역 + 추천 이유 요약
2. 날씨 요약
3. 행사/축제 목록
4. 맛집 리스트 (맛집이 0건이면 "데이터 없음"이라고 표기)
5. 1일 일정 제안 (오전 / 오후 / 저녁)

작성 규칙:
- 제목 1개 포함
- 소제목을 적절히 사용
- 맛집은 bullet list로 정리
- 일정은 오전/오후/저녁으로 구분
- 맛집이 없으면 억지로 만들어내지 말고 "데이터 없음"이라고 쓸 것
""".strip()

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]


def generate_markdown_report(date_str: str, recommendation: dict, restaurants: list,
                             api_key: str, model: str, errors: list) -> str:
    try:
        print("[로그] 최종 리포트 생성을 위해 LLM 호출 중...")
        messages = build_report_messages(date_str, recommendation, restaurants)
        report_md = request_openai_chat(api_key, model, messages)
        return report_md
    except requests.exceptions.RequestException as e:
        error_msg = f"최종 리포트 LLM 호출 실패: {str(e)}"
        print(f"[오류] {error_msg}")
        errors.append(error_msg)
        raise RuntimeError("최종 리포트 생성에 실패했습니다.")


def save_report_and_raw(date_str: str, recommendation: dict, restaurants: list, errors: list, report_md: str):
    results_dir = Path("results")
    results_dir.mkdir(exist_ok=True)

    raw_path = results_dir / f"{date_str}_final_data.json"
    md_path = results_dir / f"{date_str}_travel_report.md"

    raw_data = {
        "recommendation": recommendation,
        "restaurants": restaurants,
        "errors": errors
    }

    with open(raw_path, "w", encoding="utf-8") as f:
        json.dump(raw_data, f, ensure_ascii=False, indent=2)

    with open(md_path, "w", encoding="utf-8") as f:
        f.write(report_md)

    print(f"[로그] 최종 데이터 저장 완료: {raw_path}")
    print(f"[로그] Markdown 리포트 저장 완료: {md_path}")


def main():
    load_dotenv()
    args = parse_args()

    date_str = args.date
    api_key = get_env_value("OPENAI_API_KEY")
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    try:
        recommendation, restaurants, errors = load_step_files(date_str)

        report_md = generate_markdown_report(
            date_str=date_str,
            recommendation=recommendation,
            restaurants=restaurants,
            api_key=api_key,
            model=model,
            errors=errors
        )

        print("\n[최종 Markdown 리포트]\n")
        print(report_md)

        save_report_and_raw(
            date_str=date_str,
            recommendation=recommendation,
            restaurants=restaurants,
            errors=errors,
            report_md=report_md
        )

    except FileNotFoundError as e:
        print(f"[오류] {str(e)}")
        raise SystemExit(1)

    except RuntimeError as e:
        print(f"[오류] {str(e)}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
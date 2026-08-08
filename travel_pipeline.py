
import os
import json
import argparse
from pathlib import Path
from datetime import datetime

import requests
from dotenv import load_dotenv
from openai import OpenAI


# =========================
# 공통 유틸
# =========================
RESULTS_DIR = Path("results")


def ensure_results_dir():
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)


def save_json(file_path: Path, data: dict):
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def save_text(file_path: Path, text: str):
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(text)


def validate_date(date_str: str) -> str:
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return date_str
    except ValueError:
        raise ValueError("날짜는 YYYY-MM-DD 형식의 올바른 날짜여야 합니다.")


def dedupe_errors(errors: list[str]) -> list[str]:
    seen = set()
    result = []
    for err in errors:
        if err and err not in seen:
            seen.add(err)
            result.append(err)
    return result


def normalize_recommendation(data: dict) -> dict:
    return {
        "recommended_city": data.get("recommended_city", ""),
        "weather": data.get("weather", ""),
        "events": data.get("events", []) if isinstance(data.get("events", []), list) else [],
        "reason": data.get("reason", "")
    }


# =========================
# 1단계: 여행지 추천
# =========================
def get_travel_recommendation(travel_date: str, errors: list[str]) -> dict:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        errors.append("OpenAI API 키가 설정되지 않았습니다. (.env의 OPENAI_API_KEY 확인)")
        return {}

    client = OpenAI(api_key=api_key)

    prompt = f"""
당신은 국내 여행 추천 전문가입니다.

입력 날짜: {travel_date}

사용자에게 한국의 여행지 1곳을 추천하세요.
날짜에 맞는 계절감, 날씨 분위기, 어울리는 행사/활동을 반영하세요.

반드시 아래 JSON 객체만 반환하세요.
설명 문장, 마크다운, 코드블록은 절대 포함하지 마세요.

{{
  "recommended_city": "추천 도시명",
  "weather": "날씨 설명",
  "events": ["활동1", "활동2", "활동3"],
  "reason": "추천 이유"
}}
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "당신은 JSON만 반환하는 여행 추천 도우미입니다."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            response_format={"type": "json_object"}
        )

        content = response.choices[0].message.content
        data = json.loads(content)
        return normalize_recommendation(data)

    except Exception as e:
        errors.append(f"OpenAI 추천 생성 실패: {e}")
        return {}


# =========================
# 2단계: Kakao 맛집 검색
# =========================
def search_kakao_restaurants(city: str, errors: list[str], size: int = 5) -> list[dict]:
    api_key = os.getenv("KAKAO_REST_API_KEY")
    if not api_key:
        errors.append("Kakao REST API 키가 설정되지 않았습니다. (.env의 KAKAO_REST_API_KEY 확인)")
        return []

    url = "https://dapi.kakao.com/v2/local/search/keyword.json"
    headers = {
        "Authorization": f"KakaoAK {api_key}"
    }
    params = {
        "query": f"{city} 맛집",
        "size": size,
        "sort": "accuracy"
    }

    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)

        try:
            response.raise_for_status()
        except requests.HTTPError as e:
            raise requests.HTTPError(f"{e} | 응답본문: {response.text[:200]}")

        data = response.json()
        documents = data.get("documents", [])

        restaurants = []
        for doc in documents:
            restaurants.append({
                "name": doc.get("place_name", ""),
                "address": doc.get("road_address_name") or doc.get("address_name", ""),
                "phone": doc.get("phone", ""),
                "place_url": doc.get("place_url", ""),
                "category": doc.get("category_name", "")
            })

        return restaurants

    except Exception as e:
        errors.append(f"지도 API 요청 실패: {e}")
        return []


# =========================
# 3단계: Markdown 리포트 생성
# =========================
def build_markdown_report(travel_date: str, recommendation: dict, restaurants: list[dict], errors: list[str]) -> str:
    city = recommendation.get("recommended_city", "추천 없음")
    weather = recommendation.get("weather", "정보 없음")
    events = recommendation.get("events", [])
    reason = recommendation.get("reason", "정보 없음")

    lines = [
        f"# 국내 여행 추천 리포트",
        "",
        f"- 여행 날짜: **{travel_date}**",
        f"- 추천 도시: **{city}**",
        "",
        "## 1. 추천 이유",
        reason,
        "",
        "## 2. 예상 날씨",
        weather,
        "",
        "## 3. 추천 활동"
    ]

    if events:
        for event in events:
            lines.append(f"- {event}")
    else:
        lines.append("- 추천 활동 정보가 없습니다.")

    lines.extend([
        "",
        "## 4. 맛집 추천"
    ])

    if restaurants:
        for idx, place in enumerate(restaurants, start=1):
            lines.extend([
                f"### {idx}. {place.get('name', '')}",
                f"- 주소: {place.get('address', '')}",
                f"- 전화번호: {place.get('phone', '') or '정보 없음'}",
                f"- 카테고리: {place.get('category', '') or '정보 없음'}",
                f"- 링크: {place.get('place_url', '') or '정보 없음'}",
                ""
            ])
    else:
        lines.append("- 맛집 정보를 불러오지 못했습니다.")
        lines.append("")

    lines.append("## 5. 오류 로그")
    if errors:
        for err in errors:
            lines.append(f"- {err}")
    else:
        lines.append("- 없음")

    return "\n".join(lines)


# =========================
# 메인 실행
# =========================
def main():
    parser = argparse.ArgumentParser(description="국내 여행 추천 통합 프로그램")
    parser.add_argument("date", help="여행 날짜 (YYYY-MM-DD)")
    args = parser.parse_args()

    load_dotenv()
    ensure_results_dir()

    try:
        travel_date = validate_date(args.date)
    except ValueError as e:
        print(f"[오류] {e}")
        return

    print("[시작] 🔎 국내 여행 추천 프로그램 실행")
    print(f"- 여행 날짜: {travel_date}")
    print()

    all_errors = []

    # -------------------------
    # Step 1: 여행지 추천
    # -------------------------
    print("[1/3] 📑 여행지 추천 생성 중...")
    step1_errors = []
    recommendation = get_travel_recommendation(travel_date, step1_errors)

    step1_data = {
        "request_date": travel_date,
        "recommendation": recommendation,
        "errors": step1_errors
    }
    step1_path = RESULTS_DIR / f"{travel_date}_step1_recommendation.json"
    save_json(step1_path, step1_data)
    #print(f"[완료] 추천 결과 저장: {step1_path}")
    print(f"[완료] 추천 여행지: {step1_path}")
    print()

    all_errors.extend(step1_errors)

    # -------------------------
    # Step 2: 맛집 검색
    # -------------------------
    print("[2/3] 🍴 맛집 검색 중...")
    step2_errors = []
    city = recommendation.get("recommended_city", "")

    if city:
        restaurants = search_kakao_restaurants(city, step2_errors, size=5)
    else:
        restaurants = []
        step2_errors.append("추천 도시가 없어 맛집 검색을 건너뛰었습니다.")

    step2_data = {
        "request_date": travel_date,
        "recommended_city": city,
        "restaurants": restaurants,
        "errors": step2_errors
    }
    step2_path = RESULTS_DIR / f"{travel_date}_step2_restaurants.json"
    save_json(step2_path, step2_data)
    print(f"[완료] 맛집 결과 저장: {step2_path}")
    print()

    all_errors.extend(step2_errors)

    # -------------------------
    # Step 3: Markdown 리포트
    # -------------------------
    print("[3/3] 📒 Markdown 리포트 생성 중...")
    final_errors = dedupe_errors(all_errors)

    report_md = build_markdown_report(
        travel_date=travel_date,
        recommendation=recommendation,
        restaurants=restaurants,
        errors=final_errors
    )

    report_path = RESULTS_DIR / f"{travel_date}_travel_report.md"
    save_text(report_path, report_md)
    print(f"[완료] 리포트 저장: {report_path}")
    print()

    # -------------------------
    # 요약
    # -------------------------
    print("[요약]")
    print(f"- 추천 도시: {city or '없음'}")
    print(f"- 맛집 수: {len(restaurants)}건")
    print(f"- 오류 수: {len(final_errors)}건")

    if final_errors:
        print()
        print("[오류/경고]")
        for err in final_errors:
            print(f"- {err}")

    print()
    print("[완료] 여행 추천 리포트 생성이 완료되었습니다.")


if __name__ == "__main__":
    main()
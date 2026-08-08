
import os
import json
import argparse
from pathlib import Path

import requests
from dotenv import load_dotenv


def parse_args():
    parser = argparse.ArgumentParser(
        description="도시 이름을 입력받아 Kakao Local API로 맛집을 검색합니다."
    )
    parser.add_argument(
        "-city",
        required=True,
        help='추천 도시명 (예: "전주", "제주", "강릉")'
    )
    return parser.parse_args()


def get_env_value(key: str) -> str:
    value = os.getenv(key)
    if not value:
        print(f"[오류] 환경변수 {key} 가 설정되지 않았습니다.")
        print("설정 예시:")
        print('  macOS/Linux: export KAKAO_REST_API_KEY="YOUR_KEY"')
        print('  Windows PowerShell: $env:KAKAO_REST_API_KEY="YOUR_KEY"')
        raise SystemExit(1)
    return value


def search_kakao_restaurants(city: str, api_key: str, errors: list, size: int = 5) -> list:
    """
    Kakao Local API로 특정 도시의 맛집 검색
    실패 시 [] 반환, errors에 메시지 누적
    """
    url = "https://dapi.kakao.com/v2/local/search/keyword.json"
    headers = {
        "Authorization": f"KakaoAK {api_key.strip()}"
    }

    # "전주 맛집", "제주 맛집" 식으로 검색
    query = f"{city} 맛집"

    params = {
        "query": query,
        "size": size,
        "sort": "accuracy",
        # FD6 = 음식점
        "category_group_code": "FD6"
    }

    try:
        print(f"[로그] Kakao Local API 요청 중... query={query}")
        response = requests.get(url, headers=headers, params=params, timeout=15)        
        response.raise_for_status()

        data = response.json()
        documents = data.get("documents", [])

        restaurants = []
        for doc in documents:
            item = {
                "name": doc.get("place_name", ""),
                "address": doc.get("road_address_name") or doc.get("address_name", ""),
                "category": doc.get("category_name", ""),
                "url": doc.get("place_url", ""),
                "x": float(doc["x"]) if doc.get("x") else None,
                "y": float(doc["y"]) if doc.get("y") else None
            }
            restaurants.append(item)

        print(f"[로그] 맛집 검색 완료: {len(restaurants)}건")
        return restaurants

    except requests.exceptions.RequestException as e:
        error_msg = f"지도 API 요청 실패: {str(e)}"
        print(f"[경고] {error_msg}")
        errors.append(error_msg)
        return []

    except (ValueError, KeyError, TypeError) as e:
        error_msg = f"지도 API 응답 파싱 실패: {str(e)}"
        print(f"[경고] {error_msg}")
        errors.append(error_msg)
        return []


def save_step2_result(city: str, restaurants: list, errors: list):
    results_dir = Path("results")
    results_dir.mkdir(exist_ok=True)

    safe_city = city.replace(" ", "_")
    output_path = results_dir / f"{safe_city}_step2_restaurants.json"

    data = {
        "recommended_city": city,
        "restaurants": restaurants,
        "errors": errors
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"[로그] 결과 JSON 저장 완료: {output_path}")


def main():
    load_dotenv()
    args = parse_args()

    city = args.city
    api_key = get_env_value("KAKAO_REST_API_KEY")
    errors = []

    restaurants = search_kakao_restaurants(
        city=city,
        api_key=api_key,
        errors=errors,
        size=5
    )

    print("\n[맛집 검색 결과]")
    print(json.dumps(restaurants, ensure_ascii=False, indent=2))

    save_step2_result(city, restaurants, errors)
    


if __name__ == "__main__":
    main()
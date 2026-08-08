# A1_2


# 프로그램 개요



# 실행 방법

### 1단계 : LLM API 연동 

Step1에서 이해해야 할 핵심
    1) 날짜 인자 받기 
    2) .env에서 API 키 읽기 
    3) LLM에 보낼 프롬프트 만들기          
        build_messages()        시스템 프롬프트 설정         
    4) OpenAI API 호출하기
        request_openai_chat()   OpenAI Chat Completions API 호출 , 반환값: 모델이 생성한 텍스트    
    5) 응답을 JSON 형태로 정리하기
        get_travel_recommendation() LLM 호출 + JSON 파싱, 파싱 실패 시 최대 1회 재시도
             LLM 호출 함수
                [로그] LLM 추천 요청 중... (시도 1/2)
                [로그] LLM 응답 수신 완료
             내부에 재시도 로직이 있을 가능성이 높습니다.    
             
             parse_llm_json()        LLM 응답 텍스트를 JSON으로 파싱하고,최소 스키마를 검사  
                response.choices[0].message.content 구조
                result = json.loads(text)     LLM이 준 텍스트를 가져옴, JSON 문자열이면 Python 객체로 변환        
                
            
    6) 파일로 저장하기
        save_step1_result()
            path = f"results/{date}_step1_recommendation.json"
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)  
                
Step1 전체 흐름을 아주 쉽게 그리면      즉, 입력 → 요청 → 응답 → 저장 구조입니다.  
    def main():
        # 1. 실행 인자 받기
        args = parse_args()
        date = args.date
    
        # 2. API 키 준비
        load_env()
    
        # 3. LLM에 추천 요청
        result = request_llm_recommendation(date)
    
        # 4. 결과 저장
        save_result(result, date)

추천 읽기 순서
main()
parse_args()
request_llm_recommendation() 같은 핵심 호출 함수
build_prompt()
save_result()


### 2단계 : 지도/장소 API 연동 
recommended_city
  → Kakao Local API 호출
    → 맛집 목록 정리
      → results/ 에 JSON 저장

이번 단계에서 사용할 API
    이번 예시는 Kakao Local API 기준으로 설명하겠습니다.
    이유:
    국내 장소 검색에 잘 맞음
    JSON 응답이 깔끔함
    음식점 검색이 비교적 쉬움
1. 필요한 환경변수 
    KAKAO_REST_API_KEY=YOUR_KEY (.env 에 저장)
   https://developers.kakao.com/ 접속후 REST_API 발급


* 코드 설명
(1) 왜 -city를 입력으로 받았나?
    parser.add_argument("-city", required=True, ...)

    나중에 전체 통합할 때는 이렇게 바뀝니다:
        city = recommendation["recommended_city"]
        restaurants = search_kakao_restaurants(city, api_key, errors)

(2) Kakao API 인증 헤더
       headers = {
        "Authorization": f"KakaoAK {api_key}"  <-- Kakao Local API는 보통 이런 형식의 헤더를 요구합니다. 
       }
(3) 검색어 만들기 
    query = f"{city} 맛집" 
        왜 이렇게 하냐면,
        그냥 "강릉"만 검색하면 음식점이 아닌 장소가 섞일 수 있기 때문입니다.
        
        그래서 "도시명 + 맛집" 형태로 검색하면
        맛집 관련 결과를 더 쉽게 얻을 수 있습니다.
(4) 음식점 카테고리 제한
    "category_group_code": "FD6"
    Kakao Local의 카테고리 그룹 코드에서:    
    FD6 = 음식점
    즉, 검색 결과를 음식점 위주로 제한하려는 목적입니다.
    
(5) 응답 JSON에서 필요한 필드만 추출
    item = {
        "name": doc.get("place_name", ""),
        "address": doc.get("road_address_name") or doc.get("address_name", ""),
        "category": doc.get("category_name", ""),
        "url": doc.get("place_url", ""),
        "x": float(doc["x"]) if doc.get("x") else None,
        "y": float(doc["y"]) if doc.get("y") else None
    }
    
   각 필드 의미
    place_name → 가게 이름
    road_address_name / address_name → 주소
    category_name → 카테고리
    place_url → 카카오맵 URL
    x, y → 좌표
   
(6) 주소를 road_address_name or address_name으로 처리한 이유
    doc.get("road_address_name") or doc.get("address_name", "")

    Kakao 응답에는 도로명 주소가 비어 있는 경우가 있습니다.    
    그래서 우선순위를 이렇게 둡니다:
    도로명 주소가 있으면 사용
    없으면 지번 주소 사용
    둘 다 없으면 빈 문자열

(7) 좌표를 float로 바꾸는 이유 
    "x": float(doc["x"]) if doc.get("x") else None,
    "y": float(doc["y"]) if doc.get("y") else None

(8) 지도 API 실패 시에도 [] 반환
    except requests.exceptions.RequestException as e:
        ...
        return []

    요구사항:
    지도/장소 API 실패 시에도 리포트 생성은 진행
    맛집은 “데이터 없음” 처리
    그래서 이 함수는 실패해도 프로그램을 바로 죽이지 않고
    빈 리스트 [] 를 돌려줍니다.

(9) errors 리스트에 오류 누적
    errors.append(error_msg)
    콘솔에만 오류를 찍고 끝내지 않음
    나중에 최종 결과 JSON과 최종 보고서에 반영 가능
        예:
        {
          "errors": [
            "지도 API 요청 실패: 403 Client Error ..."
          ]
        }
(10) 결과 저장 구조
    data = {
        "recommended_city": city,
        "restaurants": restaurants,
        "errors": errors
    }
    이 구조가 좋은 이유는
    나중에 전체 통합 JSON과 비슷한 형태로 발전시키기 쉽기 때문입니다.



# API 키 설정 방법


# 결과물 확인 방법




CLI는 **Command Line Interface(명령 줄 인터페이스)**의 약자  
    CLI vs GUI (비교해보면 쉬워요)
    GUI (Graphical User Interface): 우리가 흔히 쓰는 윈도우 창, 버튼, 이미지, 메뉴가 있는 프로그램입니다. (예: 크롬 브라우저, 카카오톡 PC 버전)
    CLI (Command Line Interface): 오직 텍스트로만 소통합니다. 사용자가 명령어를 타이핑하면, 프로그램이 텍스트로 답을 줍니다. (예: 명령 프롬프트(CMD), 터미널)
    
    핵심 로직에 집중 가능: 디자인이나 버튼 배치를 고민할 필요 없이, "LLM 연결"과 "지도 API 활용"이라는 프로그램의 진짜 기능(로직)을 만드는 데 집중할 수 있습니다.
    개발 속도가 빠름: 화면을 그리는 코드를 짤 필요가 없어 훨씬 빠르게 결과를 확인할 수 있습니다.
    서버 환경에 적합: 나중에 이 프로그램을 서버에 올릴 때, 서버는 보통 화면이 없는 CLI 환경인 경우가 많습니다.

argparse는 파이썬 프로그램에 **'인자(Argument)'**를 전달할 수 있게 도와주는 도구
1. input() vs argparse 차이점
    input() (대화형):
       $ python travel.py
       > 여행 날짜를 입력하세요: 10월  (실행 후에 입력) 
    argparse (명령행 인자 방식):
       $ python travel.py --date 10월  (실행할 때 미리 입력)

2. 왜 argparse를 쓸까요? (장점)
    자동화에 유리함: 다른 프로그램이 내 프로그램을 실행시킬 때, 일일이 타이핑할 필요 없이 한 줄의 명령어로 제어할 수 있습니다.
    도움말 자동 생성: 터미널에 python travel.py --help라고 치면, 내가 설정한 help 문구들이 예쁘게 정리되어 출력됩니다. (직접 해보시면 신기할 거예요!)
    기본값 설정 가능: 사용자가 날짜를 입력 안 했을 때 기본적으로 '오늘'로 설정하는 등의 처리가 매우 쉽습니다.



1) requests 설치
py -m pip install requests
설치가 잘 되었는지 확인
py -m pip show requests

2) from dotenv import load_dotenv 오류 ->  dotenv 설치 
  Python 환경에 dotenv 모듈이 없어서 실패, 설치 명령어 이름이 dotenv가 아니라 python-dotenv
   py -m pip install python-dotenv


3) 설치 파일명 정리 : requirements.txt
    py -m pip install -r requirements.txt

4)  .env 파일 방식
    프로젝트별로 관리하기 좋음
    코드 수정 없이 사용 가능
    다른 API 키 추가도 쉬움



LLM API 연결-1차 JSON  

화면 내용 분석
1. 실행 명령어
    py step1_llm_recommend.py -date 2026-12-31
    
       
2. 로그
    [로그] LLM 추천 요청 중... (시도 1/2)
    [로그] LLM 응답 수신 완료
   
    의미: 프로그램이 OpenAI에 추천 요청을 보냈고
    첫 번째 시도에서 바로 응답을 받았다는 뜻입니다.
   
4. 추천 결과
    <img width="701" height="293" alt="image" src="https://github.com/user-attachments/assets/29793b57-d8fa-4267-9b15-a4ebb6859d03" /> 
    LLM이 요청 형식에 맞게 결과를 잘 만들어냈습니다.

   마지막 줄 분석
   [로그] 결과 JSON 저장 완료: results\2026-12-31_step1_recommendation.json




1) .gitignore 파일 만들기
    ni .gitignore

    .env              : API 키 보호
    __pycache__/
    *.pyc             : 파이썬 캐시 파일 제외
    results/          : 결과 JSON이 자동 생성물이라면 제외 가능

   

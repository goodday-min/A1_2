---
# 🚗 API 활용 국내 여행지 추천 프로그램

OpenAI LLM(LLM API)과 Kakao Local API(지도 API)를 활용하여 입력한 날짜에 맞는 국내 여행지를 추천하고, 
해당 지역의 맛집 정보를 검색한 뒤, 최종 Markdown 여행 리포트를 생성하는 CLI 프로그램입니다.  

---


## 📌 프로젝트 개요

이 프로그램은 사용자가 여행 날짜를 입력하면 다음 과정을 자동으로 수행합니다.

1. **OpenAI LLM**을 사용해 날짜에 어울리는 국내 여행지 추천   
2. 추천된 도시를 기준으로 **Kakao Local API**를 사용해 맛집 검색   
3. 수집한 추천 결과와 맛집 정보를 바탕으로 **최종 Markdown 리포트 생성**   
4. 각 단계의 결과를 `results/` 폴더에 파일로 저장  
   
✅ 이 프로그램은 **LLM 출력 결과를 JSON 구조로 받아 다음 단계의 입력값으로 연결하는 흐름**을 구현한 것이 특징입니다.

---

## 📌 주요 기능

   #### 1) 여행지 추천   
   - 입력 날짜를 바탕으로 국내 여행지 1곳 추천
   - 계절감, 날씨 분위기, 어울리는 활동을 함께 생성
   - OpenAI 응답은 JSON 형식으로 받도록 구성
   - **JSON 파싱 실패 시 1회 재시도**
   
   #### 2) 맛집 검색
   - 추천된 도시 이름으로 Kakao Local API 검색
   - 최대 5개의 맛집 정보 수집
   - 장소명, 주소, 전화번호, 카테고리, URL, 좌표(x, y) 저장
   
   #### 3) 최종 리포트 생성
   - 추천 결과 + 맛집 검색 결과를 이용해 Markdown 리포트 생성
   - LLM 리포트 생성 실패 시 fallback 방식으로 기본 리포트 생성 가능
   
   #### 4) 오류 처리
   - API 키 누락 시 프로그램 즉시 종료
   - 날짜 형식 오류 시 안내 메시지 출력
   - OpenAI/Kakao API 호출 오류를 기록하여 최종 리포트에 반영
  
---

## 📌 사용 기술

| 사용 도구 | 사용 방법 |
| --- | --- |
| Python 3.10+ | 프로그램 전체 로직 구현에 사용한 언어 |
| [OpenAI Python SDK] | 여행지 추천과 최종 리포트 생성을 위한 LLM API 호출에 사용 |
| Kakao Local API] | 추천된 지역의 맛집 검색을 위한 장소 검색 API |
| Requests | Python에서 HTTP 요청을 보내기 위한 라이브러리로, Kakao Local API에 GET 요청을 보내고 응답을 받는 데 사용 |
| python-dotenv | .env 파일에 저장된 환경변수를 불러오는 라이브러리로, API 키를 코드에 직접 작성하지 않고 안전하게 관리하기 위해 사용 |

      OpenAI Python SDK](https://pypi.org/project/openai/)  
      Kakao Local API](https://developers.kakao.com/docs/latest/ko/local/dev-guide)  
---

## 📌 프로젝트 구조

A1_2.  
├── travel_pipeline.py   
├── .env  
├── .gitignore  
├── requirements.txt  
├── README.md  
└── results/  

      실행 후 results/ 폴더에 아래 파일들이 생성됩니다.
      YYYY-MM-DD_step1_recommendation.json  
      YYYY-MM-DD_step2_restaurants.json  
      YYYY-MM-DD_travel_report.md  

---

## 📌 개발 환경 준비 

 - Python 3.10 이상 권장
 - 필요한 라이브러리 설치: pip install -r requirements.txt

 1. 로컬 저장소 생성
    
      cd 내프로젝트폴더    # 폴더로 이동
      git init             # Git 저장소 시작 (.git 폴더 생성)

 2. GitHub 저장소 연결 : 로컬 ↔ GitHub 연결 다리 만들기

      git remote add origin https://github.com/내아이디/저장소이름.git

 3. 파일 저장 (add → commit)

      git add .                        # 변경된 모든 파일 스테이징
      git commit -m "첫 번째 커밋"     # 로컬에 저장 (스냅샷 찍기)
      
 4. GitHub와 동기화

      **GitHub → 내 컴퓨터 (받아오기)**
      git pull origin main
      
      **내 컴퓨터 → GitHub (올리기)**
      git push origin main

 ✅ 전체 흐름 한눈에 보기

      [내 컴퓨터]                    [GitHub]
         │                              │
         │  git add .                   │
         │  git commit -m "메시지"      │
         │                              │
         │  ──── git push ────────────► │
         │  ◄─── git pull ──────────── │

---

## 📌 API 키 설정 방법

- 프로젝트 루트 경로에 .env 파일을 생성하고 아래와 같이 작성합니다.

       OPENAI_API_KEY=your_openai_api_key  
       KAKAO_REST_API_KEY=your_kakao_rest_api_key  

- 각 키의 용도
  
       OPENAI_API_KEY : 여행지 추천 및 최종 리포트 생성용  
       KAKAO_REST_API_KEY : 지역 맛집 검색용  
  
**✅ 환경변수 관리 이유**
     
       API 키를 소스코드에 직접 작성하면 GitHub 업로드, 화면 공유, 코드 제출 과정에서 쉽게 유출될 수 있습니다.
       따라서 환경변수 또는 .env 파일로 분리하여 관리하는 것이 안전합니다.  
    
🔹 보안: API 키를 코드에 직접 작성하면 깃허브 등 공개 저장소에 유출될 위험이 있음  
🔹 유연성: 개발/운영 환경마다 다른 키를 쉽게 적용 가능  
🔹 재사용성: 여러 프로젝트에서 동일한 키를 공유할 때 편리  

🔹 원칙: .env 파일 → dotenv 라이브러리 → os.getenv()로 불러오기   

*API 키는 매우 중요한 민감정보이므로 아래 사항을 반드시 지켜야 합니다.*

🔹주의사항
   - API 키를 코드에 직접 작성하지 않는다.
   - .env 파일은 GitHub에 업로드하지 않는다.
   - .gitignore에 .env를 반드시 포함한다.
   - 화면 캡처, 발표 자료, 제출 문서에 키가 보이지 않도록 주의한다.
   - 키가 노출되었다면 즉시 폐기하고 새 키를 발급받는다. 
   
      예시 .gitignore
      .env
      venv/
      __pycache__/
      results/

---

## 📌 실행 방법  

    python travel_pipeline.py -date 2026-12-31

🔹입력: YYYY-MM-DD 형식의 여행 날짜 (필수)  
🔹잘못된 날짜를 입력하면 에러 메시지와 함께 사용법이 출력됩니다.    

| 정상 실행방법 | 잘못된 실행방법 | 
| --- | --- |   
| <img width="1111" height="462" alt="image" src="https://github.com/user-attachments/assets/44f5aa86-90ca-48b9-821e-c0141a613439" /> | <img width="1076" height="231" alt="image" src="https://github.com/user-attachments/assets/9be72c80-9fc1-41e4-83e4-10a87cfce814" /> |  

---

## 📌 결과물 확인 방법 및 결과물 구조

*프로그램 실행이 완료되면 results/ 폴더에서 결과물을 확인할 수 있습니다.*  


| 결과물 | 결과물 파일명 | 결과물 파일 내용 | 
| --- | --- | --- |     
| 추천결과 파일 | results/<br>YYYY-MM-DD_step1_recommendation.json | <img width="600" alt="image" src="https://github.com/user-attachments/assets/c50fe97b-4234-4b41-89bd-e31bcdf8a485" /> |   
| 맛집검색결과 파일 | results/<br>YYYY-MM-DD_step2_restaurants.json | <img width="600" alt="image" src="https://github.com/user-attachments/assets/2a843cbd-cdfb-48ed-be1a-5c7f2676bcd3" /> |     
| 최종결과 파일 | results/<br>YYYY-MM-DD_travel_report.md | <img width="600" alt="image" src="https://github.com/user-attachments/assets/a246bb97-64dc-4b25-b28c-dc25eaef4021" /> |     

---

## 📌  실행 흐름 설명

*이 프로그램은 다음과 같은 데이터 흐름으로 동작합니다.*

**🔹 LLM 여행지 추천**  

    사용자가 입력한 날짜를 OpenAI API에 전달하면, LLM이 아래와 같은 구조화된 JSON 결과를 반환합니다.
    
    {
      "recommended_city": "강릉",
      "weather": "초여름 바다를 즐기기 좋은 시기입니다.",
      "events": ["해변 산책", "카페 투어", "로컬 음식 탐방"],
      "reason": "계절과 분위기에 잘 어울리는 여행지입니다."
    }

**🔹 JSON 결과를 다음 API 입력으로 사용**

    위 JSON에서 recommended_city 값을 꺼내어,
    Kakao Local API 검색어인 "강릉 맛집" 형태로 전달합니다.
    
    즉,
    
    LLM 출력(JSON) → recommended_city
    다음 단계 입력값 → Kakao 검색 쿼리
    이 과정을 통해 LLM의 결과를 구조화하여 외부 API의 입력으로 연결하는 방식을 구현했습니다.

 **🔹 최종 리포트 생성**  

    추천 정보와 맛집 정보를 모아서 Markdown 리포트를 생성하고 저장합니다.
---

## 📌 REST API와 HTTP 메서드 설명

   🔹 REST API 요청/응답 구조  

      REST API는 클라이언트가 서버에 요청(Request)을 보내고, 서버가 결과를 응답(Response)으로 반환하는 방식으로 동작합니다.
  
   🔹 REST API 구성 요소
     
      URL(엔드포인트) : 요청 대상 주소  
      HTTP 메서드 : 어떤 작업을 할지 지정  
      헤더(Header) : 인증 정보(API 키 등) 전달  
      파라미터(Query / Body) : 검색 조건이나 입력 데이터 전달  
      응답(Response) : 보통 JSON 형식으로 결과 반환  

    예를 들어 Kakao Local API 호출 시에는:       
      - URL: 장소 검색 API 주소
      - 메서드: GET
      - 헤더: Authorization: KakaoAK ...
      - 쿼리 파라미터: "도시명 맛집"
      - 응답: 검색된 장소 목록(JSON)

   🔹 HTTP 메서드 : GET / POST  


| GET | POST |
| --- | --- |
| 서버에서 데이터를 조회할 때 사용 | 서버에 새로운 데이터를 전달하거나 생성 요청할 때 사용 |  
| 주로 검색, 조회 기능에 사용 | 요청 본문(body)에 데이터를 담는 경우가 많음 |  
| 파라미터가 URL에 포함되는 경우가 많음 | 이 프로젝트에서는 맛집 검색이므로 주로 GET 방식이 사용됩니다. |    

---

## 📌 대표 오류와 대응 원칙

  외부 API 호출 시 자주 발생할 수 있는 오류와 대응 방식은 아래와 같습니다.

| 오류 종류 | 인증 오류 | 쿼터 초과 오류 | 네트워크 오류 | 파싱 오류 |
| --- | --- | --- |--- | --- |
| 예 | -API 키 누락<br>-잘못된 키 입력<br>-권한 미설정<br> | -일일 호출량 초과<br>-분당 요청 제한 초과 | -인터넷 연결 문제<br>-타임아웃<br>-서버 응답 지연 | -LLM이 예상 형식이 아닌 응답 반환<br>-JSON 디코딩 실패 |
| 오류 대응 | -.env에 키가 정확히 설정되었는지 확인<br>-API 서비스 활성화 여부 확인<br>-인증 실패 메시지를 사용자에게 출력 | -재실행 전에 사용량 확인<br>-과도한 반복 호출 방지<br>-필요 시 요청 수 줄이기 | -timeout 설정<br>-예외 처리 후 오류 기록<br>-빈 결과라도 프로그램이 중단되지 않도록 설계 | -JSON 형식만 반환하도록 프롬프트를 강하게 제한<br>-파싱 실패 시 1회 재시도<br>-최종 실패 시 오류 로그 기록 |


   
| 인증 오류 | 스크린샷 |
| --- | --- |
|     API 키 누락  | <img width="600" alt="image" src="https://github.com/user-attachments/assets/00c8f2a2-da28-49ad-85cd-52d51d4ea5f3" /> |


**✅ 이 프로그램은 아래 상황에 대비해 예외 처리를 포함하고 있습니다.**

   🔹 API 키 누락 시 즉시 종료  
   🔹 잘못된 날짜 형식 입력 시 오류 메시지 출력  
   🔹 OpenAI JSON 파싱 실패 시 재시도  
   🔹 Kakao API 요청 실패 시 오류 기록 후 빈 결과 처리  
   🔹 최종 리포트 생성 실패 시 fallback Markdown 생성  

---
   
## 📌 결과 파일 예시

 1) 추천 결과 JSON
      
         {
           "request_date": "2025-05-20",
           "recommendation": {
             "recommended_city": "강릉",
             "weather": "초여름 바다를 즐기기 좋은 시기입니다.",
             "events": ["해변 산책", "카페 투어", "로컬 음식 탐방"],
             "reason": "날씨와 계절 분위기를 고려했을 때 만족도가 높은 여행지입니다."
           },
           "errors": []
         }
      
 2) 맛집 검색 결과 JSON
      
         {
           "request_date": "2025-05-20",
           "recommended_city": "강릉",
           "restaurants": [
             {
               "name": "예시 맛집",
               "address": "강원특별자치도 강릉시 ...",
               "phone": "033-000-0000",
               "place_url": "https://place.map.kakao.com/...",
               "category": "음식점 > 한식",
               "x": "128.123456",
               "y": "37.123456"
             }
           ],
           "errors": []
         }

3) Markdown 리포트 예시

         # 국내 여행 추천 리포트
         
         - 여행 날짜: **2025-05-20**
         - 추천 도시: **강릉**
         
         ## 1. 추천 이유
         계절과 여행 분위기를 고려했을 때 적합한 여행지입니다.
         
         ## 2. 예상 날씨
         초여름 바다를 즐기기 좋은 시기입니다.
         
         ## 3. 추천 활동
         - 해변 산책
         - 카페 투어
         - 로컬 음식 탐방
         
         ## 4. 맛집 추천
         ### 1. 예시 맛집
         - 주소: ...
         - 전화번호: ...
         - 카테고리: ...
         - 링크: ...
         - 좌표: x=..., y=...
         
         ## 5. 오류 로그
         - 없음

---

## 📌 향후 개선 아이디어

   - 실제 날씨 API 연동
   - 지역 축제/행사 API 연동
   - 관광지 추천 추가
   - 웹 UI(Streamlit) 확장
   - 지도 시각화 기능 추가
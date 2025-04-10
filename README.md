# 청소 관리 대시보드

노션 데이터베이스에서 청소 일정을 관리하고 담당자를 배정하는 웹 애플리케이션입니다.

## 기능

- 캘린더에서 청소 일정 확인
- 미배정된 청소 일정에 담당자 신청/배정
- 주간 청소 일정 확인
- 전체 청소 일정 목록 보기

## 로컬에서 실행하기

1. 의존성 설치
```
pip install -r requirements.txt
```

2. 환경 변수 설정 (선택 사항)
```
export NOTION_TOKEN="your_notion_api_token"
export NOTION_DATABASE_ID="your_notion_database_id"
```

3. 앱 실행
```
python app.py
```

4. 브라우저에서 `http://localhost:5000` 접속

## Render에 배포하기

1. Render 계정 생성: [render.com](https://render.com)에서 가입

2. 새 Web Service 생성
   - GitHub 저장소에 코드 업로드 후 Render에서 연결
   - 또는 직접 Git 저장소 URL 입력

3. 설정:
   - Name: 원하는 서비스 이름 입력
   - Environment: Python
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn app:app`

4. 환경 변수 설정:
   - NOTION_TOKEN: 노션 API 키
   - NOTION_DATABASE_ID: 노션 데이터베이스 ID

5. 'Create Web Service' 클릭

## 노션 데이터베이스 설정

이 앱은 다음과 같은 속성을 가진 노션 데이터베이스를 필요로 합니다:

- 청소 일정 (Date 타입)
- 예약인원 (Number 타입)
- 청소 담당자 (Select 타입)
- 상태 (Status 타입) - '청소 배정 필요', '예약됨', '완료' 옵션 포함

## 라이선스

MIT 
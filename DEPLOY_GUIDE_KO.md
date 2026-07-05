# 학교 PC에서 접속할 수 있게 배포하는 방법

선생님 PC에 Python이 없고, 내 노트북을 학교에 가져갈 수 없다면 앱을 인터넷에 배포해야 합니다.
가장 쉬운 방법은 Streamlit Community Cloud에 올려서 웹 주소를 만드는 것입니다.

## 준비물

- GitHub 계정
- Streamlit Community Cloud 계정
- 이 앱 파일들

## 배포 순서

1. GitHub에 새 저장소를 만듭니다.
2. 아래 파일들을 저장소에 올립니다.
   - `app.py`
   - `requirements.txt`
   - `README.md`
   - `.streamlit/secrets.toml.example`
3. Streamlit Community Cloud에 로그인합니다.
4. `New app`을 선택합니다.
5. GitHub 저장소를 선택합니다.
6. Main file path를 아래처럼 설정합니다.

```text
app.py
```

7. 배포 전에 Secrets 설정에 아래 내용을 추가합니다.

```toml
APP_PASSWORD = "학교에서_사용할_비밀번호"
```

8. Deploy를 누릅니다.
9. 만들어진 앱 주소를 보건 선생님께 전달합니다.

## 선생님께 안내할 내용

선생님은 Python을 설치하지 않아도 됩니다.
브라우저에서 배포된 주소로 접속하고, 비밀번호를 입력하면 됩니다.

## 중요한 주의사항

- 학생 이름, 증상, 질병, 상담 내용, 개인 건강 정보는 입력하지 마세요.
- 이 앱은 재고 관리 전용입니다.
- 무료 클라우드 배포에서는 SQLite 데이터가 장기 보관에 적합하지 않을 수 있습니다.
- 내일 시연에는 괜찮지만, 실제 운영용으로 쓰려면 Google Sheets, Supabase, 학교 서버 같은 별도 저장소를 붙이는 것이 좋습니다.

## 내일 가장 현실적인 시연 방법

1. 오늘 집에서 앱을 Streamlit Community Cloud에 배포합니다.
2. 배포된 URL과 비밀번호를 메모합니다.
3. 내일 학교에서 선생님 PC 브라우저로 URL에 접속합니다.
4. 비밀번호를 입력하고 앱을 사용해봅니다.

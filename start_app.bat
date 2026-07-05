@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo 학교 보건실 재고 관리 앱을 시작합니다.
echo.

where python >nul 2>nul
if errorlevel 1 (
    echo Python을 찾을 수 없습니다.
    echo 먼저 https://www.python.org/downloads/ 에서 Python을 설치하세요.
    echo 설치할 때 "Add Python to PATH" 옵션을 체크하면 좋습니다.
    pause
    exit /b 1
)

echo 필요한 패키지를 확인하고 설치합니다...
python -m pip install -r requirements.txt
if errorlevel 1 (
    echo 패키지 설치 중 문제가 발생했습니다.
    pause
    exit /b 1
)

echo.
echo 앱을 실행합니다.
echo 브라우저에서 http://localhost:8501 로 접속하세요.
echo 같은 Wi-Fi의 휴대폰에서는 이 PC의 IP 주소 뒤에 :8501을 붙여 접속합니다.
echo 예: http://192.168.0.10:8501
echo.

python -m streamlit run app.py --server.address 0.0.0.0 --server.port 8501
pause

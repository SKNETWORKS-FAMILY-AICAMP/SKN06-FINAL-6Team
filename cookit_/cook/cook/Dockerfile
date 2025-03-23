# Django 기반 이미지
FROM python:3.12

# 작업 디렉토리 설정
WORKDIR /app

# 종속성 복사 및 설치
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# 프로젝트 코드 복사
COPY . /app

# Django 실행 (runserver 사용)
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
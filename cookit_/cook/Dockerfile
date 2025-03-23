FROM python:3.12

WORKDIR /app

COPY . /app

RUN apt-get update && apt-get install -y ffmpeg

RUN pip install --no-cache-dir -r requirements.txt

CMD ["gunicorn", "--chdir", "cook", "cook.wsgi:application", "--bind", "0.0.0.0:8000"]
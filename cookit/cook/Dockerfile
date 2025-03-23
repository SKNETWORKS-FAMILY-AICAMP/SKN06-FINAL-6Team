FROM python:3.12

WORKDIR /app

COPY . /app

COPY ./requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

EXPOSE 8000

CMD ["uvicorn", "cook.asgi:application", "--host", "0.0.0.0", "--port", "8000"]
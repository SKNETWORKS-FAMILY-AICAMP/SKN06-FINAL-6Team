FROM python:3.12

WORKDIR /app

COPY .  /app
RUN apt-get update && apt-get install -y libgl1-mesa-glx

COPY ./requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

EXPOSE 9000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "9000"]
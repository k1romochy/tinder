FROM python:3.9

WORKDIR /likes_service

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN useradd -m appuser
USER appuser

CMD ["python", "-m", "likes_service.app.main"] 
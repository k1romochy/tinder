FROM python:3.11

WORKDIR /main_service

RUN apt-get update && apt-get install -y postgresql-client

COPY requirements.txt .
RUN pip3 install --upgrade setuptools
RUN pip3 install -r requirements.txt

ENV PYTHONPATH=/

COPY . .

CMD ["uvicorn", "main_service.app.run:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
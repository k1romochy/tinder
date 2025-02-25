FROM python:3.11

WORKDIR /tinder

RUN apt-get update && apt-get install -y postgresql-client

COPY requirements.txt requirements.txt
RUN pip3 install --upgrade setuptools
RUN pip3 install -r requirements.txt

ENV PYTHONPATH=/tinder

COPY . .

RUN chmod -R 755 /tinder

CMD ["uvicorn", "app.run:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
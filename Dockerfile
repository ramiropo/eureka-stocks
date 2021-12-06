from python:3.9


COPY . /app

WORKDIR /app

RUN pip install -r requirements.txt

EXPOSE 5000/tcp

CMD python app.py
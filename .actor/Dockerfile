FROM apify/actor-python:3.13

WORKDIR /usr/src/app

COPY requirements.txt /usr/src/app/
COPY src /usr/src/app/src

RUN mkdir -p logs \
  && pip install --no-cache-dir -r requirements.txt \
  && python3 -m compileall -q .

ENV DISPLAY=:99

CMD ["python3", "-m", "src"]

FROM apify/actor-python:3.13

WORKDIR /usr/src/app

COPY src requirements.txt /usr/src/app/

RUN mkdir -p logs \
  && pip install --no-cache-dir -r requirements.txt \
  && python3 -m compileall -q . \
  && rm -rf /var/lib/apt/lists/*

ENV DISPLAY=:99

CMD ["python3", "-m", "src"]

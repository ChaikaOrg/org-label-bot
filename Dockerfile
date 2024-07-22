FROM python:3.10-slim

WORKDIR /action

COPY requirements.txt /action/requirements.txt

RUN pip install -r requirements.txt


COPY main.py /action/main.py

# Execute the script when the docker container starts up
ENTRYPOINT ["python3", "/action/main.py"]

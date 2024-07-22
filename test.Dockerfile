FROM python:3.8-slim

WORKDIR /action

# Copy the script into the docker container
COPY script.py /script.py

# Execute the script when the docker container starts up
ENTRYPOINT ["python", "/script.py"]

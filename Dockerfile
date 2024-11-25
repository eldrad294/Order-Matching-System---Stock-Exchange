FROM python:latest
WORKDIR /src
COPY ./requirements.txt /requirements.txt
RUN pip install --no-cache-dir --upgrade -r /requirements.txt
COPY src /src
EXPOSE 80
CMD ["uvicorn", "controllers:app", "--host", "0.0.0.0", "--port", "80"]

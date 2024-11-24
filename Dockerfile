FROM python:latest
WORKDIR /src
COPY ./requirements.txt /requirements.txt
RUN pip install --no-cache-dir --upgrade -r /requirements.txt
COPY src/app /src/app
EXPOSE 80
CMD ["uvicorn", "app.controllers:app", "--host", "0.0.0.0", "--port", "80"]

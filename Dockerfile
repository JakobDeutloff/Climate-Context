FROM python:3.10.15
ADD . /app
WORKDIR /app
RUN pip install -r requirements.txt
CMD ["python", "./main.py"]

FROM python:3.6
WORKDIR /app
ADD . /app
COPY requirements.txt /
RUN pip install -r requirements.txt
EXPOSE 9996
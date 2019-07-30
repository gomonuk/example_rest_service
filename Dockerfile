FROM python:3.6
WORKDIR /
ADD . /
COPY requirements.txt /
RUN pip install -r requirements.txt
EXPOSE 9996
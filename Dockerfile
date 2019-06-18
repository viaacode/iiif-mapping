FROM python:3.6
ENV PYTHONUNBUFFERED 1

RUN mkdir /web
WORKDIR /web
COPY requirements.pip /web
RUN pip install --upgrade pip
RUN pip install -r /web/requirements.pip

COPY . /web
EXPOSE 8080
CMD ["/web/start-webserver.sh"]

FROM python:3.6
ENV PYTHONUNBUFFERED 1

RUN mkdir /web
WORKDIR /web
COPY requirements.pip /web
RUN pip install --upgrade pip
RUN pip install -r /web/requirements.pip
RUN test "${MAPPINGS_DOWNLOAD_URL}" && wget "${MAPPINGS_DOWNLOAD_URL}" -O /web/mappings.csv
COPY . /web
EXPOSE 8080
CMD ["/web/start-webserver.sh"]

FROM python:3.6
ARG MAPPINGS_DOWNLOAD_URL
RUN mkdir /web
WORKDIR /web
COPY requirements.txt /web
RUN apt-get update && apt-get install -y git
RUN pip install --upgrade pip
RUN pip install -r /web/requirements.txt
RUN if [ "${MAPPINGS_DOWNLOAD_URL}" ]; then echo "Downloading mappings.csv"; wget "${MAPPINGS_DOWNLOAD_URL}" -O /web/mappings.csv; fi
COPY . /web
EXPOSE 8080
CMD ["/web/start-webserver.sh"]

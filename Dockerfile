FROM python:3-alpine

RUN mkdir /app
ADD requirements.txt exporter.py /app/
RUN pip3 install -r /app/requirements.txt

USER nobody
EXPOSE 8999
CMD ["/app/exporter.py"]

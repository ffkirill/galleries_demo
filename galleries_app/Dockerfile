FROM python:3.6-alpine
ADD . /app
WORKDIR /app
RUN apk add build-base python-dev py-pip jpeg-dev zlib-dev postgresql-dev musl-dev
ENV LIBRARY_PATH=/lib:/usr/lib DJANGO_SETTINGS_MODULE=galleries.settings_docker
RUN pip install -r requirements.txt
CMD python manage.py create_schema; python manage.py runserver 0.0.0.0:8000

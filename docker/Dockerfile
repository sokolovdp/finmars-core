FROM ubuntu:16.04

# RUN apt-get update
# RUN apt-get install -y apt-utils
# RUN apt-get install -y apt-utils telnet iputils-ping iputils-tracepath

RUN apt-get update && \
    apt-get install -y apt-utils && \
    apt-get upgrade -y && \
    apt-get install -y \
        openssl libssl-dev \
        python3-dev python3-pip python3-venv python3-setuptools python3-wheel \
        libpq-dev libgdal-dev libgeos-dev libproj-dev \
        libtiff5-dev libjpeg-turbo8-dev libzip-dev zlib1g-dev libffi-dev git \
        libgeoip-dev geoip-bin geoip-database \
        uwsgi uwsgi-plugin-python3 uwsgi-plugin-asyncio-python3 \
        supervisor && \
    rm -rf /var/lib/apt/lists/*


ADD requirements.txt /var/app/
RUN pyvenv-3.5 /var/app-venv
RUN /var/app-venv/bin/pip install -U pip wheel && /var/app-venv/bin/pip install -r /var/app/requirements.txt

ADD . /var/app/

RUN mkdir -p /var/log/finmars/

RUN mkdir -p /var/app-data/
RUN mkdir -p /var/app-data/media/
RUN mkdir -p /var/app-data/import/configs/
RUN mkdir -p /var/app-data/import/files/
RUN chmod 777 /var/app-data/

#COPY docker/supervisor-celery.conf /etc/supervisor/conf.d/celeryd.conf
#COPY docker/supervisor-celerybeat.conf /etc/supervisor/conf.d/celerybeat.conf
#COPY docker/supervisor-devserver.conf /etc/supervisor/conf.d/devserver.conf

COPY docker/uwsgi-celery.ini /etc/uwsgi/finmars-vassals/finmars-celery.ini
COPY docker/uwsgi-celerybeat.ini /etc/uwsgi/finmars-vassals/finmars-celerybeat.ini
COPY docker/uwsgi-www.ini /etc/uwsgi/finmars-vassals/finmars-www.ini
COPY docker/uwsgi-emperor.ini /etc/uwsgi/apps-enabled/finmars.ini

RUN chmod +x /var/app/docker/finmars-run.sh

# ENV        UWSGI_NUM_PROCESSES    1
# ENV        UWSGI_NUM_THREADS      1
# ENV        UWSGI_UID              uwsgi
# ENV        UWSGI_GID              uwsgi
# ENV        UWSGI_LOG_FILE         /var/log/uwsgi/uwsgi.log

ENV DJANGO_SETTINGS_MODULE poms_app.settings_standalone

ENV RDS_DB_NAME postgres
ENV RDS_USERNAME postgres
ENV RDS_PASSWORD finmars
ENV RDS_HOSTNAME finmars-db
# ENV RDS_PORT

ENV REDIS_HOST finmars-redis:6379

ENV POMS_DEV True
ENV POMS_BLOOMBERG_SANDBOX True
ENV POMS_PRICING_AUTO_DOWNLOAD_DISABLED True

EXPOSE 8080

# CMD ["uwsgi.sh"]
# CMD ["ping", "192.168.57.2"]
# CMD ["tracepath", "safelagoon.com"]
# CMD ["telnet", "192.168.57.2", "5432"]
# CMD ["/var/app-venv/bin/python", "/var/app/manage_ai.py", "runserver", "0.0.0.0:8000"]
#CMD ["/usr/bin/supervisord", "-n"]
#CMD ["/bin/bash", "/var/app/docker/finmars-run.sh"]
CMD ["/bin/bash"]

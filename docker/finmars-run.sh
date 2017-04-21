
# /var/app/docker/finmars-run.sh

#source /var/app-venv/bin/activate
#cd /var/app/

echo "Finmars"

/var/app-venv/bin/python /var/app/manage.py migrate -noinput
/var/app-venv/bin/python /var/app/manage.py createcachetable -noinput
/var/app-venv/bin/python /var/app/manage.py clearsessions -noinput
/var/app-venv/bin/python /var/app/manage.py collectstatic -c --noinput

/var/app-venv/bin/python /var/app/manage.py initstandalone -noinput

#/usr/bin/uwsgi /etc/uwsgi/apps-enabled/finmars.ini

#run()

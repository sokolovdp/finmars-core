
# /var/app/docker/finmars-run.sh

#source /var/app-venv/bin/activate
#cd /var/app/

echo "Finmars"

/var/app-venv/bin/python /var/app/manage.py migrate
/var/app-venv/bin/python /var/app/manage.py createcachetable
/var/app-venv/bin/python /var/app/manage.py clearsessions
/var/app-venv/bin/python /var/app/manage.py collectstatic -c --noinput

/var/app-venv/bin/python /var/app/manage.py initstandalone

#/usr/bin/uwsgi /etc/uwsgi/apps-enabled/finmars.ini

#run()


echo "Finmars"

source /var/app-venv/bin/activate
cd /var/app/

./manage.py

./manage.py runserver 0.0.0.0:8080

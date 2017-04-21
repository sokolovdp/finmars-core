
echo "Finmars"

source /var/app-venv/bin/activate
cd /var/app/


function migrate {
    ./manage.py migrate
}

function createsuperuser {
    ./manage.py initstandalone
}

./manage.py runserver 0.0.0.0:8080

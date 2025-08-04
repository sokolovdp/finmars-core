import os


chdir = "/var/app/"
project_name = os.getenv("PROJECT_NAME", "poms_app")

bind = os.getenv("GUNICORN_BIND", "0.0.0.0:8080")

workers = int(os.getenv("GUNICORN_WORKERS", "1"))
threads = int(os.getenv("GUNICORN_THREADS", "1"))

timeout = int(os.getenv("GUNICORN_TIMEOUT", "180"))

accesslog = "/var/log/finmars/backend/gunicorn.access.log"
errorlog = "/var/log/finmars/backend/gunicorn.error.log"
loglevel = os.getenv("GUNICORN_LOG_LEVEL", "info")

reload = bool(os.getenv("LOCAL"))

INSTANCE_TYPE = os.getenv("INSTANCE_TYPE", "web")
celery_queue = os.getenv("QUEUES", "backend-general-queue,backend-background-queue")
celery_worker = os.getenv("WORKER_NAME", "worker1")

def on_starting(server):
    if INSTANCE_TYPE == "web":
        print("I'm web_instance")
        os.system("python /var/app/manage.py collectstatic -c --noinput")
    else:
        print("Gunicorn should not start for INSTANCE_TYPE:", INSTANCE_TYPE)
        server.log.info("Exiting because this pod is not a web instance")
        exit(0)

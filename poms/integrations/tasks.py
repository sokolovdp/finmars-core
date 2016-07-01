from celery import shared_task


@shared_task(name='backend.health_check')
def health_check_async():
    return True


def health_check():
    result = health_check_async.apply_async()
    try:
        return result.get(timeout=1, interval=0.1)
    except TimeoutError:
        pass
    return False

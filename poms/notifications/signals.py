from django.dispatch import Signal

notify = Signal(providing_args=[
    'recipient', 'nf_type', 'message', 'actor', 'verb', 'action_object', 'target',
    'create_date', 'level', 'data'
])

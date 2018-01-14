from celery import shared_task
from django.apps import apps
from .utils import return_csv_file, split_csv_str

# @shared_task
def run_import(obj):
    from poms.data_import.models import DataImportSchema
    schema = DataImportSchema.objects.filter(data_import=obj).values('source', 'target')
    matching_fields = {s['source']: s['target'] for s in schema}
    with open(obj.file.file.name, 'rb') as csv_file:
        f = return_csv_file(csv_file)
        for row in f:
            keys = split_csv_str(row.keys())
            values = split_csv_str(row.values())
            if values:
                data = {matching_fields[k]: values[i] for i, k in enumerate(keys)}
                name = data.pop('name')
                o = obj.model.model_class()(name=name, master_user_id=obj.master_user.id, attrs=data)
                o.save()
    obj.status = 2
    obj.save()
    return None
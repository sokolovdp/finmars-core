import csv
import io


def return_csv_file(file_obj):
    return csv.DictReader(io.TextIOWrapper(file_obj))

def split_csv_str(row):
    return list(filter(lambda x: len(x) > 0, list(row)[0].split(';')))
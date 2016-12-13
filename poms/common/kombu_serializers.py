import pickle

import base64
from django.core.signing import TimestampSigner
from kombu.five import BytesIO
from kombu.serialization import register
from kombu.utils.encoding import str_to_bytes, bytes_to_str

__author__ = 'ailyukhin'


def register_pickle_signed(key=None, salt=None):
    def signer():
        return TimestampSigner(key=key, salt=salt)

    def encoder(obj):
        d = pickle.dumps(obj)
        d = base64.b64encode(d)
        d = signer().sign(d)
        d = str_to_bytes(d)
        return d

    def decoder(s):
        d = bytes_to_str(s)
        d = signer().unsign(d)
        d = base64.b64decode(d)
        return pickle.load(BytesIO(d))

    register('pickle-signed', encoder, decoder,
             content_type='application/x-python-serialize-signed',
             content_encoding='binary')

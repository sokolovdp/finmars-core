from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as _


class PhoneNumberValidator(object):
    code = 'invalid'
    message = _('Enter a valid phone number.')

    def __init__(self):
        pass

    def __call__(self, value):
        # raise ValidationError(self.message, code=self.code)
        return True

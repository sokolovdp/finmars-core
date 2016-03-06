from __future__ import unicode_literals

from rest_framework import serializers

from poms.audit.models import AuthLog


class AuthLogSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='authlog-detail')

    class Meta:
        model = AuthLog
        fields = ['url', 'date', 'user_ip', 'user_agent', 'is_success']

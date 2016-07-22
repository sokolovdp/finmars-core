from rest_framework.response import Response

from poms.common.views import AbstractViewSet
from poms.integrations.serializers import InstrumentBloombergImportSerializer, InstrumentFileImportSerializer


class AbstractIntegrationViewSet(AbstractViewSet):
    serializer_class = None

    def get_serializer(self, *args, **kwargs):
        serializer_class = self.get_serializer_class()
        kwargs['context'] = self.get_serializer_context()
        return serializer_class(*args, **kwargs)

    def get_serializer_class(self):
        return self.serializer_class

    def get_serializer_context(self):
        return {
            'request': self.request,
            'format': self.format_kwarg,
            'view': self
        }


class InstrumentFileImportViewSet(AbstractIntegrationViewSet):
    serializer_class = InstrumentFileImportSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class InstrumentBloombergImportViewSet(AbstractIntegrationViewSet):
    serializer_class = InstrumentBloombergImportSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

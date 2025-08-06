from django.db.models import Q
from rest_framework.filters import BaseFilterBackend


class ConfigurationQueryFilter(BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        query = request.query_params.get("query", None)

        if query:
            pieces = query.split(" ")

            name_q = Q()
            short_name_q = Q()
            description_q = Q()
            configuration_code_q = Q()

            for piece in pieces:
                name_q.add(Q(name__icontains=piece), Q.AND)
                short_name_q.add(Q(short_name__icontains=piece), Q.AND)
                description_q.add(Q(description__icontains=piece), Q.AND)
                configuration_code_q.add(Q(configuration_code__icontains=piece), Q.AND)

            options = Q()

            options.add(name_q, Q.OR)
            options.add(short_name_q, Q.OR)
            options.add(description_q, Q.OR)
            options.add(configuration_code_q, Q.OR)

            return queryset.filter(options)

        return queryset


class ManifestQueryFilter(BaseFilterBackend):
    """
    Read any query params that start with "manifest."
    and turn them into manifest_data__… lookups.
    """

    def filter_queryset(self, request, queryset, view):
        for param, raw_value in request.query_params.items():
            if not param.startswith('manifest.'):
                continue

            # param = "manifest.settings.ui.is_shown_in_sidenav"
            # split into ['manifest', 'settings', 'ui', 'is_shown_in_sidenav']
            parts = param.split('.')

            # build the Django lookup: manifest_data__settings__ui__is_shown_in_sidenav
            lookup = "manifest_data"
            for key in parts[1:]:
                lookup += "__" + key

            # parse boolean strings into real bools
            val_lower = raw_value.lower()
            if val_lower in ("true", "false"):
                value = val_lower == "true"
            else:
                value = raw_value

            # apply the filter
            queryset = queryset.filter(**{lookup: value})

        return queryset
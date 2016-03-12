from __future__ import unicode_literals

from collections import OrderedDict

import six
from django.core.paginator import Page
from django.utils.encoding import force_bytes
from rest_framework.renderers import BaseRenderer


class PlainTextRenderer(BaseRenderer):
    media_type = 'text/html'
    format = 'debug'
    charset = 'utf-8'

    def render(self, data, accepted_media_type=None, renderer_context=None):
        if data is None:
            return bytes()
        import pandas as pd
        # pd.set_option('display.height', 1000)
        # pd.set_option('display.max_rows', 500)
        # pd.set_option('display.max_columns', 500)
        # pd.set_option('display.width', 1000)

        count = None
        if isinstance(data, dict) and 'results' in data:
            results = data['results']
            count = data['count']
        else:
            results = data
            count = len(results)

        if not isinstance(results, list):
            results = [results]

        pd_index = []
        pd_data = []
        for instance in results:
            if len(pd_index) == 0:
                pd_index = [k for k in six.iterkeys(instance) if k != 'url']
            pd_data.append([v for k, v in six.iteritems(instance) if k != 'url'])
        df = pd.DataFrame(data=pd_data, columns=pd_index)
        # df = pd.DataFrame.from_dict(results)

        # txt = '<html><body><pre>%s</pre></body></html>' % (df, )

        summary = pd.DataFrame.from_dict([{
            'count': count,
            'page': len(results),
        }])

        txt = '<html>' \
              '<style>' \
              'table {border-spacing:0;} ' \
              'thead {background:#f0f0f0;} ' \
              'tr:nth-child(2n) {background:#f0f0f0;} ' \
              'tr:hover {background:#d0d0d0;}' \
              'th,td{font-family:monospace;padding:5px;}' \
              '</style>' \
              '<body>' \
              '<h2>Summary</h2>' \
              '%s' \
              '<h2>Data</h2>' \
              '%s' \
              '</body>' \
              '</html>' % (summary.to_html(), df.to_html(),)
        return force_bytes(txt, 'utf-8')


import logging

_l = logging.getLogger('poms.reports')


def sprint_table(data, headers=None, floatfmt=None, showindex=None):
    try:
        import pandas
    except ImportError:
        pandas = None
    if pandas:
        with pandas.option_context('display.max_rows', 10000,
                                   'display.max_columns', 10000,
                                   'display.float_format', '{:.4f}'.format,
                                   'display.line_width', 10000):
            df = pandas.DataFrame(data=data, columns=headers)
            # df.index += 1
            return df.to_string(index=False)
    import tabulate
    if not floatfmt:
        floatfmt = '.4f'
    if not showindex:
        showindex = 'default'
    return tabulate.tabulate(data, headers=headers, floatfmt=floatfmt, showindex=showindex)

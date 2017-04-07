import logging

_l = logging.getLogger('poms.reports')


def sprint_table(data, headers=None, floatfmt=None, showindex=None):
    import tabulate
    if not floatfmt:
        floatfmt = ".4f"
    if not showindex:
        showindex = 'default'
    return tabulate.tabulate(data, headers=headers, floatfmt=floatfmt, showindex=showindex)

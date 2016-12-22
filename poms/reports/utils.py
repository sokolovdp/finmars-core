def sprint_table(data, headers=None, floatfmt=".4f"):
    import tabulate
    return tabulate.tabulate(data, headers=headers, floatfmt=floatfmt)

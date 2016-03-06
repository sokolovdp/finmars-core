from __future__ import unicode_literals, division

from collections import OrderedDict

DEBUG = True


def get_data(cnt):
    # # transactions = list(Transaction.objects.order_by('id').filter(is_canceled=False))
    # transactions = list(Transaction.objects.order_by('id').all())
    #
    # data = []
    # for t in transactions:
    #     data.append([t.instrument.name, t.position_size_with_sign, t.principal_with_sign])
    #     # data.append([t.id, t.position_size_with_sign, t.principal_with_sign])

    index = ['instrument', 'position_size_with_sign', 'principal_with_sign']
    data = [
        # ['I_1', 50.0, -100.0],
        # ['I_1', 25.0, -40.0],
        # ['I_1', -50.0, 80.0],
        ['I_1', 25.0, -70.0],
        ['I_1', -25.0, 30.0],
    ]
    data = [
        ['I_1', 10000.0, -70.0],
        ['I_1', 10000.0, -70.0],
        ['I_1', -1.0, 30.0],
    ]
    # data = [
    #     ['I_1', 50.0, -100.0],
    #     ['I_1', 50.0, -100.0],
    #     # ['I_1', 25.0, -40.0],
    #     ['I_1', -50.0, 80.0],
    #     ['I_1', 25.0, -70.0],
    #     # ['I_1', -25.0, 30.0],
    #     ['I_1', -2.0, 70.0],
    # ]
    # data = [
    #     # ['I_1', 5.0, -10.0],
    #     # ['I_1', 5.0, -10.0],
    #     # ['I_1', 5.0, -10.0],
    #     # ['I_1', 5.0, -10.0],
    #     # ['I_1', 5.0, -10.0],
    #     ['I_1', -14.0, 99.0],
    #     ['I_1', -14.0, 99.0],
    #     ['I_1', 1.0, -10.0],
    #     ['I_1', 1.0, -10.0],
    #     # ['I_1', 1.0, -10.0],
    # ]

    # import random
    # data = []
    # for i in range(0, cnt):
    #     while True:
    #         position_size_with_sign = random.randint(-10, 10)
    #         if position_size_with_sign != 0:
    #             break
    #     principal_with_sign = position_size_with_sign
    #     data.append(['I_1', position_size_with_sign, -principal_with_sign * 10])
    # if DEBUG:
    #     print(data)

    # data = [
    #     ['I_1', 10, -10],
    #     # ['I_1', 3, -3],
    #     # ['I_1', 4, -4],
    #     ['I_1', -5, 5],
    #     # ['I_1', 3, -3],
    #     # ['I_1', -10, 10],
    #     # ['I_1', -2, 2],
    #     # ['I_1', 4, -4],
    #     # ['I_1', -1, 1],
    #     # ['I_1', -6, 6]
    # ]
    # while len(data) < cnt:
    #     data *= 2
    # data = data[0:cnt]

    # data = [['I_1', -8, 80], ['I_1', -6, 60], ['I_1', 3, -30], ['I_1', -2, 20], ['I_1', -9, 90], ['I_1', -2, 20],
    #         ['I_1', 9, -90], ['I_1', 5, -50], ['I_1', 10, -100], ['I_1', 1, -10], ['I_1', 4, -40], ['I_1', -8, 80],
    #         ['I_1', 1, -10], ['I_1', 6, -60], ['I_1', -1, 10], ['I_1', 8, -80], ['I_1', 8, -80], ['I_1', 10, -100],
    #         ['I_1', -7, 70], ['I_1', -10, 100], ['I_1', 10, -100], ['I_1', 1, -10], ['I_1', -4, 40], ['I_1', 8, -80],
    #         ['I_1', 7, -70], ['I_1', 8, -80], ['I_1', 3, -30], ['I_1', -6, 60], ['I_1', 2, -20], ['I_1', 4, -40],
    #         ['I_1', 1, -10], ['I_1', -6, 60], ['I_1', -5, 50], ['I_1', -5, 50], ['I_1', 7, -70], ['I_1', -1, 10],
    #         ['I_1', 3, -30], ['I_1', 4, -40], ['I_1', 5, -50], ['I_1', 1, -10], ['I_1', 6, -60], ['I_1', 6, -60],
    #         ['I_1', 4, -40], ['I_1', 9, -90], ['I_1', -8, 80], ['I_1', -4, 40], ['I_1', 2, -20], ['I_1', 4, -40],
    #         ['I_1', 2, -20], ['I_1', 8, -80], ['I_1', -10, 100], ['I_1', 7, -70], ['I_1', 6, -60], ['I_1', -10, 100],
    #         ['I_1', 9, -90], ['I_1', -8, 80], ['I_1', 5, -50], ['I_1', -10, 100], ['I_1', 10, -100], ['I_1', 4, -40],
    #         ['I_1', -9, 90], ['I_1', -8, 80], ['I_1', -4, 40], ['I_1', -9, 90], ['I_1', -10, 100], ['I_1', -7, 70],
    #         ['I_1', -8, 80], ['I_1', 5, -50], ['I_1', -5, 50], ['I_1', -8, 80], ['I_1', -1, 10], ['I_1', 4, -40],
    #         ['I_1', -2, 20], ['I_1', 3, -30], ['I_1', 1, -10], ['I_1', 9, -90], ['I_1', 1, -10], ['I_1', 7, -70],
    #         ['I_1', -10, 100], ['I_1', 3, -30], ['I_1', 1, -10], ['I_1', -3, 30], ['I_1', 6, -60], ['I_1', 9, -90],
    #         ['I_1', -6, 60], ['I_1', 6, -60], ['I_1', 1, -10], ['I_1', 7, -70], ['I_1', -7, 70], ['I_1', -6, 60],
    #         ['I_1', -4, 40], ['I_1', 1, -10], ['I_1', 8, -80], ['I_1', -6, 60], ['I_1', -8, 80], ['I_1', -2, 20],
    #         ['I_1', 7, -70], ['I_1', -10, 100], ['I_1', -2, 20], ['I_1', 1, -10]]

    for r in data:
        r[1] = float(r[1])
        r[2] = float(r[2])

    return data, index


def get_data2(data):
    make_record = lambda instrument, position_size_with_sign, principal_with_sign: OrderedDict((
        ('instrument', instrument,),
        ('position_size_with_sign', position_size_with_sign,),
        # ('principal_with_sign', principal_with_sign,),
        ('avco', 0.,),
        ('rolling_position', 0.,)
    ))
    return [make_record(*a) for a in data]


def avco3(transactions):
    in_stock = {}
    for_sale = {}
    rolling_position = 0.

    def show(m):
        if DEBUG:
            if isinstance(m, list):
                # print('-' * 79)
                # for t in m:
                #     print(t)
                pass
            else:
                print('-' * 79)
                print(m)

    show(transactions)
    for index, transaction in enumerate(transactions):
        instrument = transaction['instrument']
        position_size_with_sign = transaction['position_size_with_sign']
        transaction['multiplier'] = 0.
        if position_size_with_sign > 0.:  # покупка
            instrument_for_sale = for_sale.get(instrument, [])
            if instrument_for_sale:  # есть прошлые продажи, которые надо закрыть
                if position_size_with_sign + rolling_position >= 0.:  # все есть
                    transaction['multiplier'] = abs(rolling_position / position_size_with_sign)
                    for t in instrument_for_sale:
                        t['multiplier'] = 1.
                    in_stock[instrument] = in_stock.get(instrument, []) + [transaction]
                else:  # только частично
                    transaction['multiplier'] = 1.
                    for t in instrument_for_sale:
                        t['multiplier'] += abs((1. - t['multiplier']) * position_size_with_sign / rolling_position)
                for_sale[instrument] = [t for t in instrument_for_sale if t['multiplier'] < 1.]
            else:  # новая "чистая" покупка
                transaction['multiplier'] = 0.
                in_stock[instrument] = in_stock.get(instrument, []) + [transaction]
        else:  # продажа
            instrument_in_stock = in_stock.get(instrument, [])
            if instrument_in_stock:  # есть что продавать
                if position_size_with_sign + rolling_position >= 0.:  # все есть
                    transaction['multiplier'] = 1.
                    for t in instrument_in_stock:
                        t['multiplier'] += abs((1. - t['multiplier']) * position_size_with_sign / rolling_position)
                else:  # только частично
                    transaction['multiplier'] = abs(rolling_position / position_size_with_sign)
                    for t in instrument_in_stock:
                        t['multiplier'] = 1.
                    for_sale[instrument] = for_sale.get(instrument, []) + [transaction]
                in_stock[instrument] = [t for t in instrument_in_stock if t['multiplier'] < 1.]
            else:  # нечего продавать
                transaction['multiplier'] = 0.
                for_sale[instrument] = for_sale.get(instrument, []) + [transaction]
        rolling_position += position_size_with_sign
        transaction['rolling_position'] = rolling_position

    show(transactions)

    if DEBUG:
        show('in_stock: %s' % in_stock)
        show('for_sale: %s' % for_sale)

    v = 0.
    for t in transactions:
        v += t['position_size_with_sign'] * (1 - t['multiplier'])
    # if v != transactions[-1]['rolling_position']:
    #     raise RuntimeError('avco error')
    show('rolling_position=%s, verify=%s' % (rolling_position, v))


def fifo2(transactions):
    in_stock = {}
    for_sale = {}
    rolling_position = 0.

    def show(m):
        if DEBUG:
            if isinstance(m, list):
                # print('-' * 79)
                # for t in m:
                #     print(t)
                pass
            else:
                print('-' * 79)
                print(m)

    show(transactions)
    for index, transaction in enumerate(transactions):
        instrument = transaction['instrument']
        position_size_with_sign = transaction['position_size_with_sign']
        transaction['multiplier'] = 0.
        if position_size_with_sign > 0.:  # покупка
            instrument_for_sale = for_sale.get(instrument, [])
            balance = position_size_with_sign
            if instrument_for_sale:
                for t in instrument_for_sale:
                    sale = t['not_closed']
                    if balance + sale > 0.:  # есть все
                        balance -= abs(sale)
                        t['multiplier'] = 1.
                        t['not_closed'] = t['not_closed'] - abs(t['position_size_with_sign'])
                    else:
                        t['not_closed'] = t['not_closed'] + balance
                        t['multiplier'] = 1. - abs(t['not_closed'] / t['position_size_with_sign'])
                        balance = 0.
                    # sale = (1 - t['multiplier']) * t['position_size_with_sign']
                    # if balance + sale > 0.:  # есть все
                    #     balance -= abs(sale)
                    #     t['multiplier'] = 1.
                    # else:
                    #     t['multiplier'] = 1 - abs((abs(sale) - balance) / t['position_size_with_sign'])
                    #     balance = 0.
                    if balance <= 0.:
                        break
                for_sale[instrument] = [t for t in instrument_for_sale if t['multiplier'] < 1.]
            transaction['balance'] = balance
            transaction['multiplier'] = abs((position_size_with_sign - balance) / position_size_with_sign)
            if transaction['multiplier'] < 1.:
                in_stock[instrument] = in_stock.get(instrument, []) + [transaction]
        else:  # продажа
            instrument_in_stock = in_stock.get(instrument, [])
            sale = position_size_with_sign
            if instrument_in_stock:
                for t in instrument_in_stock:
                    balance = t['balance']
                    if sale + balance > 0.:  # есть все
                        t['balance'] = balance - abs(sale)
                        t['multiplier'] = abs(
                            (t['position_size_with_sign'] - t['balance']) / t['position_size_with_sign'])
                        # print(t['position_size_with_sign'])
                        # print(t['balance'])
                        # print(t['position_size_with_sign'] - t['balance'])
                        sale = 0.
                    else:
                        t['balance'] = 0.
                        t['multiplier'] = 1.
                        sale += abs(balance)
                    # balance = (1 - t['multiplier']) * t['position_size_with_sign']
                    # if sale + balance > 0.:  # есть все
                    #     t['multiplier'] = abs((balance - abs(sale)) / t['position_size_with_sign'])
                    #     sale = 0.
                    # else:
                    #     t['multiplier'] = 1.
                    #     sale += abs(balance)
                    if sale >= 0.:
                        break
                in_stock[instrument] = [t for t in instrument_in_stock if t['multiplier'] < 1.]
            transaction['not_closed'] = sale
            transaction['multiplier'] = abs((position_size_with_sign - sale) / position_size_with_sign)
            if transaction['multiplier'] < 1.:
                for_sale[instrument] = for_sale.get(instrument, []) + [transaction]

        rolling_position += position_size_with_sign
        transaction['rolling_position'] = rolling_position

    show(transactions)

    if DEBUG:
        show('in_stock: %s' % in_stock)
        show('for_sale: %s' % for_sale)

    v = 0.
    for t in transactions:
        v += t['position_size_with_sign'] * (1 - t['multiplier'])
    # if v != transactions[-1]['rolling_position']:
    #     raise RuntimeError('fifo error')
    show('rolling_position=%s, verify=%s' % (rolling_position, v))


def main():
    # import os
    # os.environ.setdefault("DJANGO_SETTINGS_MODULE", "poms_app.settings")
    # import django
    # django.setup()

    import sys
    print(sys.version)

    data, index = get_data(10000)
    data2 = get_data2(data)
    number = 1
    precision = 3
    if DEBUG:
        # avco2(data, index)
        avco3(data2)

        # fifo(data, index)
        fifo2(data2)
    else:
        import timeit

        def test(prefix, func):
            times = timeit.repeat(func, number=number)
            print('%s: loops=%s, best=%.*g, times=%s' % (
                prefix, number, precision, min(times), ['%.*g' % (precision, t,) for t in times]))
            # if min(times) > 0.002:
            #     print(data)

        print('loops=%s, data=%s, total_rows=%s' % (number, len(data), number * len(data)))
        # test('avco2 pandas', lambda: avco2(data, index))
        test('avco3 code  ', lambda: avco3(data2))
        # test('fifo  pandas', lambda: fifo(data, index))
        test('fifo2 code  ', lambda: fifo2(data2))
        # print('avco2 code: loops=%s, times=%s' % (number, timeit.repeat(lambda: avco2(data, index), number=number)))
        # print('avco3 code  :    -> %s -> %s' % (number, timeit.repeat(lambda: avco3(data2), number=number)))
        # print('fifo  pandas -> %s -> %s' % (number, timeit.repeat(lambda: fifo(data, index), number=number)))
        # print('fifo2 code   -> %s -> %s' % (number, timeit.repeat(lambda: fifo2(data2), number=number)))


if __name__ == "__main__":
    main()

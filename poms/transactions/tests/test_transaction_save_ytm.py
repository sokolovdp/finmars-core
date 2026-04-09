from datetime import date, timedelta

from django.conf import settings
from django.db import connection

from poms.common.common_base_test import BaseTestCase
from poms.portfolios.models import Portfolio
from poms.transactions.models import (
    ComplexTransaction,
    ComplexTransactionStatus,
    Transaction,
    TransactionClass,
    TransactionType,
    TransactionTypeGroup,
)


class TransactionSaveYtmTest(BaseTestCase):
    """
    Tests that Transaction.save() never produces a complex ytm_at_cost,
    especially for defaulted bonds where maturity_date is in the past.

    Reproduces production error:
      Book Exception: Field 'ytm_at_cost' expected a number but got
      (-0.9802270234352741+0.586687270683598j)
    for instrument USP7807HAM71 (defaulted, maturity 2022, traded 2026-03-20).
    """

    databases = "__all__"

    def setUp(self):
        super().setUp()
        self.init_test_case()

        self.transaction_type_group = (
            TransactionTypeGroup.objects.using(settings.DB_DEFAULT).filter(user_code__contains="unified").first()
        )

        self.transaction_type = TransactionType.objects.using(settings.DB_DEFAULT).create(
            master_user=self.master_user,
            owner=self.member,
            configuration_code="local.poms.space00000",
            user_code="test_ytm_type",
            name="Test YTM Type",
            short_name="TYT",
            group=self.transaction_type_group.user_code,
            type=TransactionType.TYPE_DEFAULT,
        )

        self.portfolio = Portfolio.objects.using(settings.DB_DEFAULT).create(
            master_user=self.master_user,
            owner=self.member,
            user_code="test_portfolio",
            name="Test Portfolio",
            short_name="TP",
        )

        self.complex_transaction_status = ComplexTransactionStatus.objects.using(settings.DB_DEFAULT).first()

    def _create_complex_transaction(self):
        return ComplexTransaction.objects.using(settings.DB_DEFAULT).create(
            master_user=self.master_user,
            owner=self.member,
            transaction_type=self.transaction_type,
            status=self.complex_transaction_status,
            date=date.today(),
        )

    def _save_transaction(self, instrument, trade_price, accounting_date):
        ct = self._create_complex_transaction()
        transaction = Transaction(
            master_user=self.master_user,
            owner=self.member,
            instrument=instrument,
            portfolio=self.portfolio,
            complex_transaction=ct,
            transaction_class=TransactionClass.objects.using(settings.DB_DEFAULT).first(),
            settlement_currency=self.usd,
            trade_price=trade_price,
            accounting_date=accounting_date,
            cash_date=accounting_date,
        )
        transaction.save()
        return transaction

    def test_defaulted_bond_maturity_in_past(self):
        """
        Bond in default: maturity_date=2022, trade_date=2026.
        ytm_at_cost must be a real number (float/int), never complex.
        """
        instrument = self.create_instrument()
        instrument.maturity_date = date(2022, 6, 15)
        instrument.maturity_price = 100
        instrument.price_multiplier = 1
        instrument.save()

        transaction = self._save_transaction(
            instrument=instrument,
            trade_price=98.5,
            accounting_date=date(2026, 3, 20),
        )

        self.assertIsInstance(transaction.ytm_at_cost, (int, float))
        self.assertNotIsInstance(transaction.ytm_at_cost, complex)

    def test_normal_bond_positive_ytm(self):
        """Normal bond with future maturity — ytm_at_cost should be a real number."""
        instrument = self.create_instrument()
        instrument.maturity_date = date.today() + timedelta(days=365)
        instrument.maturity_price = 100
        instrument.price_multiplier = 1
        instrument.save()

        transaction = self._save_transaction(
            instrument=instrument,
            trade_price=95.0,
            accounting_date=date.today(),
        )

        self.assertIsInstance(transaction.ytm_at_cost, (int, float))
        self.assertNotIsInstance(transaction.ytm_at_cost, complex)

    def test_bond_bought_above_par_negative_ytm(self):
        """Bond bought above par — ytm_at_cost should be negative but still real."""
        instrument = self.create_instrument()
        instrument.maturity_date = date.today() + timedelta(days=365)
        instrument.maturity_price = 100
        instrument.price_multiplier = 1
        instrument.save()

        transaction = self._save_transaction(
            instrument=instrument,
            trade_price=110.0,
            accounting_date=date.today(),
        )

        self.assertIsInstance(transaction.ytm_at_cost, (int, float))
        self.assertNotIsInstance(transaction.ytm_at_cost, complex)

    def test_perpetual_instrument_no_maturity(self):
        """Instrument with no maturity date — ytm_at_cost should still be real."""
        instrument = self.create_instrument()
        instrument.maturity_date = None
        instrument.save()

        transaction = self._save_transaction(
            instrument=instrument,
            trade_price=100.0,
            accounting_date=date.today(),
        )

        self.assertIsInstance(transaction.ytm_at_cost, (int, float))
        self.assertNotIsInstance(transaction.ytm_at_cost, complex)

    def test_complex_value_already_in_db_is_sanitized_on_resave(self):
        """
        Simulates a scenario where a complex number was written to the DB
        before the fix was deployed. On next save(), ytm_at_cost must be
        replaced with a real number.
        """
        instrument = self.create_instrument()
        instrument.maturity_date = None
        instrument.save()

        transaction = self._save_transaction(
            instrument=instrument,
            trade_price=100.0,
            accounting_date=date.today(),
        )
        self.assertIsInstance(transaction.ytm_at_cost, (int, float))

        # Inject a complex number directly into the DB, bypassing Django ORM validation
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE transactions_transaction SET ytm_at_cost = %s WHERE id = %s",
                [-0.98, transaction.id],
            )

        # Reload from DB to confirm the raw value is there
        transaction.refresh_from_db()

        # Now manually set the in-memory value to complex (as if loaded from
        # a corrupted row or assigned by buggy code before the fix)
        transaction.ytm_at_cost = complex(-0.9802, 0.5866)

        # save() must sanitize the value — no TypeError, no complex in DB
        transaction.save()
        transaction.refresh_from_db()

        self.assertIsInstance(transaction.ytm_at_cost, (int, float))
        self.assertNotIsInstance(transaction.ytm_at_cost, complex)
        self.assertEqual(transaction.ytm_at_cost, 0)

    def test_extreme_maturity_date_2999(self):
        """Instrument with maturity far in the future (2999) — treated as perpetual."""
        instrument = self.create_instrument()
        instrument.maturity_date = date(2999, 1, 1)
        instrument.save()

        transaction = self._save_transaction(
            instrument=instrument,
            trade_price=100.0,
            accounting_date=date.today(),
        )

        self.assertIsInstance(transaction.ytm_at_cost, (int, float))
        self.assertNotIsInstance(transaction.ytm_at_cost, complex)

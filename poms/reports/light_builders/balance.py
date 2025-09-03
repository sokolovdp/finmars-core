import logging
import time

from celery import group

from poms.accounts.models import Account
from poms.celery_tasks.models import CeleryTask
from poms.iam.utils import get_allowed_queryset
from poms.portfolios.models import Portfolio
from poms.reports.common import Report
from poms.reports.sql_builders.balance import build
from poms.users.models import EcosystemDefault

_l = logging.getLogger("poms.reports")


class BalanceReportLightBuilderSql:
    def __init__(self, instance=None):
        _l.debug("ReportBuilderSql init")

        self.instance = instance

        self.instance.allocation_mode = Report.MODE_IGNORE

        self.ecosystem_defaults = EcosystemDefault.cache.get_cache(master_user_pk=self.instance.master_user.pk)

        _l.debug(f"self.instance master_user {self.instance.master_user} report_date {self.instance.report_date}")

        """
        TODO IAM_SECURITY_VERIFY need to check, if user somehow passes 
        id of object he has no access to we should throw error
        """

        """Important security methods"""
        self.transform_to_allowed_portfolios()
        self.transform_to_allowed_accounts()

    def transform_to_allowed_portfolios(self):
        if not len(self.instance.portfolios):
            self.instance.portfolios = get_allowed_queryset(self.instance.member, Portfolio.objects.all())

    def transform_to_allowed_accounts(self):
        if not len(self.instance.accounts):
            self.instance.accounts = get_allowed_queryset(self.instance.member, Account.objects.all())

    def build_balance(self):
        st = time.perf_counter()

        self.instance.items = []

        self.parallel_build()

        self.instance.execution_time = float(f"{time.perf_counter() - st:3.3f}")

        _l.debug(f"items total {len(self.instance.items)}")

        relation_prefetch_st = time.perf_counter()

        self.instance.relation_prefetch_time = float(f"{time.perf_counter() - relation_prefetch_st:3.3f}")

        _l.debug(f"build_st done: {self.instance.execution_time}")

        return self.instance

    def parallel_build(self):
        st = time.perf_counter()

        tasks = []

        if self.instance.portfolio_mode == Report.MODE_INDEPENDENT:
            for portfolio in self.instance.portfolios:
                task = CeleryTask.objects.create(
                    master_user=self.instance.master_user,
                    member=self.instance.member,
                    verbose_name="Balance Report",
                    type="calculate_balance_report",
                    options_object={
                        "report_date": self.instance.report_date,
                        "portfolios_ids": [portfolio.id],
                        "accounts_ids": [instance.id for instance in self.instance.accounts],
                        "strategies1_ids": [instance.id for instance in self.instance.strategies1],
                        "strategies2_ids": [instance.id for instance in self.instance.strategies2],
                        "strategies3_ids": [instance.id for instance in self.instance.strategies3],
                        "report_currency_id": self.instance.report_currency.id,
                        "pricing_policy_id": self.instance.pricing_policy.id,
                        "cost_method_id": self.instance.cost_method.id,
                        "show_balance_exposure_details": self.instance.show_balance_exposure_details,
                        "portfolio_mode": self.instance.portfolio_mode,
                        "account_mode": self.instance.account_mode,
                        "strategy1_mode": self.instance.strategy1_mode,
                        "strategy2_mode": self.instance.strategy2_mode,
                        "strategy3_mode": self.instance.strategy3_mode,
                        "allocation_mode": self.instance.allocation_mode,
                    },
                )

                tasks.append(task)

        else:
            task = CeleryTask.objects.create(
                master_user=self.instance.master_user,
                member=self.instance.member,
                verbose_name="Balance Report",
                type="calculate_balance_report",
                options_object={
                    "report_date": self.instance.report_date,
                    "portfolios_ids": [instance.id for instance in self.instance.portfolios],
                    "accounts_ids": [instance.id for instance in self.instance.accounts],
                    "strategies1_ids": [instance.id for instance in self.instance.strategies1],
                    "strategies2_ids": [instance.id for instance in self.instance.strategies2],
                    "strategies3_ids": [instance.id for instance in self.instance.strategies3],
                    "report_currency_id": self.instance.report_currency.id,
                    "pricing_policy_id": self.instance.pricing_policy.id,
                    "cost_method_id": self.instance.cost_method.id,
                    "show_balance_exposure_details": self.instance.show_balance_exposure_details,
                    "portfolio_mode": self.instance.portfolio_mode,
                    "account_mode": self.instance.account_mode,
                    "strategy1_mode": self.instance.strategy1_mode,
                    "strategy2_mode": self.instance.strategy2_mode,
                    "strategy3_mode": self.instance.strategy3_mode,
                    "allocation_mode": self.instance.allocation_mode,
                },
            )

            tasks.append(task)

        _l.debug("Going to run %s tasks", len(tasks))

        # Run the group of tasks
        job = group(
            build.s(
                task_id=task.id,
                context={
                    "realm_code": self.instance.master_user.realm_code,
                    "space_code": self.instance.master_user.space_code,
                },
            )
            for task in tasks
        )

        group_result = job.apply_async()
        # Wait for all tasks to finish and get their results
        group_result.join()

        # Retrieve results
        all_dicts = []
        # TODO probably we can do some optimization here
        for result in group_result.results:
            # Each result is an AsyncResult instance.
            # You can get the result of the task with its .result property.
            all_dicts.extend(result.result)

        for task in tasks:
            # refresh the task instance to get the latest status from the database
            task.refresh_from_db()

            task.delete()

        # 'all_dicts' is now a list of all dicts returned by the tasks
        self.instance.items = all_dicts

        _l.debug("parallel_build done: %s", f"{time.perf_counter() - st:3.3f}")

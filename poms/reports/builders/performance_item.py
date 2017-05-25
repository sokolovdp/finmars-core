
class PerformanceReportItem:
    def __init__(self,
                 report,
                 ):
        self.report = report
        self.id = None

        self.custom_fields = []

    def __str__(self):
        return 'PerformanceReportItem:%s' % self.id

    def eval_custom_fields(self):
        # use optimization inside serialization
        res = []
        self.custom_fields = res


class PerformanceReport:
    def __init__(self, id=None, task_id=None, task_status=None, master_user=None, member=None,
                 custom_fields=None, items=None):
        self.has_errors = False
        self.id = id
        self.task_id = task_id
        self.task_status = task_status
        self.master_user = master_user
        self.member = member
        self.custom_fields = custom_fields or []

        self.context = {
            'master_user': self.master_user,
            'member': self.member,
        }

        self.items = items

        self.currencies = []
        self.portfolios = []
        self.accounts = []
        self.strategies1 = []
        self.strategies2 = []
        self.strategies3 = []

    def __str__(self):
        return 'PerformanceReport:%s' % self.id

    def close(self):
        for item in self.items:
            item.eval_custom_fields()


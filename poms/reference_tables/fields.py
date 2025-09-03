from poms.common.fields import PrimaryKeyRelatedFilteredField
from poms.reference_tables.models import ReferenceTableRow


class ReferenceTableRowField(PrimaryKeyRelatedFilteredField):
    queryset = ReferenceTableRow.objects
    filter_backends = ()

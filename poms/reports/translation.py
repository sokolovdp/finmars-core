from modeltranslation.translator import translator

from poms.common.translation import AbstractClassModelOptions
from poms.reports.models import ReportClass

translator.register(ReportClass, AbstractClassModelOptions)

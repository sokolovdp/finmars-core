from modeltranslation.translator import TranslationOptions


class ClassModelTranslationOptions(TranslationOptions):
    fields = ('name', 'description',)

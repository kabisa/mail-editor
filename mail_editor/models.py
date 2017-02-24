from django.db import models
from django.template import Template, Context
from django.utils.encoding import python_2_unicode_compatible
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from . import settings
from .mail_template import validate_template
from .utils import variable_help_text


@python_2_unicode_compatible
class Mail(models.Model):
    to = models.TextField()
    cc = models.TextField(blank=True)
    bcc = models.TextField(blank=True)
    subject = models.CharField(max_length=255)
    body = models.TextField()
    sent = models.BooleanField(default=False)

    class Meta:
        verbose_name = _('email')
        verbose_name_plural = _('emails')
        ordering = ('-pk',)

    def __str__(self):
        return self.subject


@python_2_unicode_compatible
class MailTemplate(models.Model):
    template_type = models.CharField(_('type'), max_length=50, unique=True)

    remarks = models.TextField(_('remarks'), help_text=_('Extra information about the template'))
    subject = models.CharField(_('subject'), max_length=255)
    body = models.TextField(_('body'), help_text=_('Add the body with {{variable}} placeholders'))

    CONFIG = {}
    CHOICES = None

    class Meta:
        verbose_name = _('mail template')
        verbose_name_plural = _('mail templates')

    def __init__(self, *args, **kwargs):
        super(MailTemplate, self).__init__(*args, **kwargs)
        fields = self._meta.get_field('template_type')
        fields.choices = settings.get_choices()

        self.CONFIG = settings.get_config()

    def __str__(self):
        return self.template_type

    def clean(self):
        validate_template(self)

    def render(self, context):
        tpl_subject = Template(self.subject)
        tpl_body = Template(self.body)
        ctx = Context(context)
        return tpl_subject.render(ctx), tpl_body.render(ctx)

    def get_variable_help_text(self):
        return variable_help_text(self.template_type)

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class FinanceCalendarConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'finance_calendar'
    verbose_name = _('Finance Calendar')
    
    def ready(self):
        # Import signal handlers
        import finance_calendar.signals

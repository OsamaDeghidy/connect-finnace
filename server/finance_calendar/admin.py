from django.contrib import admin
from .models import CalendarEvent


@admin.register(CalendarEvent)
class CalendarEventAdmin(admin.ModelAdmin):
    list_display = ('title', 'event_type', 'start_date', 'end_date', 'all_day')
    list_filter = ('event_type', 'all_day', 'start_date')
    search_fields = ('title', 'description')
    date_hierarchy = 'start_date'
    readonly_fields = ('color',)
    fieldsets = (
        (None, {
            'fields': ('title', 'description', 'event_type', 'color')
        }),
        ('Date Information', {
            'fields': ('start_date', 'end_date', 'all_day')
        }),
        ('Related Records', {
            'fields': ('receivable', 'payable', 'obligation')
        }),
        ('Google Calendar', {
            'fields': ('google_calendar_id', 'google_event_id'),
            'classes': ('collapse',),
        }),
        ('System Information', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    
    def get_readonly_fields(self, request, obj=None):
        readonly_fields = list(self.readonly_fields)
        if obj:  # editing an existing object
            readonly_fields.extend(['created_by', 'created_at', 'updated_at'])
        return readonly_fields

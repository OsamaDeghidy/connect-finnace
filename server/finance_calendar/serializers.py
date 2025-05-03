from rest_framework import serializers
from .models import CalendarEvent


class CalendarEventSerializer(serializers.ModelSerializer):
    color = serializers.CharField(read_only=True)
    
    class Meta:
        model = CalendarEvent
        fields = [
            'id', 'title', 'description', 'event_type', 'start_date', 'end_date',
            'all_day', 'color', 'receivable', 'payable', 'obligation',
            'google_calendar_id', 'google_event_id'
        ]
        read_only_fields = ['color']

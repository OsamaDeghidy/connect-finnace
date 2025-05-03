from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils.translation import gettext_lazy as _
from .models import CalendarEvent
from .serializers import CalendarEventSerializer
import datetime


class CalendarEventViewSet(viewsets.ModelViewSet):
    """
    API endpoint for calendar events.
    """
    queryset = CalendarEvent.objects.all()
    serializer_class = CalendarEventSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['event_type', 'all_day']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by date range if provided
        start_date = self.request.query_params.get('start_date', None)
        end_date = self.request.query_params.get('end_date', None)
        
        if start_date:
            queryset = queryset.filter(start_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(start_date__lte=end_date)
            
        # Filter by event type if provided
        event_type = self.request.query_params.get('event_type', None)
        if event_type:
            queryset = queryset.filter(event_type=event_type)
            
        return queryset
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    @action(detail=False, methods=['post'])
    def sync_events(self, request):
        """Sync all events from all sources."""
        CalendarEvent.sync_all_events()
        return Response({'status': 'Events synchronized successfully'})
    
    @action(detail=True, methods=['post'])
    def export_to_google(self, request, pk=None):
        """Export event to Google Calendar."""
        event = self.get_object()
        
        # Here you would implement the actual Google Calendar API integration
        # This is a placeholder for the actual implementation
        
        # For demonstration purposes, we'll just update the Google Calendar IDs
        event.google_calendar_id = 'primary'
        event.google_event_id = f'event_{event.id}_{datetime.datetime.now().timestamp()}'
        event.save()
        
        return Response({
            'status': 'Event exported to Google Calendar',
            'google_calendar_id': event.google_calendar_id,
            'google_event_id': event.google_event_id
        })
    
    @action(detail=False, methods=['post'])
    def export_all_to_google(self, request):
        """Export all events to Google Calendar."""
        events = self.get_queryset()
        count = 0
        
        # Here you would implement the actual Google Calendar API integration
        # This is a placeholder for the actual implementation
        
        for event in events:
            event.google_calendar_id = 'primary'
            event.google_event_id = f'event_{event.id}_{datetime.datetime.now().timestamp()}'
            event.save()
            count += 1
        
        return Response({
            'status': 'Events exported to Google Calendar',
            'count': count
        })

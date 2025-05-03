from django.shortcuts import render

def index(request):
    """View for the home page."""
    return render(request, 'index.html')

# backend/ring_counter/urls.py

from django.urls import path
from .views import OnionProcessView # <-- Import the view

urlpatterns = [
    # This creates the endpoint: /api/process-onion/
    path('process-onion/', OnionProcessView.as_view(), name='process-onion'),
]
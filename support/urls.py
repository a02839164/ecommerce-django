from django.urls import path
from . import views



urlpatterns = [
    path("center/", views.support_center, name="support-center"),
    path("ticket/<int:ticket_id>/", views.ticket_detail, name="ticket-detail"),
]
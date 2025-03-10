from django.urls import path
from .views import whook_handler


urlpatterns = [
    path('', whook_handler),
]
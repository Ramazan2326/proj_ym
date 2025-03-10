from django.urls import path
from oauth_bru.views import redirect_to_bru


urlpatterns = [
    path('', redirect_to_bru, name='oauth_redirect'),
]

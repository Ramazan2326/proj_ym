from django.contrib import admin
from .models import AccountProvider, Provider


admin.site.register(AccountProvider)
admin.site.register(Provider)

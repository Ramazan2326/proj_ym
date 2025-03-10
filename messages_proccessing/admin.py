from django.contrib import admin
from .models import Message, Rule, Channel, ProviderChannel


admin.site.register(Rule)
admin.site.register(Channel)
admin.site.register(Message)
admin.site.register(ProviderChannel)

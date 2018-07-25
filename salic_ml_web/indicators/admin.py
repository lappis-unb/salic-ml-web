from django.contrib import admin

from .models import Indicator, Entity, Evidence, Metric

admin.site.register(Indicator)
admin.site.register(Entity)
admin.site.register(Evidence)
admin.site.register(Metric)

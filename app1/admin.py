from django.contrib import admin

# Register your models here.
# app1/admin.py
from .models import Prediction,CustomUser

admin.site.register(Prediction)
admin.site.register(CustomUser)




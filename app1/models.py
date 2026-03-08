from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

# Create your models here.
'''lass CustomUser(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='custom_user')
    email = models.EmailField(unique=True)
    

    def __str__(self):
        return self.user.username '''


class CustomUser(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='custom_user')
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=100, blank=True, null=True)
    last_name = models.CharField(max_length=100, blank=True, null=True)
    gender = models.CharField(max_length=10, choices=[('M', 'Male'), ('F', 'Female')], blank=True, null=True)
    dob = models.DateField(blank=True, null=True) # Change age to dob

    def __str__(self):
        return self.user.username




class Prediction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    n_days = models.IntegerField()
    status = models.CharField(max_length=20)
    drug = models.CharField(max_length=20)
    age = models.IntegerField()
    sex = models.CharField(max_length=10)
    ascites = models.CharField(max_length=10)
    hepatomegaly = models.CharField(max_length=10)
    spiders = models.CharField(max_length=10)
    edema = models.CharField(max_length=10)
    bilirubin = models.FloatField()
    cholesterol = models.IntegerField(blank=True, null=True) # Allowing null for fields that might be missing
    albumin = models.FloatField()
    copper = models.FloatField(blank=True, null=True)
    alk_phos = models.FloatField(blank=True, null=True)
    sgot = models.FloatField(blank=True, null=True)
    tryglicerides = models.FloatField(blank=True, null=True)
    platelets = models.FloatField()
    prothrombin = models.FloatField()
    prediction_result = models.CharField(max_length=30)
    prediction_date = models.DateTimeField(auto_now=True)

class ChatSession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_sessions')
    title = models.CharField(max_length=200, default="New Chat")
    history = models.JSONField(default=list)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.user.username} - {self.title}"

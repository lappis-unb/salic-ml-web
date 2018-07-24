from django.db import models

class Entity(models.Model):
    pronac = models.CharField(max_length=10)
    name = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class Indicator(models.Model):
    entity = models.ForeignKey(
        Entity, 
        on_delete=models.CASCADE,
        related_name='indicators')
    name = models.CharField(max_length=200)
    value = models.FloatField(default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class Metric(models.Model):
    indicator = models.ForeignKey(
        Indicator, 
        on_delete=models.CASCADE,
        related_name='metrics')
    value = models.FloatField(default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class Evidence(models.Model):
    metric = models.ForeignKey(
        Metric, 
        on_delete=models.CASCADE, 
        related_name='evidences')
    slug = models.SlugField(max_length=280)
    is_valid = models.IntegerField(default=0)
    is_invalid = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
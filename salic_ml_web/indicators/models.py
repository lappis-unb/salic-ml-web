from django.db import models

class Entity(models.Model):
    pronac = models.CharField(max_length=10)
    name = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Indicator(models.Model):
    entity = models.ForeignKey(
        Entity, 
        on_delete=models.CASCADE,
        related_name='indicators')
    name = models.CharField(max_length=200)
    value = models.FloatField(default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Metric(models.Model):
    indicator = models.ForeignKey(
        Indicator, 
        on_delete=models.CASCADE,
        related_name='metrics')
    value = models.FloatField(default=0.0)
    name = models.CharField(max_length=200, default='Metric')
    reason = models.CharField(max_length=500, default='Any reason')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Evidence(models.Model):
    metric = models.ForeignKey(
        Metric, 
        on_delete=models.CASCADE,
        related_name='evidences')
    slug = models.TextField(max_length=280)
    name = models.CharField(max_length=200, default='Evidence')
    is_valid = models.IntegerField(default=0)
    is_invalid = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class User(models.Model):
    name = models.CharField(max_length=200)
    email = models.EmailField(max_length=254)

    def __str__(self):
        return self.name

class MetricFeedback(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='metric_feedbacks'
    )
    metric = models.ForeignKey(
        Metric,
        on_delete=models.CASCADE,
        related_name='metric_feedbacks'
    )
    grade = models.IntegerField(default=1)
    reason = models.TextField(max_length=500)

class ProjectFeedback(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='entity_feedbacks'
    )
    entity = models.ForeignKey(
        Entity,
        on_delete=models.CASCADE,
        related_name='entity_feedbacks'
    )
    grade = models.IntegerField(default=1)
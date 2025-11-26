from django.db import models


class Task(models.Model):
    title = models.CharField(max_length=255)
    due_date = models.DateField(null=True, blank=True)
    estimated_hours = models.FloatField(default=0)
    importance = models.IntegerField(default=5)

    def __str__(self):
        return self.title

from django.urls import path
from .views import index, analyze_tasks, suggest_tasks

urlpatterns = [
    path("", index, name="index"),
    path("api/tasks/analyze/", analyze_tasks, name="analyze-tasks"),
    path("api/tasks/suggest/", suggest_tasks, name="suggest-tasks"),
]

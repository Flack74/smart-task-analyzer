import json
from django.http import JsonResponse, FileResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from urllib.parse import unquote
import os

from .serializers import validate_task
from .scoring import compute_scores


def index(request):
    """Serve the frontend index.html"""
    frontend_path = os.path.join(os.path.dirname(__file__), '../../frontend/index.html')
    return FileResponse(open(frontend_path, 'rb'), content_type='text/html')


@csrf_exempt
@require_http_methods(["POST"])
def analyze_tasks(request):
    """
    POST /api/tasks/analyze/
    Body: {"tasks": [...], "strategy": "smart_balance"}
    """
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    
    tasks = data.get("tasks", [])
    strategy = data.get("strategy", "smart_balance")
    
    if not isinstance(tasks, list):
        return JsonResponse({"error": "Tasks must be a list"}, status=400)
    
    if strategy not in ["smart_balance", "fastest_wins", "high_impact", "deadline_driven"]:
        return JsonResponse({"error": "Invalid strategy"}, status=400)
    
    for task in tasks:
        errors = validate_task(task)
        if errors:
            return JsonResponse({"error": errors}, status=400)
    
    scored = compute_scores(tasks, strategy)
    return JsonResponse(scored, safe=False)


@csrf_exempt
@require_http_methods(["GET"])
def suggest_tasks(request):
    """
    GET /api/tasks/suggest/?strategy=smart_balance&tasks=<urlencoded-json>
    """
    strategy = request.GET.get("strategy", "smart_balance")
    raw_tasks = request.GET.get("tasks")
    
    if not raw_tasks:
        return JsonResponse({"error": "Missing 'tasks' query parameter"}, status=400)
    
    if strategy not in ["smart_balance", "fastest_wins", "high_impact", "deadline_driven"]:
        return JsonResponse({"error": "Invalid strategy"}, status=400)
    
    try:
        decoded = unquote(raw_tasks)
        tasks_data = json.loads(decoded)
    except Exception:
        return JsonResponse({"error": "Invalid tasks JSON"}, status=400)
    
    if not isinstance(tasks_data, list):
        return JsonResponse({"error": "Tasks must be a list"}, status=400)
    
    for task in tasks_data:
        errors = validate_task(task)
        if errors:
            return JsonResponse({"error": errors}, status=400)
    
    scored = compute_scores(tasks_data, strategy)
    top3 = scored[:3]
    return JsonResponse(top3, safe=False)

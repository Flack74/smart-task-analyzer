from datetime import date, datetime
from typing import List, Dict, Any, Set


def _parse_date(value):
    if value is None:
        return None
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        return datetime.strptime(value, "%Y-%m-%d").date()
    raise ValueError("Invalid date format")


def _compute_urgency(due_date: date | None, today: date | None = None) -> float:
    """
    Returns a value roughly in [0.0, 1.5]
    Higher = more urgent.
    """
    if today is None:
        today = date.today()

    if due_date is None:
        return 0.3

    days_diff = (due_date - today).days

    if days_diff < 0:
        return 1.5
    elif days_diff == 0:
        return 1.3
    elif days_diff <= 3:
        return 1.1
    elif days_diff <= 7:
        return 0.9
    elif days_diff <= 14:
        return 0.7
    else:
        return 0.4


def _build_graph(tasks: List[Dict[str, Any]]) -> Dict[str, set]:
    graph = {}
    for t in tasks:
        tid = str(t.get("id", t.get("_internal_id")))
        deps = [str(d) for d in t.get("dependencies", [])]
        graph[tid] = set(deps)
    return graph


def _dfs_cycle(node: str, graph: Dict[str, set],
               visiting: Set[str], visited: Set[str], cycle_nodes: Set[str]):
    if node in visited:
        return
    if node in visiting:
        cycle_nodes.update(visiting)
        return
    visiting.add(node)
    for nei in graph.get(node, []):
        _dfs_cycle(nei, graph, visiting, visited, cycle_nodes)
    visiting.remove(node)
    visited.add(node)


def detect_circular_dependencies(tasks: List[Dict[str, Any]]) -> Set[str]:
    graph = _build_graph(tasks)
    visited: Set[str] = set()
    cycle_nodes: Set[str] = set()
    for node in graph.keys():
        if node not in visited:
            _dfs_cycle(node, graph, set(), visited, cycle_nodes)
    return cycle_nodes


def compute_scores(tasks: List[Dict[str, Any]], strategy: str = "smart_balance") -> List[Dict[str, Any]]:
    """
    Mutates each task dict to add:
      - score: float
      - explanation: str
    and returns the sorted list (highest score first).
    """
    for index, t in enumerate(tasks):
        if "id" not in t:
            t["_internal_id"] = f"task_{index}"

    hours_values = [t.get("estimated_hours", 0) or 0 for t in tasks]
    max_hours = max(hours_values) if hours_values else 1
    if max_hours <= 0:
        max_hours = 1

    id_to_block_count: Dict[str, int] = {}
    for t in tasks:
        tid = str(t.get("id", t.get("_internal_id")))
        id_to_block_count.setdefault(tid, 0)

    for t in tasks:
        deps = t.get("dependencies", []) or []
        for dep_id in deps:
            dep_id = str(dep_id)
            id_to_block_count[dep_id] = id_to_block_count.get(dep_id, 0) + 1

    cycle_ids = detect_circular_dependencies(tasks)

    today = date.today()

    enriched = []
    for t in tasks:
        tid = str(t.get("id", t.get("_internal_id")))
        title = t.get("title", "(no title)")

        due_raw = t.get("due_date")
        try:
            due = _parse_date(due_raw)
        except Exception:
            due = None

        importance = t.get("importance") or 0
        if importance < 1:
            importance = 1
        if importance > 10:
            importance = 10
        importance_norm = importance / 10.0

        hours = t.get("estimated_hours") or 0
        if hours < 0:
            hours = 0

        effort_norm = min(hours / max_hours, 1.0)
        quick_win = 1.0 - effort_norm

        urgency = _compute_urgency(due, today)
        urgency_norm = min(urgency / 1.5, 1.0)

        blocks = id_to_block_count.get(tid, 0)
        dependency_norm = 0.0
        if blocks > 0:
            dependency_norm = min(blocks / max(1, len(tasks) - 1), 1.0)

        in_cycle = tid in cycle_ids

        enriched.append({
            "task": t,
            "tid": tid,
            "title": title,
            "importance_norm": importance_norm,
            "urgency_norm": urgency_norm,
            "quick_win": quick_win,
            "dependency_norm": dependency_norm,
            "in_cycle": in_cycle,
        })

    for e in enriched:
        imp = e["importance_norm"]
        urg = e["urgency_norm"]
        qw = e["quick_win"]
        dep = e["dependency_norm"]
        in_cycle = e["in_cycle"]

        if strategy == "fastest_wins":
            score = qw
            reason_parts = ["Low effort / quick to complete is prioritized."]
        elif strategy == "high_impact":
            score = imp * 0.7 + urg * 0.3
            reason_parts = ["High importance is heavily prioritized, with some urgency weight."]
        elif strategy == "deadline_driven":
            score = urg
            reason_parts = ["Closer / overdue deadlines are prioritized."]
        else:
            score = imp * 0.4 + urg * 0.3 + qw * 0.15 + dep * 0.15
            reason_parts = ["Balanced importance, urgency, effort, and dependencies."]

        if dep > 0:
            reason_parts.append(f"This task blocks {round(dep * (len(tasks)-1))} other task(s).")

        if in_cycle:
            score *= 0.8
            reason_parts.append("Circular dependency detected; slightly de-prioritized.")

        e["task"]["score"] = round(float(score), 4)
        e["task"]["explanation"] = " ".join(reason_parts)

    enriched.sort(key=lambda x: x["task"]["score"], reverse=True)
    return [e["task"] for e in enriched]

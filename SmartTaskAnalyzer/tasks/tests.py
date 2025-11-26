from django.test import TestCase
from datetime import date, timedelta

from .scoring import compute_scores


class ScoringAlgorithmTests(TestCase):

    def test_overdue_task_has_higher_score_than_future_task(self):
        today = date.today()
        overdue = (today - timedelta(days=2)).isoformat()
        next_week = (today + timedelta(days=7)).isoformat()

        tasks = [
            {
                "id": "overdue",
                "title": "Overdue task",
                "due_date": overdue,
                "estimated_hours": 2,
                "importance": 5,
                "dependencies": []
            },
            {
                "id": "future",
                "title": "Future task",
                "due_date": next_week,
                "estimated_hours": 2,
                "importance": 5,
                "dependencies": []
            },
        ]

        scored = compute_scores(tasks, strategy="smart_balance")
        self.assertEqual(scored[0]["id"], "overdue")

    def test_high_impact_strategy_prioritizes_importance(self):
        today = date.today().isoformat()

        tasks = [
            {
                "id": "high_importance",
                "title": "High impact, longer",
                "due_date": today,
                "estimated_hours": 5,
                "importance": 10,
                "dependencies": []
            },
            {
                "id": "low_importance",
                "title": "Low impact, quick",
                "due_date": today,
                "estimated_hours": 1,
                "importance": 2,
                "dependencies": []
            },
        ]

        scored = compute_scores(tasks, strategy="high_impact")
        self.assertEqual(scored[0]["id"], "high_importance")

    def test_circular_dependencies_are_detected_and_penalized(self):
        today = date.today().isoformat()

        tasks = [
            {
                "id": "A",
                "title": "Task A",
                "due_date": today,
                "estimated_hours": 1,
                "importance": 8,
                "dependencies": ["B"]
            },
            {
                "id": "B",
                "title": "Task B",
                "due_date": today,
                "estimated_hours": 1,
                "importance": 8,
                "dependencies": ["A"]
            },
        ]

        scored = compute_scores(tasks, strategy="smart_balance")
        explanations = [t["explanation"] for t in scored]

        self.assertTrue(
            any("Circular dependency" in exp or "circular" in exp.lower() for exp in explanations)
        )

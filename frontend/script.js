const tasks = [];
let nextInternalId = 0;

const taskForm = document.getElementById("task-form");
const jsonInput = document.getElementById("json-input");
const loadJsonBtn = document.getElementById("load-json-btn");
const strategySelect = document.getElementById("strategy");
const analyzeBtn = document.getElementById("analyze-btn");
const suggestBtn = document.getElementById("suggest-btn");
const tasksList = document.getElementById("tasks-list");
const messageDiv = document.getElementById("message");

function renderTasks(list) {
    tasksList.innerHTML = "";
    list.forEach(task => {
        const score = task.score ?? 0;
        let priorityClass = "low";
        if (score >= 0.75) priorityClass = "high";
        else if (score >= 0.5) priorityClass = "medium";

        const card = document.createElement("div");
        card.className = `task-card ${priorityClass}`;

        card.innerHTML = `
      <div class="task-header">
        <div class="task-title">${task.title || "(no title)"}</div>
        <div class="score-badge">Score: ${score.toFixed(3)}</div>
      </div>
      <div class="task-meta">
        <div>Due: ${task.due_date || "none"}</div>
        <div>Estimated Hours: ${task.estimated_hours}</div>
        <div>Importance: ${task.importance}</div>
        <div>Dependencies: ${(task.dependencies || []).join(", ") || "none"}</div>
      </div>
      <div class="task-explanation">
        ${task.explanation || ""}
      </div>
    `;
        tasksList.appendChild(card);
    });
}

function showMessage(text, isError = false) {
    messageDiv.textContent = text;
    messageDiv.style.color = isError ? "#ff4d4f" : "#f5f5f5";
}

taskForm.addEventListener("submit", (e) => {
    e.preventDefault();

    const title = document.getElementById("title").value.trim();
    const due_date = document.getElementById("due_date").value || null;
    const estimated_hours = parseFloat(document.getElementById("estimated_hours").value);
    const importance = parseInt(document.getElementById("importance").value, 10);
    const depsRaw = document.getElementById("dependencies").value.trim();

    if (!title || isNaN(estimated_hours) || isNaN(importance)) {
        showMessage("Please fill in title, estimated hours and importance.", true);
        return;
    }

    const dependencies = depsRaw
        ? depsRaw.split(",").map(s => s.trim()).filter(Boolean)
        : [];

    const task = {
        id: `task_${nextInternalId++}`,
        title,
        due_date,
        estimated_hours,
        importance,
        dependencies
    };

    tasks.push(task);
    renderTasks(tasks);
    taskForm.reset();
    showMessage("Task added.");
});

loadJsonBtn.addEventListener("click", () => {
    const raw = jsonInput.value.trim();
    if (!raw) {
        showMessage("Please paste JSON first.", true);
        return;
    }

    try {
        const parsed = JSON.parse(raw);
        if (!Array.isArray(parsed)) {
            showMessage("JSON must be an array of tasks.", true);
            return;
        }
        tasks.length = 0;
        parsed.forEach(t => tasks.push(t));
        renderTasks(tasks);
        showMessage("Tasks loaded from JSON.");
    } catch (err) {
        console.error(err);
        showMessage("Invalid JSON.", true);
    }
});

async function callAnalyze() {
    if (!tasks.length) {
        showMessage("No tasks to analyze.", true);
        return;
    }

    const strategy = strategySelect.value;
    const payload = {
        tasks: tasks,
        strategy: strategy
    };

    showMessage("Analyzing tasks...");
    try {
        const res = await fetch("/api/tasks/analyze/", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify(payload)
        });

        if (!res.ok) {
            const errData = await res.json().catch(() => ({}));
            throw new Error(errData.error || "Server error");
        }

        const data = await res.json();
        renderTasks(data);
        showMessage(`Tasks analyzed with "${strategy}" strategy.`);
    } catch (err) {
        console.error(err);
        showMessage(err.message, true);
    }
}

async function callSuggest() {
    if (!tasks.length) {
        showMessage("No tasks to analyze.", true);
        return;
    }

    const strategy = strategySelect.value;
    const encodedTasks = encodeURIComponent(JSON.stringify(tasks));
    const url = `/api/tasks/suggest/?strategy=${strategy}&tasks=${encodedTasks}`;

    showMessage("Fetching top 3 suggestions...");
    try {
        const res = await fetch(url, {method: "GET"});

        if (!res.ok) {
            const errData = await res.json().catch(() => ({}));
            throw new Error(errData.error || "Server error");
        }

        const data = await res.json();
        renderTasks(data);
        showMessage(`Top 3 tasks to work on today (${strategy}).`);
    } catch (err) {
        console.error(err);
        showMessage(err.message, true);
    }
}

analyzeBtn.addEventListener("click", callAnalyze);
suggestBtn.addEventListener("click", callSuggest);

from flask import Flask, jsonify, redirect, render_template_string, request, url_for

app = Flask(__name__)
tasks = []
next_id = 1
PAGE = """
<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Checklist Maker</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background: #f4f4f4;
            margin: 0;
            padding: 30px 15px;
        }

        .box {
            max-width: 700px;
            margin: 0 auto;
            background: white;
            padding: 25px;
            border-radius: 12px;
            box-shadow: 0 4px 14px rgba(0, 0, 0, 0.1);
        }

        h1 {
            margin-top: 0;
            text-align: center;
        }

        .add-form {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
        }

        .add-form input {
            flex: 1;
            padding: 12px;
            font-size: 16px;
        }

        .add-form button,
        .task-actions button {
            padding: 10px 14px;
            font-size: 14px;
            border: none;
            border-radius: 6px;
            cursor: pointer;
        }

        .add-form button {
            background: #2f80ed;
            color: white;
        }

        ul {
            list-style: none;
            padding: 0;
            margin: 0;
        }

        li {
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 12px;
            border: 1px solid #ddd;
            padding: 12px;
            border-radius: 8px;
            margin-bottom: 10px;
            background: #fafafa;
        }

        .done .task-title {
            text-decoration: line-through;
            color: #777;
        }

        .task-actions {
            display: flex;
            gap: 8px;
        }

        .toggle-button {
            background: #27ae60;
            color: white;
        }

        .delete-button {
            background: #e74c3c;
            color: white;
        }

        .empty {
            text-align: center;
            color: #777;
            padding: 20px 0;
        }

        .message {
            text-align: center;
            margin-bottom: 15px;
            color: #c0392b;
        }

        @media (max-width: 600px) {
            .add-form,
            li {
                flex-direction: column;
                align-items: stretch;
            }

            .task-actions {
                width: 100%;
            }

            .task-actions form,
            .task-actions button {
                width: 100%;
            }
        }
    </style>
</head>
<body>
    <div class="box">
        <h1>Checklist Maker</h1>

        {% if error_message %}
            <div class="message">{{ error_message }}</div>
        {% endif %}

        <form class="add-form" method="post" action="{{ url_for('add_task') }}">
            <input type="text" name="title" placeholder="Enter a task" maxlength="100" required>
            <button type="submit">Add Task</button>
        </form>

        {% if tasks %}
            <ul>
                {% for task in tasks %}
                    <li class="{% if task['done'] %}done{% endif %}">
                        <span class="task-title">{{ task["title"] }}</span>

                        <div class="task-actions">
                            <form method="post" action="{{ url_for('toggle_task', task_id=task['id']) }}">
                                <button class="toggle-button" type="submit">
                                    {% if task["done"] %}Mark Pending{% else %}Mark Done{% endif %}
                                </button>
                            </form>

                            <form method="post" action="{{ url_for('delete_task', task_id=task['id']) }}">
                                <button class="delete-button" type="submit">Delete</button>
                            </form>
                        </div>
                    </li>
                {% endfor %}
            </ul>
        {% else %}
            <div class="empty">No tasks yet. Add your first task above.</div>
        {% endif %}
    </div>
</body>
</html>
"""
def get_task(task_id):
    for task in tasks:
        if task["id"] == task_id:
            return task
    return None

@app.route("/", methods=["GET"])
def index():
    return render_template_string(PAGE, tasks=tasks, error_message=request.args.get("error", ""))

@app.route("/add", methods=["POST"])
def add_task():
    global next_id

    title = request.form.get("title", "").strip()
    if not title:
        return redirect(url_for("index", error="Task title is required"))

    tasks.append(
        {
            "id": next_id,
            "title": title,
            "done": False,
        }
    )
    next_id += 1
    return redirect(url_for("index"))

@app.route("/toggle/<int:task_id>", methods=["POST"])
def toggle_task(task_id):
    task = get_task(task_id)
    if task is not None:
        task["done"] = not task["done"]
    return redirect(url_for("index"))

@app.route("/delete/<int:task_id>", methods=["POST"])
def delete_task(task_id):
    task = get_task(task_id)
    if task is not None:
        tasks.remove(task)
    return redirect(url_for("index"))

@app.route("/api/tasks", methods=["GET"])
def list_tasks():
    return jsonify(tasks)

@app.route("/api/tasks", methods=["POST"])
def api_add_task():
    global next_id

    data = request.get_json(silent=True) or {}
    title = str(data.get("title", "")).strip()
    if not title:
        return jsonify({"error": "title is required"}), 400

    task = {
        "id": next_id,
        "title": title,
        "done": False,
    }
    tasks.append(task)
    next_id += 1
    return jsonify(task), 201

@app.route("/api/tasks/<int:task_id>", methods=["PUT"])
def api_update_task(task_id):
    task = get_task(task_id)
    if task is None:
        return jsonify({"error": "task not found"}), 404

    data = request.get_json(silent=True) or {}

    if "title" in data:
        title = str(data["title"]).strip()
        if not title:
            return jsonify({"error": "title cannot be empty"}), 400
        task["title"] = title

    if "done" in data:
        task["done"] = bool(data["done"])

    return jsonify(task)

@app.route("/api/tasks/<int:task_id>", methods=["DELETE"])
def api_delete_task(task_id):
    task = get_task(task_id)
    if task is None:
        return jsonify({"error": "task not found"}), 404

    tasks.remove(task)
    return jsonify({"message": "task deleted"})

if __name__ == "__main__":
    print("Checklist app started.")
    print("Open http://127.0.0.1:5000/ in your browser.")
    print("JSON API is available at http://127.0.0.1:5000/api/tasks")
    app.run()
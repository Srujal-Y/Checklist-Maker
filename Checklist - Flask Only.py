import sqlite3
from pathlib import Path

from flask import Flask, jsonify, redirect, request


BASE_DIR = Path(__file__).resolve().parent
DATABASE_PATH = BASE_DIR / "checklist.db"

app = Flask(__name__)


def get_connection():
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_db():
    with get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                done INTEGER NOT NULL DEFAULT 0
            )
            """
        )
        connection.commit()


def parse_done_value(value):
    if isinstance(value, bool):
        return value
    if isinstance(value, int) and value in (0, 1):
        return bool(value)
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"true", "1", "yes"}:
            return True
        if normalized in {"false", "0", "no"}:
            return False
    raise ValueError("done must be a boolean value")


def serialize_task(row):
    return {
        "id": row["id"],
        "title": row["title"],
        "done": bool(row["done"]),
    }


def fetch_task(task_id):
    with get_connection() as connection:
        row = connection.execute(
            "SELECT id, title, done FROM tasks WHERE id = ?",
            (task_id,),
        ).fetchone()
    return row


@app.route("/", methods=["GET"])
def home():
    return redirect("/api/tasks")


@app.route("/api/tasks", methods=["GET"])
def list_tasks():
    with get_connection() as connection:
        rows = connection.execute(
            "SELECT id, title, done FROM tasks ORDER BY id"
        ).fetchall()
    tasks = [serialize_task(row) for row in rows]
    return jsonify({"count": len(tasks), "tasks": tasks})


@app.route("/api/tasks/<int:task_id>", methods=["GET"])
def get_task(task_id):
    row = fetch_task(task_id)
    if row is None:
        return jsonify({"error": "Task not found"}), 404
    return jsonify(serialize_task(row))


@app.route("/api/tasks", methods=["POST"])
def create_task():
    data = request.get_json(silent=True) or {}
    title = str(data.get("title", "")).strip()

    if not title:
        return jsonify({"error": "title is required"}), 400

    try:
        done = parse_done_value(data.get("done", False))
    except ValueError as error:
        return jsonify({"error": str(error)}), 400

    with get_connection() as connection:
        cursor = connection.execute(
            "INSERT INTO tasks (title, done) VALUES (?, ?)",
            (title, int(done)),
        )
        connection.commit()
        row = connection.execute(
            "SELECT id, title, done FROM tasks WHERE id = ?",
            (cursor.lastrowid,),
        ).fetchone()

    return jsonify(serialize_task(row)), 201


@app.route("/api/tasks/<int:task_id>", methods=["PUT"])
def update_task(task_id):
    existing_row = fetch_task(task_id)
    if existing_row is None:
        return jsonify({"error": "Task not found"}), 404

    data = request.get_json(silent=True) or {}

    title = existing_row["title"]
    done = bool(existing_row["done"])

    if "title" in data:
        title = str(data["title"]).strip()
        if not title:
            return jsonify({"error": "title cannot be empty"}), 400

    if "done" in data:
        try:
            done = parse_done_value(data["done"])
        except ValueError as error:
            return jsonify({"error": str(error)}), 400

    with get_connection() as connection:
        connection.execute(
            "UPDATE tasks SET title = ?, done = ? WHERE id = ?",
            (title, int(done), task_id),
        )
        connection.commit()
        updated_row = connection.execute(
            "SELECT id, title, done FROM tasks WHERE id = ?",
            (task_id,),
        ).fetchone()

    return jsonify(serialize_task(updated_row))


@app.route("/api/tasks/<int:task_id>", methods=["DELETE"])
def delete_task(task_id):
    if fetch_task(task_id) is None:
        return jsonify({"error": "Task not found"}), 404

    with get_connection() as connection:
        connection.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        connection.commit()

    return jsonify({"message": "Task deleted"})


init_db()


if __name__ == "__main__":
    print("Checklist REST API started.")
    print("Use /api/tasks for CRUD operations.")
    app.run(debug=True)

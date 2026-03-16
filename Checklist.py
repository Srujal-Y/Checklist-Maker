import json
import os
import tkinter as tk
from tkinter import ttk, messagebox


class ChecklistMaker:
    def __init__(self, root):
        self.root = root
        self.root.title("Checklist Maker")
        self.root.geometry("760x560")
        self.root.minsize(680, 500)

        self.data_file = os.path.join(os.path.dirname(__file__), "checklist_data.json")
        self.tasks = []
        self.current_filter = "All"

        self.task_text = tk.StringVar()
        self.search_text = tk.StringVar()
        self.status_text = tk.StringVar(value="0 total   0 done   0 pending")

        self.build_ui()
        self.load_tasks()
        self.refresh_list()

        self.root.bind("<Return>", self.enter_pressed)
        self.root.bind("<Delete>", self.delete_selected)
        self.root.bind("<Control-d>", self.toggle_selected_done)
        self.root.bind("<Control-D>", self.toggle_selected_done)

    def build_ui(self):
        main = ttk.Frame(self.root, padding=14)
        main.pack(fill="both", expand=True)

        top = ttk.Frame(main)
        top.pack(fill="x")

        title = ttk.Label(top, text="Checklist Maker", font=("Segoe UI", 18, "bold"))
        title.pack(side="left")

        self.count_label = ttk.Label(top, textvariable=self.status_text, font=("Segoe UI", 10))
        self.count_label.pack(side="right")

        add_row = ttk.Frame(main)
        add_row.pack(fill="x", pady=(14, 8))

        self.task_entry = ttk.Entry(add_row, textvariable=self.task_text, font=("Segoe UI", 11))
        self.task_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.task_entry.focus_set()

        add_btn = ttk.Button(add_row, text="Add Task", command=self.add_task)
        add_btn.pack(side="left")

        middle = ttk.Frame(main)
        middle.pack(fill="x", pady=(2, 10))

        search_label = ttk.Label(middle, text="Search")
        search_label.pack(side="left")

        search_entry = ttk.Entry(middle, textvariable=self.search_text, width=28)
        search_entry.pack(side="left", padx=(8, 16))
        search_entry.bind("<KeyRelease>", lambda event: self.refresh_list())

        filter_label = ttk.Label(middle, text="Show")
        filter_label.pack(side="left")

        self.filter_box = ttk.Combobox(
            middle,
            values=["All", "Pending", "Done"],
            state="readonly",
            width=10
        )
        self.filter_box.current(0)
        self.filter_box.pack(side="left", padx=(8, 0))
        self.filter_box.bind("<<ComboboxSelected>>", self.change_filter)

        list_frame = ttk.Frame(main)
        list_frame.pack(fill="both", expand=True)

        columns = ("done", "task")
        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings", selectmode="browse")
        self.tree.heading("done", text="Status")
        self.tree.heading("task", text="Task")
        self.tree.column("done", width=110, anchor="center", stretch=False)
        self.tree.column("task", anchor="w")

        y_scroll = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=y_scroll.set)

        self.tree.pack(side="left", fill="both", expand=True)
        y_scroll.pack(side="right", fill="y")

        self.tree.bind("<Double-1>", lambda event: self.toggle_done())
        self.tree.bind("<ButtonRelease-1>", self.update_button_state)

        action_row = ttk.Frame(main)
        action_row.pack(fill="x", pady=(10, 0))

        self.done_btn = ttk.Button(action_row, text="Toggle Done", command=self.toggle_done)
        self.done_btn.pack(side="left")

        self.edit_btn = ttk.Button(action_row, text="Edit Task", command=self.edit_task)
        self.edit_btn.pack(side="left", padx=8)

        self.delete_btn = ttk.Button(action_row, text="Delete Task", command=self.delete_task)
        self.delete_btn.pack(side="left")

        clear_done_btn = ttk.Button(action_row, text="Clear Completed", command=self.clear_completed)
        clear_done_btn.pack(side="right")

        clear_all_btn = ttk.Button(action_row, text="Clear All", command=self.clear_all)
        clear_all_btn.pack(side="right", padx=(0, 8))

        bottom = ttk.Label(
            main,
            text="Enter = add task   Double-click = mark done   Delete = remove selected   Ctrl+D = toggle selected",
            font=("Segoe UI", 9)
        )
        bottom.pack(fill="x", pady=(10, 0))

        self.update_button_state()

    def load_tasks(self):
        if not os.path.exists(self.data_file):
            self.tasks = []
            return

        try:
            with open(self.data_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    cleaned = []
                    for item in data:
                        if isinstance(item, dict):
                            task_id = item.get("id")
                            text = str(item.get("text", "")).strip()
                            done = bool(item.get("done", False))
                            if task_id is not None and text:
                                cleaned.append({"id": task_id, "text": text, "done": done})
                    self.tasks = cleaned
                else:
                    self.tasks = []
        except Exception:
            self.tasks = []

    def save_tasks(self):
        with open(self.data_file, "w", encoding="utf-8") as f:
            json.dump(self.tasks, f, indent=2, ensure_ascii=False)

    def next_id(self):
        if not self.tasks:
            return 1
        return max(item["id"] for item in self.tasks) + 1

    def change_filter(self, event=None):
        self.current_filter = self.filter_box.get()
        self.refresh_list()

    def match_filter(self, item):
        if self.current_filter == "Pending":
            return not item["done"]
        if self.current_filter == "Done":
            return item["done"]
        return True

    def match_search(self, item):
        query = self.search_text.get().strip().lower()
        if not query:
            return True
        return query in item["text"].lower()

    def visible_tasks(self):
        visible = []
        for item in self.tasks:
            if self.match_filter(item) and self.match_search(item):
                visible.append(item)
        visible.sort(key=lambda x: (x["done"], x["text"].lower(), x["id"]))
        return visible

    def refresh_list(self):
        selected_id = self.selected_task_id()

        for row in self.tree.get_children():
            self.tree.delete(row)

        for item in self.visible_tasks():
            status = "Done" if item["done"] else "Pending"
            self.tree.insert("", "end", iid=str(item["id"]), values=(status, item["text"]))

        if selected_id is not None and self.tree.exists(str(selected_id)):
            self.tree.selection_set(str(selected_id))
            self.tree.focus(str(selected_id))

        total = len(self.tasks)
        done_count = len([x for x in self.tasks if x["done"]])
        pending_count = total - done_count
        self.status_text.set(f"{total} total   {done_count} done   {pending_count} pending")

        self.update_button_state()

    def selected_task_id(self):
        picked = self.tree.selection()
        if not picked:
            return None
        try:
            return int(picked[0])
        except Exception:
            return None

    def get_task_by_id(self, task_id):
        for item in self.tasks:
            if item["id"] == task_id:
                return item
        return None

    def update_button_state(self, event=None):
        state = "normal" if self.selected_task_id() is not None else "disabled"
        self.done_btn.config(state=state)
        self.edit_btn.config(state=state)
        self.delete_btn.config(state=state)

    def enter_pressed(self, event=None):
        widget = self.root.focus_get()
        if widget == self.task_entry:
            self.add_task()

    def add_task(self):
        text = self.task_text.get().strip()
        if not text:
            messagebox.showwarning("Missing task", "Please type a task first.")
            return

        new_task = {
            "id": self.next_id(),
            "text": text,
            "done": False
        }
        self.tasks.append(new_task)
        self.task_text.set("")
        self.save_tasks()
        self.refresh_list()
        self.task_entry.focus_set()

    def toggle_done(self):
        task_id = self.selected_task_id()
        if task_id is None:
            return

        item = self.get_task_by_id(task_id)
        if item is None:
            return

        item["done"] = not item["done"]
        self.save_tasks()
        self.refresh_list()

    def edit_task(self):
        task_id = self.selected_task_id()
        if task_id is None:
            return

        item = self.get_task_by_id(task_id)
        if item is None:
            return

        edit_win = tk.Toplevel(self.root)
        edit_win.title("Edit Task")
        edit_win.geometry("420x120")
        edit_win.resizable(False, False)
        edit_win.transient(self.root)
        edit_win.grab_set()

        box = ttk.Frame(edit_win, padding=12)
        box.pack(fill="both", expand=True)

        ttk.Label(box, text="Task name").pack(anchor="w")

        text_var = tk.StringVar(value=item["text"])
        entry = ttk.Entry(box, textvariable=text_var, font=("Segoe UI", 11))
        entry.pack(fill="x", pady=(6, 10))
        entry.focus_set()
        entry.select_range(0, "end")

        btns = ttk.Frame(box)
        btns.pack(fill="x")

        def save_edit(event=None):
            new_text = text_var.get().strip()
            if not new_text:
                messagebox.showwarning("Missing task", "Task name cannot be empty.", parent=edit_win)
                return
            item["text"] = new_text
            self.save_tasks()
            self.refresh_list()
            edit_win.destroy()

        def cancel_edit():
            edit_win.destroy()

        ttk.Button(btns, text="Save", command=save_edit).pack(side="left")
        ttk.Button(btns, text="Cancel", command=cancel_edit).pack(side="left", padx=8)

        edit_win.bind("<Return>", save_edit)
        edit_win.bind("<Escape>", lambda event: cancel_edit())

    def delete_task(self):
        task_id = self.selected_task_id()
        if task_id is None:
            return

        item = self.get_task_by_id(task_id)
        if item is None:
            return

        ok = messagebox.askyesno("Delete task", f"Delete this task?\n\n{item['text']}")
        if not ok:
            return

        self.tasks = [x for x in self.tasks if x["id"] != task_id]
        self.save_tasks()
        self.refresh_list()

    def clear_completed(self):
        done_count = len([x for x in self.tasks if x["done"]])
        if done_count == 0:
            messagebox.showinfo("Nothing to clear", "There are no completed tasks.")
            return

        ok = messagebox.askyesno("Clear completed", f"Remove {done_count} completed task(s)?")
        if not ok:
            return

        self.tasks = [x for x in self.tasks if not x["done"]]
        self.save_tasks()
        self.refresh_list()

    def clear_all(self):
        if not self.tasks:
            messagebox.showinfo("Nothing to clear", "Your checklist is already empty.")
            return

        ok = messagebox.askyesno("Clear all", "Delete all tasks from the checklist?")
        if not ok:
            return

        self.tasks = []
        self.save_tasks()
        self.refresh_list()

    def delete_selected(self, event=None):
        self.delete_task()

    def toggle_selected_done(self, event=None):
        self.toggle_done()


def main():
    root = tk.Tk()
    try:
        ttk.Style().theme_use("clam")
    except Exception:
        pass
    ChecklistMaker(root)
    root.mainloop()


if __name__ == "__main__":
    main()
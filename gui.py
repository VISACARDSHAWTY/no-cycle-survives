import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from tkinter import messagebox
from tkinter.scrolledtext import ScrolledText
import os
from recoverability import analyze_schedule
from visualization import visualize_precedence_graph


class ScheduleAnalyzer:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Schedule Analyzer")
        self.root.geometry("1180x820")
        self.root.configure(bg="#f5f6f5")

        self.editors = {}
        self.current_pg = None

        # Menu Bar
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New Schedule", command=self.new_schedule)
        file_menu.add_command(label="Open Files...", command=self.open_files)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)

        # Style
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TNotebook", background="#f5f6f5")
        style.configure("TNotebook.Tab", padding=[12, 6], font=("Segoe UI", 11))
        style.map("TNotebook.Tab",
                  background=[("selected", "#4a90e2"), ("!selected", "#e0e0e0")],
                  foreground=[("selected", "white"), ("!selected", "black")])

        main_pane = ttk.PanedWindow(self.root, orient=tk.VERTICAL)
        main_pane.pack(fill="both", expand=True)

        top_frame = ttk.Frame(main_pane)
        main_pane.add(top_frame, weight=5)

        self.schedule_notebook = ttk.Notebook(top_frame)
        self.schedule_notebook.pack(fill="both", expand=True, padx=10, pady=(10, 5))

        bottom_frame = ttk.Frame(main_pane)
        main_pane.add(bottom_frame, weight=4)

        result_notebook = ttk.Notebook(bottom_frame)
        result_notebook.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self.tab_serial   = self._create_serial_tab(result_notebook)
        self.tab_recover  = self._create_result_tab(result_notebook, "Recoverability")
        self.tab_aca      = self._create_result_tab(result_notebook, "ACA")
        self.tab_strict   = self._create_result_tab(result_notebook, "Strict")
        self.tab_rigorous = self._create_result_tab(result_notebook, "Rigorous")
        self.tab_logs = self._create_result_tab(result_notebook, "Execution Logs")

        if os.path.exists("operations.txt"):
            self.load_file("operations.txt")
        else:
            self.new_schedule()

        self.root.after(50, self.root.update_idletasks)

    def _create_result_tab(self, notebook, title):
        frame = ttk.Frame(notebook)
        notebook.add(frame, text=title)

        ttk.Label(frame, text=title, font=("Segoe UI", 14, "bold"), foreground="#2c3e50").pack(pady=(15, 8))

        text = ScrolledText(frame, wrap=tk.WORD, font=("Consolas", 11), bg="#fdfdfd")
        text.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        text.config(state="disabled")
        return text

    def _create_serial_tab(self, notebook):
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="Serializability")

        frame.grid_rowconfigure(1, weight=1)
        frame.grid_columnconfigure(0, weight=1)

        ttk.Label(frame, text="Serializability (Conflict)", font=("Segoe UI", 14, "bold"), foreground="#2c3e50").grid(row=0, column=0, sticky="w", padx=15, pady=(15, 8))

        self.serial_text = ScrolledText(frame, wrap=tk.WORD, font=("Consolas", 11), bg="#fdfdfd")
        self.serial_text.grid(row=1, column=0, sticky="nsew", padx=15, pady=(0, 8))
        self.serial_text.config(state="disabled")

        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=2, column=0, sticky="ew", padx=15, pady=10)

        ttk.Button(btn_frame, text="Show Precedence Graph Visualization", 
                   command=self.show_graph).pack(pady=5, fill="x")

        return self.serial_text

    def _set_result_text(self, widget, content, tag_color=None):
        widget.config(state="normal")
        widget.delete("1.0", tk.END)
        widget.insert("1.0", content.strip() + "\n")
        if tag_color:
            widget.tag_configure("status", foreground=tag_color, font=("Segoe UI", 12, "bold"))
            widget.tag_add("status", "1.0", "2.0")
        widget.config(state="disabled")

    def _format_status(self, status):
        if status == "pass": return "✓ PASSED", "#27ae60"
        if status == "fail": return "✗ FAILED", "#e74c3c"
        return "?", "#7f8c8d"

    def show_graph(self):
        if not self.current_pg or len(self.current_pg) == 0:
            messagebox.showwarning("No Graph Yet", "Please click 'Analyze' first.\n\n")
            return
        try:
            visualize_precedence_graph(self.current_pg)
        except Exception as e:
            messagebox.showerror("Graph Error", str(e))

    def analyze(self, frame=None):
        if frame is None:
            tab_id = self.schedule_notebook.select()
            if not tab_id: return
            frame = self.schedule_notebook.nametowidget(tab_id)

        editor = self.editors.get(frame)
        if not editor: return

        content = editor.get("1.0", tk.END).strip()
        if not content.strip():
            messagebox.showwarning("Empty", "Please enter a schedule first.")
            return

        result = analyze_schedule(content)
        trace_list = result.get("execution_trace", [])
        self._set_result_text(self.tab_logs, "\n".join(trace_list))
        if result.get("error"):
            msg = f"PARSE ERROR\n{'═'*60}\n\n{result['error']}"
            for w in [self.serial_text, self.tab_recover, self.tab_aca, self.tab_strict, self.tab_rigorous]:
                self._set_result_text(w, msg)
            return

        self.current_pg = result.get("precedence_graph", {})

        s = result["serializability"]
        stat_txt, color = self._format_status(s["status"])
        txt = f"{stat_txt}\n\n{s['cycle']}\n\nPrecedence Graph (text view):\n{'─'*50}\n{s['graph'] or '(no edges)'}"
        self._set_result_text(self.serial_text, txt, color)

        for key, widget in [
            ("recoverability", self.tab_recover),
            ("aca", self.tab_aca),
            ("strict", self.tab_strict),
            ("rigorous", self.tab_rigorous)
        ]:
            data = result[key]
            stat_txt, color = self._format_status(data["status"])
            txt = f"{stat_txt}\n\n{data.get('message', '—')}"
            self._set_result_text(widget, txt, color)

        self.serial_text.focus_set()

    def open_files(self):
        files = filedialog.askopenfilenames(filetypes=[("Text files", "*.txt")])
        for path in files:
            try:
                with open(path, encoding="utf-8") as f:
                    content = f.read()
                self._add_editor_tab(os.path.basename(path), content)
            except Exception as e:
                messagebox.showerror("Error", str(e))

    def new_schedule(self):
        count = sum(1 for t in self.schedule_notebook.tabs() if "Untitled" in self.schedule_notebook.tab(t, "text"))
        name = f"Untitled {count+1}.txt"
        template = """START(1)
START(2)
WRITE(1,X)
READ(2,X)
COMMIT(1)
COMMIT(2)
"""
        self._add_editor_tab(name, template)

    def load_file(self, path):
        try:
            with open(path, encoding="utf-8") as f:
                content = f.read()
            self._add_editor_tab(os.path.basename(path), content)
        except:
            self.new_schedule()

    def _add_editor_tab(self, name, content):
        frame = ttk.Frame(self.schedule_notebook)
        self.schedule_notebook.add(frame, text=name)

        frame.grid_rowconfigure(1, weight=1)
        frame.grid_columnconfigure(0, weight=1)

        ttk.Label(frame, text=f"Schedule: {name}", font=("Segoe UI", 12)).grid(row=0, column=0, sticky="w", padx=12, pady=(12, 6))

        editor = ScrolledText(frame, wrap=tk.WORD, font=("Consolas", 11), undo=True, bg="#fdfdfd")
        editor.insert("1.0", content)
        editor.grid(row=1, column=0, sticky="nsew", padx=12, pady=(0, 8))

        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=2, column=0, sticky="ew", padx=12, pady=10)

        ttk.Button(btn_frame, text="Analyze", command=lambda f=frame: self.analyze(f)).grid(row=0, column=0, padx=6, sticky="w")
        ttk.Button(btn_frame, text="Save As…", command=lambda f=frame: self._save_tab(f)).grid(row=0, column=1, padx=6)
        ttk.Button(btn_frame, text="Close", command=lambda f=frame: self._close_tab(f)).grid(row=0, column=2, padx=6, sticky="e")

        self.editors[frame] = editor
        self.schedule_notebook.select(frame)
        frame.update_idletasks()
        self.root.update_idletasks()

    def _save_tab(self, frame):
        editor = self.editors.get(frame)
        if not editor: return
        content = editor.get("1.0", tk.END)
        path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt")])
        if path:
            try:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(content)
                self.schedule_notebook.tab(frame, text=os.path.basename(path))
            except Exception as e:
                messagebox.showerror("Save Error", str(e))

    def _close_tab(self, frame):
        if messagebox.askyesno("Close Tab", "Close this tab?"):
            if frame in self.editors:
                del self.editors[frame]
            self.schedule_notebook.forget(frame)

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = ScheduleAnalyzer()
    app.run()
# gui.py  (revised 2025-03-xx version)
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from tkinter import messagebox
from tkinter.scrolledtext import ScrolledText
import os
from recoverability import analyze_schedule

class ScheduleAnalyzer:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Schedule Analyzer")
        self.root.geometry("1240x860")
        self.root.configure(bg="#f8f9fa")

        self.editors = {}           # frame → editor widget
        self.current_content = ""

        # ── Style ────────────────────────────────────────
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TNotebook", background="#f8f9fa", borderwidth=0)
        style.configure("TNotebook.Tab", padding=[14, 8], font=("Helvetica", 11))
        style.map("TNotebook.Tab",
                  background=[("selected", "#d0d8e0"), ("!selected", "#e8ecef")],
                  foreground=[("selected", "#2c3e50"), ("!selected", "#5a6a7a")])

        style.configure("TLabel", background="#f8f9fa")
        style.configure("Header.TLabel", font=("Helvetica", 15, "bold"), foreground="#2c3e50")

        # ── Layout ───────────────────────────────────────
        main_pane = ttk.PanedWindow(self.root, orient=tk.VERTICAL)
        main_pane.pack(fill="both", expand=True)

        # Top: editors
        top_frame = ttk.Frame(main_pane)
        main_pane.add(top_frame, weight=5)

        self.schedule_notebook = ttk.Notebook(top_frame)
        self.schedule_notebook.pack(fill="both", expand=True, padx=12, pady=(12, 6))

        # Bottom: results
        bottom_frame = ttk.Frame(main_pane)
        main_pane.add(bottom_frame, weight=4)

        result_notebook = ttk.Notebook(bottom_frame)
        result_notebook.pack(fill="both", expand=True, padx=12, pady=(6, 12))

        # Result tabs (order: Console first, then properties, then dependencies)
        self.tab_console     = self._create_result_tab(result_notebook, "Console / Full Report")
        self.tab_serial      = self._create_result_tab(result_notebook, "Serializability")
        self.tab_recover     = self._create_result_tab(result_notebook, "Recoverability")
        self.tab_aca         = self._create_result_tab(result_notebook, "ACA")
        self.tab_strict      = self._create_result_tab(result_notebook, "Strict")
        self.tab_rigorous    = self._create_result_tab(result_notebook, "Rigorous")
        self.tab_deps        = self._create_result_tab(result_notebook, "Dependencies")     # new

        # ── Menu ─────────────────────────────────────────
        menubar = tk.Menu(self.root)
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Open Schedule(s)…", command=self.open_files)
        file_menu.add_command(label="New Schedule", command=self.new_schedule)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        menubar.add_cascade(label="File", menu=file_menu)

        analyze_menu = tk.Menu(menubar, tearoff=0)
        analyze_menu.add_command(label="Analyze Current", command=self.analyze)
        menubar.add_cascade(label="Analyze", menu=analyze_menu)

        self.root.config(menu=menubar)

        # Startup
        if os.path.exists("operations.txt"):
            self.load_file("operations.txt")
        else:
            self.new_schedule()

    def _create_result_tab(self, notebook, title):
        frame = ttk.Frame(notebook)
        notebook.add(frame, text=title)

        lbl = ttk.Label(frame, text=title, style="Header.TLabel")
        lbl.pack(pady=(18, 10))

        text = ScrolledText(frame, wrap=tk.WORD, font=("Consolas", 11), bg="#ffffff", relief="flat", bd=1,
                            insertbackground="#444")
        text.pack(fill="both", expand=True, padx=16, pady=(0, 16))
        text.config(state="disabled")
        return text

    def _set_result_text(self, widget, content, tag_color=None):
        widget.config(state="normal")
        widget.delete("1.0", tk.END)
        widget.insert("1.0", content.strip() + "\n")

        if tag_color:
            widget.tag_configure("status", foreground=tag_color, font=("Helvetica", 13, "bold"))
            widget.tag_add("status", "1.0", "2.0")

        widget.see("1.0")
        widget.config(state="disabled")

    def _format_status(self, status):
        if status == "pass": return "✓ PASSED",  "#2e7d32"
        if status == "fail": return "✗ FAILED",  "#c62828"
        return "– UNKNOWN", "#757575"

    def analyze(self, frame=None):
        if frame is None:
            tab_id = self.schedule_notebook.select()
            if not tab_id: return
            frame = self.schedule_notebook.nametowidget(tab_id)

        editor = self.editors.get(frame)
        if not editor: return

        content = editor.get("1.0", tk.END).strip()
        if not content.strip():
            messagebox.showwarning("Empty", "Nothing to analyze.")
            return

        self.current_content = content
        res = analyze_schedule(content)

        # ── Console / Full Report ────────────────────────
        if res.get("error"):
            report = f"PARSE ERROR\n{'═'*50}\n\n{res['error']}\n"
            self._set_result_text(self.tab_console, report, "#c62828")
            for t in [self.tab_serial, self.tab_recover, self.tab_aca, self.tab_strict, self.tab_rigorous, self.tab_deps]:
                self._set_result_text(t, "— parse error —")
            return

        lines = []

        # Summary block
        lines.append("SCHEDULE ANALYSIS SUMMARY")
        lines.append("═"*50 + "\n")

        for key, title in [
            ("serializability", "Conflict Serializability"),
            ("recoverability",  "Recoverability"),
            ("aca",             "ACA (Avoid Cascading Aborts)"),
            ("strict",          "Strict"),
            ("rigorous",        "Rigorous")
        ]:
            data = res[key]
            stat, color = self._format_status(data["status"])
            lines.append(f"[{title}]  {stat}")
            if data.get("cycle"): lines.append(f"  {data['cycle']}")
            if data.get("message"): lines.append(f"  {data['message']}")
            lines.append("")

        lines.append("═"*50 + "\n")

        self._set_result_text(self.tab_console, "\n".join(lines))

        # ── Individual property tabs ─────────────────────
        s = res["serializability"]
        stat_txt, color = self._format_status(s["status"])
        txt = f"{stat_txt}\n\n{s.get('cycle', '')}\n\nPrecedence Graph:\n{'─'*40}\n{s['graph'] or '(empty)'}"
        self._set_result_text(self.tab_serial, txt, color)

        for key, widget in [
            ("recoverability", self.tab_recover),
            ("aca", self.tab_aca),
            ("strict", self.tab_strict),
            ("rigorous", self.tab_rigorous)
        ]:
            data = res[key]
            stat_txt, color = self._format_status(data["status"])
            txt = f"{stat_txt}\n\n{data.get('message', '—')}"
            self._set_result_text(widget, txt, color)

        # ── Dependencies tab ─────────────────────────────
        deps_lines = ["DEPENDENCIES & INDICES", "═"*50, ""]

        if res["read_from"]:
            deps_lines.append("Read-from (rf):")
            for r, w, v, i in res["read_from"]:
                deps_lines.append(f"  T{r} reads {v} ← written by T{w}  (op {i})")
            deps_lines.append("")

        if res["write_after"]:
            deps_lines.append("Write-after / overwrites:")
            for w, pw, v, i in res["write_after"]:
                deps_lines.append(f"  T{w} overwrites {v} previously written by T{pw}  (op {i})")
            deps_lines.append("")

        if res["access_after"]:
            deps_lines.append("Access-after:")
            for t, pt, v, i in res["access_after"]:
                deps_lines.append(f"  T{t} accesses {v} after previous access by T{pt}  (op {i})")
            deps_lines.append("")

        if res["commit_indices"]:
            deps_lines.append("Commit / Finish positions:")
            for tx, idx in sorted(res["commit_indices"].items()):
                deps_lines.append(f"  T{tx} finishes at operation {idx}")

        if len(deps_lines) <= 3:
            deps_lines.append("No detected read/write/access dependencies.")

        self._set_result_text(self.tab_deps, "\n".join(deps_lines))

        # Focus console by default after analysis
        self.tab_console.focus_set()

    # ── The rest stays almost the same ──────────────────────────────────────

    def open_files(self):
        files = filedialog.askopenfilenames(filetypes=[("Text files", "*.txt"), ("All", "*.*")])
        for path in files:
            try:
                with open(path, encoding="utf-8") as f:
                    content = f.read()
                name = os.path.basename(path)
                self._add_editor_tab(name, content)
            except Exception as e:
                messagebox.showerror("Open failed", f"{path}\n{e}")

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
            name = os.path.basename(path)
            self._add_editor_tab(name, content)
        except:
            self.new_schedule()

    def _add_editor_tab(self, name, content):
        frame = ttk.Frame(self.schedule_notebook)
        self.schedule_notebook.add(frame, text=name)

        lbl = ttk.Label(frame, text=f"Editing: {name}", font=("Helvetica", 12))
        lbl.pack(pady=(12, 6))

        editor = ScrolledText(frame, wrap=tk.WORD, font=("Consolas", 11), undo=True, bg="#fdfdfd")
        editor.insert("1.0", content)
        editor.pack(fill="both", expand=True, padx=14, pady=(0, 10))

        btn_frame = ttk.Frame(frame)
        btn_frame.pack(pady=10)

        ttk.Button(btn_frame, text="Analyze", command=lambda f=frame: self.analyze(f)).pack(side="left", padx=8)
        ttk.Button(btn_frame, text="Save As…", command=lambda f=frame: self._save_tab(f)).pack(side="left", padx=8)
        ttk.Button(btn_frame, text="Close", command=lambda f=frame: self._close_tab(f)).pack(side="left", padx=8)

        self.editors[frame] = editor
        self.schedule_notebook.select(frame)

    def _save_tab(self, frame):
        editor = self.editors.get(frame)
        if not editor: return
        content = editor.get("1.0", tk.END)

        path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt")])
        if path:
            try:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(content)
                new_name = os.path.basename(path)
                self.schedule_notebook.tab(frame, text=new_name)
            except Exception as e:
                messagebox.showerror("Save failed", str(e))

    def _close_tab(self, frame):
        if messagebox.askyesno("Close", "Close this tab?"):
            if frame in self.editors:
                del self.editors[frame]
            self.schedule_notebook.forget(frame)

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = ScheduleAnalyzer()
    app.run()
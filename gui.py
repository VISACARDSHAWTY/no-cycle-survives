# gui.py
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from tkinter import messagebox
from tkinter.scrolledtext import ScrolledText
import os
from recoverability import perform_analysis


class ScheduleAnalyzer:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Transaction Schedule Analyzer")
        self.root.geometry("1100x800")
        self.tab_data = {}  # tab -> {"filename": str, "text_widget": ScrolledText}

        # Tabs for schedules
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=5)

        # Results area (shared, updates on Analyze)
        results_frame = ttk.Frame(self.root)
        results_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        ttk.Label(results_frame, text="Analysis Results", font=("Arial", 12, "bold")).pack(anchor="w")
        self.results_text = ScrolledText(results_frame, height=16, state="disabled", wrap=tk.WORD)
        self.results_text.pack(fill="both", expand=True)

        # Menu
        menubar = tk.Menu(self.root)
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Open Schedule(s)...", command=self.open_schedules)
        file_menu.add_command(label="New Schedule", command=self.new_schedule)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        menubar.add_cascade(label="File", menu=file_menu)
        self.root.config(menu=menubar)

        # Start with the example file if it exists, otherwise a new one
        if os.path.exists("operations.txt"):
            self.load_initial_example()
        else:
            self.new_schedule()

        self.notebook.bind("<<NotebookTabChanged>>", lambda e: None)  # optional

    def create_tab(self, display_name: str, content: str):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text=display_name)

        ttk.Label(tab, text=f"Schedule: {display_name}", font=("Arial", 10, "bold")).pack(pady=(5, 0))
        
        text_widget = ScrolledText(tab, wrap=tk.WORD, height=18, undo=True)
        text_widget.pack(fill="both", expand=True, padx=10, pady=5)
        text_widget.insert("1.0", content)

        btn_frame = ttk.Frame(tab)
        btn_frame.pack(pady=8)
        ttk.Button(btn_frame, text="Analyze", command=lambda t=tab: self.analyze_current(t)).pack(side="left", padx=8)
        ttk.Button(btn_frame, text="Save As...", command=lambda t=tab: self.save_as(t)).pack(side="left", padx=8)

        self.tab_data[tab] = {"filename": display_name, "text_widget": text_widget}

    def load_initial_example(self):
        try:
            with open("operations.txt", "r", encoding="utf-8") as f:
                content = f.read()
            self.create_tab("operations.txt", content)
        except:
            self.new_schedule()

    def open_schedules(self):
        files = filedialog.askopenfilenames(
            title="Select one or more schedule files",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        for path in files:
            try:
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                name = os.path.basename(path)
                self.create_tab(name, content)
                self.notebook.select(len(self.notebook.tabs()) - 1)
            except Exception as e:
                messagebox.showerror("Open Error", f"Could not open {path}\n{e}")

    def new_schedule(self):
        # Avoid duplicate Untitled names
        count = sum(1 for v in self.tab_data.values() if v["filename"].startswith("Untitled"))
        name = f"Untitled{count + 1}.txt"
        template = """# Transaction Schedule
# Lines starting with # are comments and ignored

START(1)
START(2)
WRITE(1,X)
COMMIT(1)
"""
        self.create_tab(name, template)
        self.notebook.select(len(self.notebook.tabs()) - 1)

    def analyze_current(self, tab):
        if tab not in self.tab_data:
            return
        text_widget = self.tab_data[tab]["text_widget"]
        content = text_widget.get("1.0", tk.END).strip()

        if not content:
            messagebox.showwarning("Empty Schedule", "Please enter some operations first.")
            return

        try:
            analysis_output = perform_analysis(content)
            self.results_text.config(state="normal")
            self.results_text.delete("1.0", tk.END)
            self.results_text.insert("1.0", analysis_output)
            self.results_text.config(state="disabled")
        except Exception as e:
            messagebox.showerror("Analysis Error", str(e))

    def save_as(self, tab):
        if tab not in self.tab_data:
            return
        text_widget = self.tab_data[tab]["text_widget"]
        content = text_widget.get("1.0", tk.END)

        filepath = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            title="Save schedule as..."
        )
        if filepath:
            try:
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(content)
                new_name = os.path.basename(filepath)
                self.notebook.tab(tab, text=new_name)
                self.tab_data[tab]["filename"] = new_name
                messagebox.showinfo("Saved", f"Saved successfully to:\n{filepath}")
            except Exception as e:
                messagebox.showerror("Save Error", str(e))

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = ScheduleAnalyzer()
    app.run()
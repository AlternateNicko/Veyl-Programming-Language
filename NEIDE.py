import json
import os
import re
import subprocess
import sys
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk


class AutoComplete:
    def __init__(self, text, words):
        self.text = text
        self.words = sorted(set(words))
        self.visible = False

        self.listbox = tk.Listbox(
            text.master,
            height=6,
            bg="#111111",
            fg="white",
            selectbackground="#007acc",
            relief="solid",
            borderwidth=1,
            highlightthickness=0,
        )

        self.text.bind(
            "<KeyRelease>",
            lambda e: self.text.after_idle(self.update, e),
            add="+",
        )
        self.text.bind("<Down>", self.move_down)
        self.text.bind("<Up>", self.move_up)
        self.text.bind("<Return>", self.complete)
        self.text.bind("<Tab>", self.complete)
        self.text.bind("<BackSpace>", lambda e: self.text.after_idle(self.update), add="+")
        self.text.bind("<Delete>", lambda e: self.text.after_idle(self.update), add="+")

    def current_word(self):
        line = self.text.get("insert linestart", "insert")
        match = re.search(r"[A-Za-z_][A-Za-z0-9_]*$", line)
        return match.group(0) if match else ""

    def update(self, event=None):
        if event and event.keysym in ("Up", "Down", "Left", "Right", "Return", "Tab", "Escape"):
            return

        word = self.current_word()
        if not word:
            self.hide()
            return

        matches = sorted(
            w for w in self.words
            if w.lower().startswith(word.lower()) and w != word
        )

        self.listbox.delete(0, tk.END)

        if not matches:
            self.hide()
            return

        for match in matches[:10]:
            self.listbox.insert(tk.END, match)

        bbox = self.text.bbox("insert")
        if bbox is None:
            self.hide()
            return

        x, y, w, h = bbox
        x += self.text.winfo_x()
        y += self.text.winfo_y()

        self.listbox.place(x=x, y=y + h, width=220)
        self.visible = True

        self.listbox.selection_clear(0, tk.END)
        self.listbox.selection_set(0)
        self.listbox.activate(0)

    def hide(self):
        self.listbox.place_forget()
        self.visible = False

    def complete(self, event=None):
        if not self.visible:
            return

        word = self.current_word()
        if not word:
            return

        choice = self.listbox.get(tk.ACTIVE)

        self.text.delete(f"insert-{len(word)}c", "insert")
        self.text.insert("insert", choice)

        self.hide()
        return "break"

    def move_down(self, event):
        if not self.visible:
            return

        current = self.listbox.curselection()
        if current:
            i = min(current[0] + 1, self.listbox.size() - 1)
        else:
            i = 0

        self.listbox.selection_clear(0, tk.END)
        self.listbox.selection_set(i)
        self.listbox.activate(i)
        return "break"

    def move_up(self, event):
        if not self.visible:
            return

        current = self.listbox.curselection()
        if current:
            i = max(current[0] - 1, 0)
        else:
            i = 0

        self.listbox.selection_clear(0, tk.END)
        self.listbox.selection_set(i)
        self.listbox.activate(i)
        return "break"


class CustomHighlighter:
    def __init__(self, text_widget):
        self.text = text_widget

        self.keywords = [
            "while", "for", "public", "private", "func", "class", "load", "rename",
            "inherit", "with", "from", "if", "else", "open", "sync", "desync",
            "attempt", "catch", "in", "ignore", "break", "continue", "import", "get",
            "and", "is", "as", "not", "or", "global", "return", "True", "False", "None",
        ]

        self.builtins = [
            "output", "quit", "num", "input", "eval", "exec", "length", "sort",
            "min", "mean", "max", "median", "mode", "sum", "range", "reverse",
            "type", "format", "zip", "dict", "map",
        ]

        keyword_group = "|".join(map(re.escape, self.keywords))
        builtin_group = "|".join(map(re.escape, self.builtins))

        pattern = (
            r"(?P<comment>//[^\n]*|#[^\n]*)"
            r"|(?P<string>\"(?:\\\\.|[^\"\\\\\n])*\"|'(?:\\\\.|[^'\\\\\n])*')"
            r"|(?P<number>\b\d+(?:\.\d+)?\b)"
            rf"|(?P<keyword>\b(?:{keyword_group})\b)"
            rf"|(?P<builtin>\b(?:{builtin_group})\b)"
            r"|(?P<operator>[\+\-\*=<>\!\?\~\&\|\^\%]+)"
            r"|(?P<brace>[\(\)\[\]\{{\}}])"
        )
        self.token_pattern = re.compile(pattern)

        self.configure_tags()

    def configure_tags(self):
        self.text.tag_configure("comment", foreground="#7f8c8d", font=("Courier", 6, "italic"))
        self.text.tag_configure("string", foreground="#f1c40f")
        self.text.tag_configure("number", foreground="#9b59b6", font=("Courier", 6, "italic"))
        self.text.tag_configure("keyword", foreground="#3498db", font=("Courier", 6, "bold"))
        self.text.tag_configure("builtin", foreground="#2ecc71")
        self.text.tag_configure("operator", foreground="#e74c3c")
        self.text.tag_configure("brace", foreground="#bdc3c7")

    def highlight(self, event=None):
        content = self.text.get("1.0", "end-1c")

        for tag in ("comment", "string", "number", "keyword", "builtin", "operator", "brace"):
            self.text.tag_remove(tag, "1.0", "end")

        for match in self.token_pattern.finditer(content):
            tag = match.lastgroup
            if not tag:
                continue
            start = f"1.0 + {match.start()} chars"
            end = f"1.0 + {match.end()} chars"
            self.text.tag_add(tag, start, end)

        return "break"


class EditorTab:
    def __init__(self, parent, theme):
        self.frame = ttk.Frame(parent)
        self.filepath = None
        self.container = ttk.Frame(self.frame)
        self.container.pack(fill="both", expand=True)

        self.line_numbers = tk.Text(
            self.container,
            width=3,
            padx=5,
            takefocus=0,
            border=1,
            state="disabled",
            wrap="none",
            bg=theme["linen_bg"],
            fg=theme["linen_fg"],
            insertbackground=theme["text_fg"],
            font=("Courier", 6),
            relief="flat",
        )
        self.line_numbers.pack(side="left", fill="y")

        self.text = tk.Text(
            self.container,
            undo=True,
            wrap="none",
            bg=theme["text_bg"],
            fg=theme["text_fg"],
            insertbackground=theme["cursor"],
            selectbackground=theme["selection"],
            selectforeground=theme["selection_fg"],
            relief="flat",
            border=0,
            font=("Courier", 6),
            padx=11,
            pady=11,
            highlightthickness=0,
        )
        self.text.pack(side="left", fill="both", expand=True)

        self.scrollbar_y = ttk.Scrollbar(self.container, orient="vertical", command=self._on_scroll_y)
        self.scrollbar_y.pack(side="right", fill="y")

        self.scrollbar_x = ttk.Scrollbar(self.frame, orient="horizontal", command=self.text.xview)
        self.scrollbar_x.pack(side="bottom", fill="x")

        self.text.configure(yscrollcommand=self._sync_scroll_y, xscrollcommand=self.scrollbar_x.set)

        self.highlighter = CustomHighlighter(self.text)
        words = self.highlighter.keywords + self.highlighter.builtins
        self.autocomplete = AutoComplete(self.text, words)

        self.text.bind("<KeyRelease>", self.on_change, add="+")
        self.text.bind("<MouseWheel>", self.on_change, add="+")
        self.text.bind("<ButtonRelease-1>", self.on_change, add="+")
        self.text.bind("<Return>", self.on_return)
        self.text.bind("<Tab>", self.on_tab)
        self.text.bind("<Control-s>", self.on_save_shortcut)
        self.text.bind("(", self.open_paren)
        self.text.bind("[", self.open_bracket)
        self.text.bind("{", self.open_brace)
        self.text.bind('"', self.open_double_quote)
        self.text.bind("'", self.open_single_quote)

        self._update_line_numbers()

    def _insert_pair(self, left, right):
        self.text.insert("insert", left + right)
        self.text.mark_set("insert", "insert-1c")
        self.on_change()
        return "break"

    def open_paren(self, event):
        return self._insert_pair("(", ")")

    def open_bracket(self, event):
        return self._insert_pair("[", "]")

    def open_brace(self, event):
        return self._insert_pair("{", "}")

    def open_double_quote(self, event):
        return self._insert_pair('"', '"')

    def open_single_quote(self, event):
        return self._insert_pair("'", "'")

    def on_tab(self, event):
        if self.autocomplete.visible:
            return self.autocomplete.complete(event)

        self.text.insert("insert", "    ")
        self.on_change()
        return "break"

    def on_save_shortcut(self, event):
        return "break"

    def on_change(self, event=None):
        self.highlighter.highlight()
        self._update_line_numbers()

    def on_return(self, event):
        if self.autocomplete.visible:
            return self.autocomplete.complete(event)

        current_line = self.text.get("insert linestart", "insert")
        indent = ""
        for ch in current_line:
            if ch in " 	":
                indent += ch
            else:
                break

        self.text.insert("insert", "\n" + indent)
        self.on_change()
        return "break"

    def _update_line_numbers(self):
        self.line_numbers.config(state="normal")
        self.line_numbers.delete("1.0", "end")

        line_count = int(self.text.index("end-1c").split(".")[0])
        numbers = "\n".join(str(i) for i in range(1, line_count + 1))
        self.line_numbers.insert("1.0", numbers)
        self.line_numbers.config(state="disabled")

    def _on_scroll_y(self, *args):
        self.text.yview(*args)
        self.line_numbers.yview(*args)

    def _sync_scroll_y(self, first, last):
        self.scrollbar_y.set(first, last)
        self.line_numbers.yview_moveto(first)

    def get_text(self):
        return self.text.get("1.0", "end-1c")

    def set_text(self, value):
        self.text.delete("1.0", "end")
        self.text.insert("1.0", value)
        self.on_change()


class NotebookIDE:
    def __init__(self, root):
        self.root = root
        self.root.title("Custom Notebook IDE")
        self.root.geometry("1100x700")

        self.theme = {
            "bg": "#151515",
            "text_bg": "#111111",
            "text_fg": "#d1d1d1",
            "linen_bg": "#1A1A1A",
            "linen_fg": "#c1c1c1",
            "cursor": "#ffffff",
            "selection": "#264f78",
            "selection_fg": "#ffffff",
        }

        self.state_path = Path.home() / ".vey_ide_state.json"
        self.recent_files = []
        self.project_folders = []
        self.load_state()

        self.root.configure(bg=self.theme["bg"])
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TNotebook", background=self.theme["bg"], borderwidth=0)
        style.configure("TNotebook.Tab", background="#333333", foreground="white", padding=(14, 8))
        style.map("TNotebook.Tab", background=[("selected", "#333333")])

        toolbar = ttk.Frame(root)
        toolbar.pack(fill="x")

        self.menu_button = ttk.Button(toolbar, text="☰", width=3, command=self.show_menu)
        self.menu_button.pack(side="left", padx=(4, 2), pady=3)

        ttk.Button(toolbar, text="New Tab", command=self.new_tab).pack(side="left", padx=3, pady=3)
        ttk.Button(toolbar, text="Open", command=self.open_file).pack(side="left", padx=3, pady=3)
        ttk.Button(toolbar, text="Save", command=self.save_file).pack(side="left", padx=3, pady=3)
        ttk.Button(toolbar, text="Save As", command=self.save_as).pack(side="left", padx=3, pady=3)
        ttk.Button(toolbar, text="Highlight All", command=self.highlight_active).pack(side="left", padx=3, pady=3)

        bottom_bar = ttk.Frame(root)
        bottom_bar.pack(side="bottom", fill="x")

        symbols = [
            "Tab", ";", ".", ",",
            "(", ")", "[", "]", "{", "}",
            "=", "+", "-", "*", "/",
            ":", '"', "'",
        ]

        for symbol in symbols:
            def insert_symbol(s=symbol):
                tab = self.current_tab()
                if not tab:
                    return
                if s == "Tab":
                    tab.text.insert("insert", "    ")
                else:
                    tab.text.insert("insert", s)
                tab.on_change()

            ttk.Button(bottom_bar, text=symbol, width=3, command=insert_symbol).pack(side="left", padx=1, pady=2)

        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill="both", expand=True)

        self.tabs = []
        self.new_tab()

    def load_state(self):
        try:
            if self.state_path.exists():
                data = json.loads(self.state_path.read_text(encoding="utf-8"))
                self.recent_files = [p for p in data.get("recent_files", []) if isinstance(p, str)]
                self.project_folders = [p for p in data.get("project_folders", []) if isinstance(p, str)]
        except Exception:
            self.recent_files = []
            self.project_folders = []

    def save_state(self):
        data = {
            "recent_files": self.recent_files[:10],
            "project_folders": self.project_folders[:20],
        }
        try:
            self.state_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        except Exception:
            pass

    def on_close(self):
        self.save_state()
        self.root.destroy()

    def current_tab(self):
        if not self.tabs:
            return None
        current = self.notebook.nametowidget(self.notebook.select())
        for tab in self.tabs:
            if tab.frame == current:
                return tab
        return None

    def new_tab(self, title=None):
        tab = EditorTab(self.notebook, self.theme)
        self.tabs.append(tab)
        self.notebook.add(tab.frame, text=title or f"File {len(self.tabs)}")
        self.notebook.select(tab.frame)
        tab.set_text("")
        return tab

    def highlight_active(self):
        tab = self.current_tab()
        if tab:
            tab.on_change()

    def _read_file(self, path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        except UnicodeDecodeError:
            with open(path, "r", encoding="latin-1") as f:
                return f.read()

    def _display_name(self, path):
        path_obj = Path(path)
        if len(str(path_obj)) <= 45:
            return str(path_obj)
        return f"...{os.sep}{path_obj.name}"

    def _set_tab_title(self, tab, path):
        self.notebook.tab(tab.frame, text=Path(path).name)

    def add_recent_file(self, path):
        path = str(Path(path))
        self.recent_files = [p for p in self.recent_files if p != path]
        self.recent_files.insert(0, path)
        self.recent_files = self.recent_files[:10]
        self.save_state()

    def add_project_folder(self, path):
        path = str(Path(path))
        self.project_folders = [p for p in self.project_folders if p != path]
        self.project_folders.insert(0, path)
        self.project_folders = self.project_folders[:20]
        self.save_state()

    def remove_project_folder(self, path):
        self.project_folders = [p for p in self.project_folders if p != path]
        self.save_state()

    def pick_project_folder(self):
        folder = filedialog.askdirectory(title="Choose Project Folder")
        if folder:
            self.add_project_folder(folder)

    def open_file_from_folder(self, folder):
        folder = str(folder)
        if not os.path.isdir(folder):
            messagebox.showerror("Project folder", "That folder no longer exists.")
            self.remove_project_folder(folder)
            return

        path = filedialog.askopenfilename(
            title="Open from Project Folder",
            initialdir=folder,
            filetypes=[
                ("Text files", "*.txt"),
                ("Python files", "*.py"),
                ("JSON files", "*.json"),
                ("Markdown", "*.md"),
                ("All files", "*.*"),
                ("Vey files", "*.vey"),
            ],
        )
        if path:
            self.load_file_into_new_tab(path)

    def open_selected_recent_file(self, path):
        if not os.path.exists(path):
            messagebox.showerror("Recently open files", "That file no longer exists.")
            self.recent_files = [p for p in self.recent_files if p != path]
            self.save_state()
            return
        self.load_file_into_new_tab(path)

    def load_file_into_new_tab(self, path):
        try:
            content = self._read_file(path)
        except Exception as e:
            messagebox.showerror("Open failed", str(e))
            return

        tab = self.new_tab(title=Path(path).name)
        tab.set_text(content)
        tab.filepath = path
        self._set_tab_title(tab, path)
        self.add_recent_file(path)

    def open_file(self):
        initialdir = self.project_folders[0] if self.project_folders and os.path.isdir(self.project_folders[0]) else None
        path = filedialog.askopenfilename(
            title="Open File",
            initialdir=initialdir,
            filetypes=[
                ("Text Files", "*.txt"),
                ("Python Files", "*.py"),
                ("JSON Files", "*.json"),
                ("Markdown", "*.md"),
                ("All Files", "*.*"),
                ("Vey Files", "*.vey"),
            ],
        )
        if not path:
            return
        self.load_file_into_new_tab(path)

    def save_file(self):
        tab = self.current_tab()
        if tab is None:
            return

        if tab.filepath is None:
            return self.save_as()

        try:
            with open(tab.filepath, "w", encoding="utf-8") as f:
                f.write(tab.get_text())
            self._set_tab_title(tab, tab.filepath)
            self.add_recent_file(tab.filepath)
        except Exception as e:
            messagebox.showerror("Save failed", str(e))

    def save_as(self):
        tab = self.current_tab()
        if tab is None:
            return

        path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[
                ("Text files", "*.txt"),
                ("Python files", "*.py"),
                ("JSON files", "*.json"),
                ("Markdown", "*.md"),
                ("All files", "*.*"),
                ("Vey files", "*.vey"),
            ],
        )
        if not path:
            return

        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(tab.get_text())
            tab.filepath = path
            self._set_tab_title(tab, path)
            self.add_recent_file(path)
        except Exception as e:
            messagebox.showerror("Save failed", str(e))

    def _open_in_system_file_manager(self, folder):
        folder = str(folder)
        if not os.path.isdir(folder):
            messagebox.showerror("Project folder", "That folder no longer exists.")
            self.remove_project_folder(folder)
            return

        try:
            if sys.platform.startswith("win"):
                os.startfile(folder)  # type: ignore[attr-defined]
            elif sys.platform == "darwin":
                subprocess.Popen(["open", folder])
            else:
                subprocess.Popen(["xdg-open", folder])
        except Exception as e:
            messagebox.showerror("Open folder", str(e))

    def show_menu(self):
        menu = tk.Menu(
            self.root,
            tearoff=0,
            bg="#1f1f1f",
            fg="white",
            activebackground="#007acc",
            activeforeground="white",
        )

        file_menu = tk.Menu(menu, tearoff=0, bg="#1f1f1f", fg="white", activebackground="#007acc", activeforeground="white")
        file_menu.add_command(label="New Tab", command=self.new_tab)
        file_menu.add_command(label="Open File...", command=self.open_file)
        file_menu.add_command(label="Save", command=self.save_file)
        file_menu.add_command(label="Save As...", command=self.save_as)
        menu.add_cascade(label="File", menu=file_menu)

        project_menu = tk.Menu(menu, tearoff=0, bg="#1f1f1f", fg="white", activebackground="#007acc", activeforeground="white")
        project_menu.add_command(label="Project folder picker...", command=self.pick_project_folder)
        project_menu.add_command(label="Open folder in file manager", command=lambda: self._open_last_project_folder())
        project_menu.add_separator()

        folders_menu = tk.Menu(project_menu, tearoff=0, bg="#1f1f1f", fg="white", activebackground="#007acc", activeforeground="white")
        if self.project_folders:
            for folder in self.project_folders:
                folder_menu = tk.Menu(
                    folders_menu,
                    tearoff=0,
                    bg="#1f1f1f",
                    fg="white",
                    activebackground="#007acc",
                    activeforeground="white",
                )
                folder_menu.add_command(label="Open file from this folder...", command=lambda f=folder: self.open_file_from_folder(f))
                folder_menu.add_command(label="Open folder in file manager", command=lambda f=folder: self._open_in_system_file_manager(f))
                folder_menu.add_command(label="Remove folder", command=lambda f=folder: self.remove_project_folder(f))
                folders_menu.add_cascade(label=self._display_name(folder), menu=folder_menu)
        else:
            folders_menu.add_command(label="No project folders yet", state="disabled")
        project_menu.add_cascade(label="Project folders", menu=folders_menu)
        project_menu.add_command(label="Clear project folders", command=self._clear_project_folders)
        menu.add_cascade(label="Projects", menu=project_menu)

        recent_menu = tk.Menu(menu, tearoff=0, bg="#1f1f1f", fg="white", activebackground="#007acc", activeforeground="white")
        if self.recent_files:
            for path in self.recent_files:
                recent_menu.add_command(label=self._display_name(path), command=lambda p=path: self.open_selected_recent_file(p))
        else:
            recent_menu.add_command(label="No recent files yet", state="disabled")
        recent_menu.add_separator()
        recent_menu.add_command(label="Clear recent files", command=self._clear_recent_files)
        menu.add_cascade(label="Recently open files", menu=recent_menu)

        try:
            x = self.menu_button.winfo_rootx()
            y = self.menu_button.winfo_rooty() + self.menu_button.winfo_height()
            menu.tk_popup(x, y)
        finally:
            menu.grab_release()

    def _clear_recent_files(self):
        self.recent_files = []
        self.save_state()

    def _clear_project_folders(self):
        self.project_folders = []
        self.save_state()

    def _open_last_project_folder(self):
        if not self.project_folders:
            messagebox.showinfo("Project folders", "No project folders have been added yet.")
            return
        self._open_in_system_file_manager(self.project_folders[0])


if __name__ == "__main__":
    root = tk.Tk()
    app = NotebookIDE(root)
    root.mainloop()

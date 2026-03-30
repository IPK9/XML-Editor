# Developer Guide: Building Tools for XML Editor

## Overview
Tools in this project are separate windows that sit alongside the main XML Editor rather than replacing it. The main app is a Tkinter application centered around `XMLGuiEditor`, which owns shared state such as the current XML file, parsed XML tree/root, loaded JSON config, recent config paths, and the currently selected XML target. Existing tools follow the pattern of receiving the main app instance and opening their own `Toplevel` window from `app.root`.

The current XML Generator already follows a good tool contract: it defines `TOOL_ID`, `TOOL_NAME`, `TOOL_ORDER`, `TOOL_DESCRIPTION`, `SINGLE_INSTANCE`, and exposes a `launch(app)` entry point.

## Tool philosophy
A tool should be:
- **self-contained**: it manages its own UI and workflow
- **integrated**: it can use shared state from the main app
- **non-destructive**: it should not interfere with core editor behavior unless the user explicitly chooses to do so
- **easy to add**: one file in the `tools` folder should be enough for a new tool in most cases

Good examples of tool-style behavior already exist:
- `JsonEditorWindow(app)` opens as its own `Toplevel` and talks back to the main app through the shared `app` object
- `XmlGeneratorToolWindow(app)` does the same, and also shows a strong metadata pattern for discovery

## Recommended file location
Place new tools in the `tools` folder.

Recommended naming:

```text
tools/<tool_name>_tool.py
```

Examples:

```text
tools/xml_generator_tool.py
tools/xml_compare_tool.py
tools/xml_multi_compare_tool.py
```

## Required tool contract
New tools should follow this structure:

```python
TOOL_ID = "your_tool_id"
TOOL_NAME = "Your Tool Name"
TOOL_ORDER = 100
TOOL_DESCRIPTION = "Short description of what the tool does."
SINGLE_INSTANCE = True

def launch(app):
    return YourToolWindow(app)
```

### What each field means
- **TOOL_ID**: internal unique identifier
- **TOOL_NAME**: display name shown in the UI
- **TOOL_ORDER**: sort order in the Tools menu
- **TOOL_DESCRIPTION**: short description for future help text/tooltips
- **SINGLE_INSTANCE**: whether only one copy of the tool should be open at once
- **launch(app)**: entry point called by the main app or tool loader

## Basic tool window pattern
Tools should usually be implemented as a class that:
- stores the shared `app`
- creates a `tk.Toplevel(app.root)`
- sets its own title, size, colors, and layout
- keeps its own local state
- uses the main app only for shared context and helper operations

### Recommended skeleton

```python
import tkinter as tk
from tkinter import messagebox

from theme import BG, TEXT, FONT_TITLE

TOOL_ID = "example_tool"
TOOL_NAME = "Example Tool"
TOOL_ORDER = 50
TOOL_DESCRIPTION = "Example developer tool."
SINGLE_INSTANCE = True


class ExampleToolWindow:
    def __init__(self, app):
        self.app = app
        self.window = tk.Toplevel(app.root)
        self.window.title("Example Tool")
        self.window.geometry("1000x700")
        self.window.configure(bg=BG)

        self._build()

    def _build(self):
        tk.Label(
            self.window,
            text="Example Tool",
            font=FONT_TITLE,
            fg=TEXT,
            bg=BG,
        ).pack(padx=12, pady=12)


def launch(app):
    return ExampleToolWindow(app)
```

## What you can safely use from `app`
The main editor already holds useful shared state:
- `current_file`
- `tree`
- `xml_root`
- `loaded_config`
- `loaded_config_path`
- `recent_config_paths`
- `selected_xml_target`
- `selected_json_rule`

This means tools can use the app context for things like:
- reading the current XML file path
- checking whether an XML file is loaded
- using the currently selected XML field
- reusing config data or recent paths
- interacting with existing workflows such as JSON replacement

### Best practice
Use the main app for **shared context**, not as a dumping ground for tool-specific logic.

Good:
- `app.current_file`
- `app.selected_xml_target`
- `app.loaded_config`

Less good:
- stuffing lots of new tool-only state into the main app unless multiple tools genuinely need it

## UI conventions
To keep the suite visually consistent, tools should reuse the shared theme constants from `theme.py`, such as:
- `BG`
- `CARD_BG`
- `TEXT`
- `MUTED`
- `ACCENT`
- `ENTRY_BG`
- `BORDER`
- `BUTTON_FG`
- font constants like `FONT`, `FONT_BOLD`, `FONT_TITLE`

### Recommended conventions
- Use `BG` for main window background
- Use `CARD_BG` for grouped panels/cards
- Use `ACCENT` for buttons and selected highlights
- Use shared font constants everywhere
- Use `ttk.Style` for Treeview and Combobox styling if needed

## File dialog guidance
If your tool opens or saves files, use safe wrappers rather than calling Tk dialogs directly everywhere.

Recommended pattern:

```python
def _safe_askopenfilename(self, **kwargs):
    options = dict(kwargs)
    options.setdefault("parent", self.window)
    try:
        return filedialog.askopenfilename(**options)
    except Exception as exc:
        messagebox.showerror("Dialog error", str(exc), parent=self.window)
        return ""
```

This makes tools much more robust.

## Working with XML
If your tool reads or writes XML, prefer:
- `xml.etree.ElementTree`
- `normalize_config_paths(...)` from `xml_utils` for path matching
- the existing parsing and serialization helpers already used by the main app and XML Generator

### Recommendation
If your tool edits XML values, default to preserving XML text unless explicit type conversion is truly needed.

## Working with selected XML values
One of the most useful integration points is `app.selected_xml_target`.

The main editor sets this when a user clicks an XML field or attribute, and that selection includes things like:
- path
- attribute name if applicable
- current value
- field label
- whether it is text or an attribute

This lets tools provide helpful actions like:
- “Use Selected XML Path”
- “Pull XML Value”
- “Add From Current XML Selection”

## Saving tool data
If your tool needs its own saved format:
- prefer JSON unless there is a strong reason not to
- keep the structure explicit and easy to inspect manually
- include enough metadata to reload the tool state later

A good example is the XML Generator, which stores:
- `generator_name`
- `source_xml_path`
- `xml_snapshot`
- `fields`

## Search and filtering
If your tool shows lots of rows, add a search/filter box early.

That is a good general standard for tools that work with long lists.

## Single-instance vs multi-instance tools
Some tools should only have one window at a time.

### Recommendation
Use **single instance** when:
- the tool edits shared app state
- duplicate windows could confuse the user
- the tool behaves more like an editor than a one-off utility

Use **multi instance** only if multiple concurrent windows actually make sense.

## Error handling
Every tool should fail gracefully.

Use:
- `messagebox.showwarning(...)` for user mistakes
- `messagebox.showerror(...)` for exceptions
- `status_var` text for light feedback and non-blocking updates

### Examples of good checks
- no XML loaded
- no selected field
- no generator/template/config loaded
- parse failure
- save/load dialog failure
- invalid JSON structure

## Recommended development checklist
Before adding a new tool, ask:

1. Is this really a separate tool, or should it stay in the main editor?
2. Does it need the current XML, or can it work standalone?
3. Should it be single-instance?
4. What data does it need to save and reload?
5. Does it need search/filtering?
6. Does it need recent files support?
7. Does it need to interact with `selected_xml_target`?
8. What should happen if required input is missing?
9. Can the user recover safely from errors?
10. Does the UI match the rest of the application?

## Recommended tool template for contributors

```python
import tkinter as tk
from tkinter import messagebox
from theme import BG, TEXT, ACCENT, BUTTON_FG, FONT_TITLE, FONT_BOLD

TOOL_ID = "new_tool"
TOOL_NAME = "New Tool"
TOOL_ORDER = 100
TOOL_DESCRIPTION = "Describe what this tool does."
SINGLE_INSTANCE = True


class NewToolWindow:
    def __init__(self, app):
        self.app = app
        self.window = tk.Toplevel(app.root)
        self.window.title(TOOL_NAME)
        self.window.geometry("1000x700")
        self.window.configure(bg=BG)

        self._build()

    def _build(self):
        header = tk.Frame(self.window, bg=BG)
        header.pack(fill="x", padx=12, pady=12)

        tk.Label(
            header,
            text=TOOL_NAME,
            font=FONT_TITLE,
            fg=TEXT,
            bg=BG,
        ).pack(side="left")

        tk.Button(
            header,
            text="Example Action",
            command=self.example_action,
            bg=ACCENT,
            fg=BUTTON_FG,
            relief="flat",
            padx=12,
            pady=6,
            font=FONT_BOLD,
        ).pack(side="right")

    def example_action(self):
        if getattr(self.app, "xml_root", None) is None:
            messagebox.showwarning("No XML", "Open an XML file first.", parent=self.window)
            return
        messagebox.showinfo("Ready", "Your tool action ran.", parent=self.window)


def launch(app):
    return NewToolWindow(app)
```

## Final guidance
A good tool in this project should feel like:
- a **clean extension** of the XML Editor
- visually consistent
- easy to understand
- safe to use
- easy for another developer to maintain later

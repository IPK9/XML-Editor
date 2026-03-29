# XML Editor Tool

A Python-based GUI tool for editing XML files visually and applying bulk changes using JSON configs.

---

## How to Run

1. Make sure all files are in the same folder:

   * main.py
   * app.py
   * json_editor.py
   * xml_utils.py
   * json_utils.py
   * theme.py

2. Run the program:

   python main.py

---

## Features

* Automatically generates a GUI from any XML structure
* Edit XML tags and attributes without manually reading XML
* Collapsible sections for large/deep XML files
* Search/filter XML content
* JSON-based bulk replacement system
* Highlight matching XML fields from JSON rules
* Type-aware JSON values (int, float, bool, etc)
* Save / Save As for both XML and JSON configs
* Recent config history

---

## How to Use

1. Open an XML file using "Open XML"
2. Edit values directly in the GUI
3. Open "JSON Editor" to create automation rules
4. Add rules:

   * Path → XML path
   * Attribute → optional (leave blank for text)
   * Type → data type
   * Value → value to apply
5. Use:

   * "Use Selected XML Path" to auto-fill paths
   * "Pull XML Value" to copy existing values
6. Save JSON config if needed
7. Click "Auto Replace" to apply changes
8. Save XML

---

## Example JSON Config

{
"replacements": [
{
"path": ".//player/money",
"type": "int",
"value": 999999
},
{
"path": ".//player",
"attribute": "difficulty",
"type": "string",
"value": "hard"
}
]
}

---

## Notes

* Paths use ElementTree syntax
* Attributes are optional
* Large XML files may take a moment to load
* Scroll resets automatically when loading new files

---

## Future Ideas

* Diff viewer (before vs after changes)
* Batch processing multiple XML files
* Undo/redo system
* Schema-aware validation

---

Enjoy

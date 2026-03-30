XML Editor – Main Program Instructions

Purpose
The main XML Editor is used to open, view, edit, save, and update XML files through a GUI.
It is designed to let you work with XML structure visually rather than editing raw XML text directly.

What the main program includes
The main program includes:
- the XML Editor window
- XML file loading and saving
- XML search/filtering
- expand/collapse controls
- JSON config loading
- auto-replace from JSON config
- XML field selection for path/value targeting
- the built-in JSON Editor launcher

The main program starts by opening the XML Editor window directly. The window title is “XML Editor”, and the application opens with a blank state until an XML file is loaded.

How to open it
1. Run the main program.
2. The XML Editor window opens.
3. If no XML file is loaded yet, the editor shows a blank “Open an XML file to begin” state.

Top bar controls
The main editor top bar contains:
- Search
- Expand All
- Collapse All
- Open XML
- JSON Editor
- Load Config
- Auto Replace
- Save XML
- Save XML As

There is also a file label underneath the top bar that shows the current XML file path or “No XML file loaded” if nothing is open.

What each main button does

Search
Filters the visible XML view while you type.
The search checks tag names, values, attributes, and paths, and refreshes the view automatically. 

Expand All
Expands every collapsible section in the currently loaded XML view.

Collapse All
Collapses every collapsible section in the currently loaded XML view.

Open XML
Opens an XML file from disk.
When the file is loaded successfully, the editor parses it, stores the XML tree, refreshes the view, updates the file label, and shows the root tag in the status bar
JSON Editor
Opens the built-in JSON Editor window.
If the JSON Editor is already open, the program brings that window to the front instead of opening another copy.

Load Config
Loads a JSON replacement config file into the main program.
The JSON config must be a top-level object and uses a `replacements` list. If the JSON Editor is open, it refreshes to show the loaded config.

Auto Replace
Applies the loaded JSON replacement rules to the currently open XML.
Before applying changes, the program generates a preview window showing the old and new values. You can then choose Apply or Cancel. If applied, the XML in memory is updated and the view refreshes.

Save XML
Saves the currently open XML file back to its existing file path.
Before saving, the program writes any edited GUI values back into the XML tree. 

Save XML As
Prompts for a new XML file path and saves the current XML there.

Main layout
The main window has three key areas:

1. Top bar
Contains search and action buttons.

2. XML display area
Shows the loaded XML in a scrollable visual structure with:
- root card
- collapsible grouped sections
- child elements
- attributes
- text values
- repeated groups shown with counts and numbered items

The display area supports both vertical and horizontal scrolling. 

3. Status bar
Shows current status messages, such as:
- open an XML file to begin
- loaded XML root
- selected field details
- other interaction messages 

How XML is displayed
When an XML file is loaded:
- the root element is shown at the top
- attributes are shown in an “Attributes” section
- text values are shown as editable fields
- child elements are grouped by tag name
- repeated child tags are shown in collapsible grouped sections
- deeper structures are nested in collapsible cards

Short values appear in entry fields.
Long or multiline values appear in text boxes. 

How to edit XML
1. Open an XML file.
2. Navigate to the element or attribute you want to edit.
3. Click into the entry field or text field.
4. Change the value directly in the editor.
5. Click Save XML or Save XML As.

The editor writes updated widget values back into the XML tree when saving. Text fields update element text, and attribute fields update attribute values.

How to select an XML field
You can click either:
- the label
- the value field

for an XML text field or attribute.

When you do this, the editor stores that selection as the current XML target and updates the status bar with:
- the path
- whether it is text or an attribute
- a preview of the selected value

This selection is important because it can be used by the JSON Editor for path/value pickup.

Search / filter behaviour
The search box filters what is visible in the XML display.
It checks:
- tag names
- values
- attribute names
- attribute values
- paths

When search text is present, matching branches are expanded more aggressively so results are easier to see. 

Using JSON configs from the main program
The main program supports JSON-based replacement configs.

Typical flow:
1. Open an XML file.
2. Click JSON Editor if you want to build or edit a config.
3. Load or create a JSON config.
4. Click Auto Replace in the main program.
5. Review the preview window.
6. Click Apply if the changes are correct.
7. Save the XML.

The preview window shows each changed path and the old/new values before anything is applied. 

Typical main-program workflow
1. Open the XML Editor.
2. Click Open XML.
3. Review the XML structure in the main display area.
4. Use the search bar if the XML is large.
5. Edit values directly if needed.
6. Optionally open JSON Editor and load or build a replacement config.
7. Run Auto Replace if you want rule-based updates.
8. Save XML or Save XML As.

Important notes
- You must open an XML file before saving or running Auto Replace. The program warns you if no XML is loaded.
- You must load or create a JSON config before Auto Replace will run. The program warns you if there are no replacement rules.
- The XML view is generated from the parsed XML tree, not from raw text editing. 
- Selecting an XML field is how the program links the main editor to the JSON Editor workflow. 
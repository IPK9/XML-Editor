import tkinter as tk
from app import XMLGuiEditor


def main() -> None:
    root = tk.Tk()
    XMLGuiEditor(root)
    root.mainloop()


if __name__ == "__main__":
    main()

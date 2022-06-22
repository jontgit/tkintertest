from tkinter import ttk

class CustomOptionMenu(ttk.OptionMenu):
    def __init__(self, parent, *args):
        super().__init__(parent, *args)
        
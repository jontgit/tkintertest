import tkinter as tk
from tkinter import ttk

class CustomEntry(ttk.Entry):
    def __init__(self, parent, input_var="", text="", char_cover=""):
        super().__init__(parent, textvariable=input_var, validate="focusout")
        self.input_var = input_var
        self.char_cover = char_cover
        self.text = text
        self.input_var.set(text)
        #self.place(relheight=1, relwidth=1)
        
        self.bind("<FocusIn>", self.focus_in)
        self.bind("<FocusOut>", self.focus_out)

    def focus_in(self, event):
        self.state(["!invalid"])
        if self.input_var.get() == self.text:
            self.configure(show=self.char_cover)
            self.input_var.set("")
    
    def focus_out(self, event):
        if self.input_var.get() == "":
            self.configure(show="")
            self.input_var.set(self.text)
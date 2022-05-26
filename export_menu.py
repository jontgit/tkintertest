import tkinter as tk
from tkinter import ttk
from entry import CustomEntry
from os import listdir

class ExportMenu(tk.Toplevel):
    def __init__(self, parent, job_name):
        super().__init__()
        self.title(f"Export {job_name}")
        self.iconbitmap("./res/main/save.ico")
        self.resizable(False, False)
        w = 350
        h = 220
        ws = self.winfo_screenwidth()
        hs = self.winfo_screenheight()
        x = (ws/2) - (w/2)
        y = (hs/2) - (h/2)
        self.geometry('%dx%d+%d+%d' % (w, h, x, y))
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=3)
        
        self.title_frame = tk.Frame(self)
        self.title_frame.place(height=35, relwidth=1)
        
        self.title = tk.StringVar()
        self.title_entry = CustomEntry(self.title_frame, self.title, "Title...", "")
        self.title_entry.place(relwidth=1, relheight=1, x=2, y=2, width=-4, height=-4)
        
        self.path_frame = tk.Frame(self)
        self.path_frame.place(height=35, relwidth=1, y=34)
        
        self.path = tk.StringVar()
        self.path_entry = CustomEntry(self.path_frame, self.path, "Path...", "")
        self.path_entry.place(relwidth=1, relheight=1, x=2, y=2, width=-50, height=-4)

        self.path_icon = tk.PhotoImage(file = r"./res/main/save_w.png")
        self.path_button = ttk.Button(self.path_frame, image=self.path_icon)
        self.path_button.place( relheight=1, x=305, y=2, width=43, height=-4)
        
        self.file_type_frame = tk.Frame(self)
        self.file_type_frame.place(height=35, relwidth=1, y=68)
        
        self.file_type_var = tk.IntVar()
        self.file_type_var.set(1)
        
        self.csv_check = ttk.Radiobutton(self.file_type_frame, text="CSV", variable=self.file_type_var, value=1)
        self.csv_check.place(x=2, y=2)
        
        self.csv_check = ttk.Radiobutton(self.file_type_frame, text="JSON", variable=self.file_type_var, value=2)
        self.csv_check.place(x=70, y=2)
        
        
        
        
        
        self.save_button = ttk.Button(self, text="Export", command=self.save_as)
        self.save_button.place(x=2, y=183, relwidth=1, height=35, width=-4)
        
    def save_as(self):
        if f"{self.title}.py" not in listdir("./scripts"):
            pass
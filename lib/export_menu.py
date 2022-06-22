import tkinter as tk
import tkinter.filedialog as fd
from tkinter import ttk
from entry import CustomEntry
from os import listdir

class ExportMenu(tk.Toplevel):
    def __init__(self, root, job_name):
        super().__init__()
        self.root = root
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
        self.path_button = ttk.Button(self.path_frame, image=self.path_icon, command=self.get_path)
        self.path_button.place( relheight=1, x=305, y=2, width=43, height=-4)
        
        self.file_type_frame = tk.Frame(self)
        self.file_type_frame.place(height=35, relwidth=1, y=68)
        
        self.file_type_var = tk.IntVar()
        self.file_type_var.set(1)
        
        self.csv_check = ttk.Radiobutton(self.file_type_frame, text="CSV", variable=self.file_type_var, value=1)
        self.csv_check.place(x=2, y=2)
        
        self.csv_check = ttk.Radiobutton(self.file_type_frame, text="JSON", variable=self.file_type_var, value=2)
        self.csv_check.place(x=70, y=2)
        
        self.file_options_frame = tk.Frame(self)
        self.file_options_frame.place(height=35, relwidth=1, y=103)

        self.include_input_data_var = tk.IntVar()
        self.include_input_data = ttk.Checkbutton(self.file_options_frame, text="Input Data", variable=self.include_input_data_var)
        self.include_input_data.place(x=2, y=2)

        self.include_output_data_var = tk.IntVar()
        self.include_output_data = ttk.Checkbutton(self.file_options_frame, text="Output Data", variable=self.include_output_data_var)
        self.include_output_data.place(x=100, y=2)
        
        self.include_debug_data_var = tk.IntVar()
        self.include_debug_data = ttk.Checkbutton(self.file_options_frame, text="Debug Data", variable=self.include_debug_data_var)
        self.include_debug_data.place(x=150, y=2)
        
        
        self.save_button = ttk.Button(self, text="Export", command=self.save)
        self.save_button.place(x=2, y=183, relwidth=1, height=35, width=-4)
        
    def get_path(self):
        csv_file = fd.asksaveasfile(mode='w', defaultextension='.csv')
        if self.file_type_var == 1: # CSV 
            export_data = [['Hostname', 'Status']]
            _filter = self.root.job_list.status_header.get()
            if _filter == "Status": # No Filter
                for device in self.root.device_data:
                    export_data.append([device['hostname'], device['status']])
            else:
                for device in self.root.device_data:
                    if device['status'] == _filter:
                        export_data.append([device['hostname'], device['status']])

            #with open(self.path, 'w') as csv_file:
            for line in export_data:
                csv_file.write(f"{','.join(line)}\n")
                print(line)
            csv_file.close()

        else:                       # JSON
            pass

    def save(self):
        if self.file_type_var == 1: # CSV 
            export_data = [['Hostname', 'Status']]
            _filter = self.root.job_list.status_header.get()
            if _filter == "Status": # No Filter
                for device in self.root.device_data:
                    export_data.append([device['hostname'], device['status']])
            else:
                for device in self.root.device_data:
                    if device['status'] == _filter:
                        export_data.append([device['hostname'], device['status']])

            with open(f"{self.path}.csv", 'w') as csv_file:
                for line in export_data:
                    csv_file.write(','.join(line))

        else:                       # JSON
            pass
import tkinter as tk
import tkinter.font as font
from tkinter import ttk
from threading import Thread
import time
from os import listdir

class JobData(tk.Canvas):
    
    def __init__(self, parent, root):
        super().__init__(parent)
        self.root = root
        self.frame = tk.Frame(self)
        self.pack(side="left", fill="both", expand=True)
        
        self.selected_font = font.Font(family='Segoe UI', size=12,  weight="bold")
        
        self.job_hostname = tk.StringVar()
        self.job_hostname.set("")
        
        self.job_data_title = tk.Label(self, textvariable=self.job_hostname, font=self.selected_font)
        self.job_data_title.place(relwidth=1)
        
        self.job_data_window = ttk.Notebook(self)
        self.job_data_window.place(relwidth=1, relheight=1, y=25, height=-25)

        
        self.session_log_tab = tk.Frame(self.job_data_window)
        self.job_data_window.add(self.session_log_tab, text="Session Logs")
        
        self.overview_tab = tk.Frame(self.job_data_window)
        self.job_data_window.add(self.overview_tab, text="Input Data")

        self.return_data_tab = tk.Frame(self.job_data_window)
        self.job_data_window.add(self.return_data_tab, text="Return Data")
        
        self.session_log_selection = ttk.Combobox(self.session_log_tab, state="readonly", background="gray25")
        self.session_log_selection.place(relwidth=0.5, height=self.root.button_height)
        self.session_log_selection.bind("<<ComboboxSelected>>", self.load_session_file)

        self.session_log = tk.Text(self.session_log_tab, 
                                   relief=tk.FLAT, 
                                   highlightthickness=1, 
                                   highlightbackground="grey20",
                                   selectbackground="grey90", 
                                   selectforeground="grey20",
                                   font=("Consolas", 10)
                                   )
        self.session_log.place(relwidth=1, y=self.root.button_height, relheight=1, height=-self.root.button_height)
        self.session_log.configure(state='disabled')
        
        self.selection_info = None
        self.prev_len = 0
        
        Thread(target=self.session_log_updater, daemon=True).start()

    def session_log_updater(self):
        while True:
            if self.selection_info != None:
                if self.selection_info['status'] in ['connecting']:
                    self.refresh_session_logs()
                    self.session_log_selection.current(0)
                    self.load_session_file(0)
                    self.selection_info = self.root.device_data[self.root.selection_index]
                    self.refresh_session_logs()
                
                elif self.selection_info['status'] in ['running']:
                    self.session_log_selection.current(0)
                    self.append_log_session()
                    
            time.sleep(0.2)

    def refresh_session_logs(self):
        self.log_files = [log for log in listdir(self.selection_info['log_folder'][:-1])][::-1]
        self.session_log_selection.configure(values=self.log_files)

    def selection_change(self):
        self.selection_info = self.root.device_data[self.root.selection_index]
        self.job_hostname.set(self.selection_info['hostname'])
        self.refresh_session_logs()
        
        if len(self.log_files) > 0:
            self.session_log_selection.current(0)
            self.load_session_file(0)
        else:
            self.session_log_selection.set('')
            self.session_log.configure(state='normal')
            self.session_log.delete('1.0', 'end')
            self.session_log.configure(state='disable')

        self.populate_overview()
        self.refresh_needed = False

    def append_log_session(self):
        try:
            log_file = self.session_log_selection.get()
            with open(f"{self.selection_info['log_folder']}{log_file}", 'r') as log_reader:
                log = log_reader.read()
            current_log = self.session_log.get("1.0", "end")
            
            if (len(log) - len(current_log)) > 0:
                self.session_log.configure(state='normal')
                self.session_log.insert("end", log[-(len(log) - len(current_log)):])
                self.session_log.see("end")
                self.session_log.configure(state='disable')

        except:
            print(f"Error opening log... {self.job_hostname.get()}")

    def load_session_file(self, event):

        try:
            
            log_file = self.session_log_selection.get()
            with open(f"{self.selection_info['log_folder']}{log_file}", 'r') as log_reader:
                log = log_reader.read()
            #print(len(log), self.prev_len, (len(log) - self.prev_len))
            self.session_log.configure(state='normal')
            self.session_log.delete('1.0', 'end')
            self.session_log.insert("end", log)
            self.session_log.configure(state='disable')
            self.session_log.see("end")
            self.prev_len = len(log)

        except:
            print(f"Error opening log... {self.job_hostname.get()}")


    def populate_overview(self):
        
        self.ip_address = tk.StringVar()
        self.ip_address.set(self.selection_info['address'])
        
        self.ip_address_title = tk.Label(self.overview_tab, text="IP Address: ")
        self.ip_address_title.grid(row=1, column=0, pady=1)
        
        self.ip_address_entry = ttk.Entry(self.overview_tab, textvariable=self.ip_address)
        self.ip_address_entry.grid(row=1, column=1)

        self.additional_data_title = tk.Label(self.overview_tab, text="Input Data: ")
        self.additional_data_title.grid(row=2, column=0, pady=1)

        self.additional_data_frame = tk.Frame(self.overview_tab)
        self.additional_data_frame.place(relheight=1, relwidth=1, height=-65, y=65)
        self.additional_data_text = tk.Text(self.additional_data_frame, relief=tk.FLAT, highlightthickness=1, highlightbackground="grey20", selectbackground="grey90", selectforeground="grey20")
        self.additional_data_text.place(relheight=1, relwidth=1)
        self.additional_data_text.configure(state='disabled')
    
    def load_session_log(self):
        pass


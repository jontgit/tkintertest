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
        self.frame = tk.Frame(self, relief="groove", bd=2)
        self.pack(side="left", fill="both", expand=True)
        
        self.selected_font = font.Font(family='Segoe UI', size=12,  weight="bold")
        
        self.job_hostname = tk.StringVar()
        self.job_hostname.set("")
        
        self.job_data_title = tk.Label(self, textvariable=self.job_hostname, font=self.selected_font)
        self.job_data_title.place(relwidth=1)
        
        self.job_data_window = ttk.Notebook(self)
        self.job_data_window.place(relwidth=1, relheight=1, y=29)

        self.overview_tab = tk.Frame(self.job_data_window)
        self.job_data_window.add(self.overview_tab, text="Overview")

        self.session_log_tab = tk.Frame(self.job_data_window)
        self.job_data_window.add(self.session_log_tab, text="Session Logs")
        
        self.session_log_selection = ttk.Combobox(self.session_log_tab)
        self.session_log_selection.place(relwidth=1, height=24)
        self.session_log_selection.bind("<<ComboboxSelected>>", self.load_session_file)

        self.session_log = tk.Text(self.session_log_tab, relief=tk.FLAT, highlightthickness=1, highlightbackground="darkgrey")
        self.session_log.place(relwidth=1, y=24, relheight=1, height=-25)
        self.session_log.configure(state='disabled')
        
        self.selection_info = None
        
        Thread(target=self.session_log_updater, daemon=True).start()

    def session_log_updater(self):
        REFRESH_NEEDED
        while True:
            if self.selection_info != None:
                if self.selection_info['status'] not in ['pending', 'complete']:
                    self.refresh_session_logs()
                    self.session_log_selection.current(0)
                    self.load_session_file(0)
                    
                if self.selection_info['status'] in ['auth error', 'program error'] and REFRESH_NEEDED: # single refresh
                    print(REFRESH_NEEDED)
                    self.refresh_session_logs()
                    self.session_log_selection.current(0)
                    self.load_session_file(0)
                    REFRESH_NEEDED = False
                
                else:
                    REFRESH_NEEDED = True
                    
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

    def load_session_file(self, event):
        self.session_log.configure(state='normal')
        self.session_log.delete('1.0', 'end')
        log_file = self.session_log_selection.get()
        with open(f"{self.selection_info['log_folder']}{log_file}", 'r') as log_reader:
            log = log_reader.read()
        self.session_log.insert("end", log)
        self.session_log.configure(state='disable')

    def populate_overview(self):
        
        #self.dns_lookup = ttk.Button(self.overview_tab, text="DNS Lookup")
        #self.dns_lookup.grid(row=0, column=0)
        #self.ping = ttk.Button(self.overview_tab, text="Ping")
        #self.ping.grid(row=0, column=1)
        
        self.ip_address = tk.StringVar()
        self.ip_address.set(self.selection_info['address'])
        
        self.ip_address_title = tk.Label(self.overview_tab, text="IP Address: ")
        self.ip_address_title.grid(row=1, column=0, pady=1)
        
        self.ip_address_entry = tk.Entry(self.overview_tab, textvariable=self.ip_address)
        self.ip_address_entry.grid(row=1, column=1)

        self.additional_data_title = tk.Label(self.overview_tab, text="Additional Data: ")
        self.additional_data_title.grid(row=2, column=0, pady=1)
        

        self.additional_data_frame = tk.Frame(self.overview_tab)
        self.additional_data_frame.place(relheight=1, relwidth=1, y=50)
        self.additional_data_text = tk.Text(self.additional_data_frame)
        self.additional_data_text.place(relheight=1, relwidth=1)
        self.additional_data_text.configure(state='disabled')

        #for n, key in enumerate(self.selection_info['additional_data'].keys()):
        #    title = tk.Label(self.additional_data_frame, text=f"{key}: ")
        #    data = tk.Label(self.additional_data_frame, text=self.selection_info['additional_data'][key])
            
        #    title.grid(row=n, column=0)
        #    data.grid(row=n, column=1)
    
    def load_session_log(self):
        pass

        """
        self.scrollbar = tk.Scrollbar(parent, orient="vertical")
        self.scrollbar.pack(side="right", fill="y")
        self.config(yscrollcommand=self.scrollbar.set)
        self.scrollbar.config(command=self.yview)
                
        self.frame = tk.Frame(self)
        
        self.pack(side="left", fill="both", expand=True)
        self.create_window(0, 0, window=self.frame, anchor='nw')
        
        self.job_hostname = tk.StringVar()
        self.job_hostname.set("self.device_data[self.selection_index]['hostname'")
        self.job_data_title = tk.Label(self.frame, textvariable=self.job_hostname)
        self.job_data_title.place(relwidth=1)
        
        self.job_data_window = ttk.Notebook(self.frame)
        self.job_data_window.place(relwidth=1, relheight=1, y=21)
        self.overview_tab = tk.Frame(self.job_data_window)
        self.job_data_window.add(self.overview_tab, text="Overview")
        self.session_log_tab = tk.Frame(self.job_data_window)
        self.job_data_window.add(self.session_log_tab, text="Session Log")
        
        self.session_log = tk.Text(self.session_log_tab, relief=tk.FLAT, highlightthickness=1, highlightbackground="darkgrey")
        self.session_log.place(relwidth=1, relheight=1, height=-18)
        self.session_log.configure(state='disabled')
        
        parent.update()
        self.config(scrollregion=self.bbox("all"))"""
        
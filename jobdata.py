import tkinter as tk
import tkinter.font as font
from tkinter import ttk
from threading import Thread
import time
import json 
import os

class JobData(tk.Frame):
    
    def __init__(self, parent, root):
        super().__init__(parent)
        self.root = root
        self.frame = tk.Frame(self)
        self.pack(side="left", fill="both", expand=True)
        
        self.selected_font = font.Font(family='Segoe UI', size=12,  weight="bold")
        

        
        self.job_data_window = ttk.Notebook(self)
        self.job_data_window.place(relwidth=1, relheight=1)


        self.job_data_title = tk.Text(self, font=self.selected_font, borderwidth=0)
        self.job_data_title.place(x=295, height=24)

        self.job_data_address = tk.Text(self, font=self.selected_font, borderwidth=0)
        self.job_data_address.place(x=600, height=24)
        
        self.session_log_tab = tk.Frame(self.job_data_window)
        self.job_data_window.add(self.session_log_tab, text="Session Logs")
        
        self.input_data_tab = tk.Frame(self.job_data_window, relief="flat")
        self.job_data_window.add(self.input_data_tab, text="Input Data")

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

    ###
    ### Title functions
    ###

    def update_title(self):
        self.job_data_title.configure(state="normal")
        self.job_data_title.delete(1.0, 'end')
        self.job_data_title.insert(1.0, self.selection_info['hostname'])
        self.job_data_title.configure(state="disabled")

    def update_address(self):
        self.job_data_address.configure(state="normal")
        self.job_data_address.delete(1.0, 'end')
        self.job_data_address.insert(1.0, self.selection_info['address'])
        self.job_data_address.configure(state="disabled")

    ###
    ### Session Log related functions
    ###

    def session_log_updater(self):
        """
        A Threaded instance that constantly updates the selected session log.
        
        """
        
        while True:
            
            if self.selection_info != None: # If something selected
                #if self.selection_info['status'] not in ['pending', 'complete']:
                    
                if self.selection_info['status'] in ['connecting']:
                    self.refresh_session_logs()
                    try:
                        self.session_log_selection.current(0)
                    except:
                        pass
    
                    self.load_session_file(0)
                    self.selection_info = self.root.device_data[self.root.selection_index]
                
                elif self.selection_info['status'] in ['running']:
                    self.refresh_session_logs()
                    self.session_log_selection.current(0)
                    self.append_log_session()
                
                #else:
                try:
                    self.remove_empty_logs()
                except Exception as e:
                    print(f"SESSION FILE UPDATE ERROR: {e}")

                    
            time.sleep(0.2)

    def remove_empty_logs(self):
        all_logs = [log for log in os.listdir(self.selection_info['log_folder'][:-1])][::-1]
        delete_logs = []
        
        for log in all_logs:
            with open(f"{self.selection_info['log_folder']}{log}", 'r') as log_file:
                contents = log_file.readlines()
                #print("   FILE SIZE ",log, len(contents))
                if len(contents) < 1:
                    delete_logs.append(log)
                    
        directory = __file__[:-11].replace('\\', '/')
        for log in delete_logs:
            print("Deleted: ", log)
            os.remove(f"{directory}{self.selection_info['log_folder'][1:]}{log}")

    def refresh_session_logs(self):
        """
        Refreshes the log selection on the JobData/SessionLog Field.
        This will ignore any logs with 'tmp.log' as an extention, as these
        are actually used by netmiko and we will want to delete them if
        for instance there is an auth error. There's no point having loads 
        of empty files.
        """
        all_logs = [log for log in os.listdir(self.selection_info['log_folder'][:-1])][::-1]
        print(self.selection_info['log_folder'])
        for log in all_logs:
            with open(f"{self.selection_info['log_folder']}{log}", 'r') as log_file:
                if log_file.read() == "":
                    all_logs.remove(log)

        self.log_files = all_logs
        self.session_log_selection.configure(values=self.log_files)

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
            print(f"Error opening log... {self.selection_info['hostname']}")

    def load_session_file(self, event):
        try:
            log_file = self.session_log_selection.get()
            with open(f"{self.selection_info['log_folder']}{log_file}", 'r') as log_reader:
                log = log_reader.read()
            self.session_log.configure(state='normal')
            self.session_log.delete('1.0', 'end')
            self.session_log.insert("end", log)
            self.session_log.configure(state='disable')
            self.session_log.see("end")
            self.prev_len = len(log)

        except:
            print(f"Error opening log... {self.selection_info['hostname']}")

    ###
    ### Selection & Data related functions
    ###

    def selection_change(self):
        self.selection_info = self.root.device_data[self.root.selection_index]
        self.update_title()
        self.update_address()
        self.refresh_session_logs()
        
        if len(self.log_files) > 0:
            self.session_log_selection.current(0)
            self.load_session_file(0)

        else:
            self.session_log_selection.set('')
            self.session_log.configure(state='normal')
            self.session_log.delete('1.0', 'end')
            self.session_log.configure(state='disable')

        self.populate_input_data()
        self.populate_return_data()
        self.refresh_needed = False

    def populate_input_data(self):
        for widget in self.input_data_tab.winfo_children():
            widget.destroy()

        for n, entry in enumerate(self.selection_info['additional_data']):
            label = tk.Label(self.input_data_tab, text=entry.replace("ï»¿", ""))

            text = tk.Text(self.input_data_tab, height=1, borderwidth=0)
            text.insert(1.0, self.selection_info['additional_data'][entry])
            text.configure(state="disabled")

            label.grid(row=n, column=0, sticky="e", padx=20)
            text.grid(row=n, column=1)

    def populate_return_data(self):
        self.selection_info = self.root.device_data[self.root.selection_index]

        for widget in self.return_data_tab.winfo_children():
            widget.destroy()

        for n, entry in enumerate(self.selection_info['return_data']):
            print(entry)
            if isinstance(entry, str):
                text = tk.Text(self.return_data_tab, height=1, borderwidth=0)
                text.insert(1.0, entry)
                text.configure(state="disabled")
                text.grid(row=n, column=1)

            #label = tk.Label(self.return_data_tab, text=entry.replace("ï»¿", ""))



            #label.grid(row=n, column=0, sticky="e", padx=20)

        #self.additional_data_text = tk.Text(self.additional_data_frame, relief=tk.FLAT, highlightthickness=1, highlightbackground="grey20", selectbackground="grey90", selectforeground="grey20")
        #self.additional_data_text.place(relheight=1, relwidth=1)
        #self.additional_data_text.configure(state='disabled')
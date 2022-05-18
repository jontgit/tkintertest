import tkinter as tk
import tkinter.filedialog as fd
from tkinter import ttk

import csv
import time
import importlib
import os
import shutil

from threading import Thread
from queue import Queue
from os import listdir

from ide import Editor
from manager import ManagerThread
from namespace_lookup import NamespaceLookup
from jobdata import JobData
from joblist import JobList

class Application(tk.Tk):

    def __init__(self):
        super().__init__()

        self.all_selected = False
        self.debug = True
        self.selection_index = 0
        
        self.title("Cisco Remote Access Program")
        self.iconbitmap("./res/ssh_icon.ico")
        self.geometry("1200x900")

        self.style=ttk.Style()
        self.style.configure("Label", font='TkFixedFont')

        self._load_scripts()

        self.manager_queue = Queue()
        self.complete_queue = Queue()
        self.manager_thread = ManagerThread(self.manager_queue, self.complete_queue).start()
        self.completed_job_thread = Thread(target=self.get_complete_job, daemon=True).start()

        self.lookup_queue = Queue()
        self.namespace_lookup = NamespaceLookup(self, self.lookup_queue).start()

        ###
        ### Menu Bar config
        ###

        self.toolbar = tk.Menu(self)
        self.config(menu = self.toolbar)

        self.file_menu = tk.Menu(self.toolbar, tearoff="off")
        self.toolbar.add_cascade(label="File", menu=self.file_menu)
        self.file_menu.add_command(label="Import CSV", command=self.import_csv)
        self.file_menu.add_command(label="Open Job", command=self.import_csv)

        self.scripts_menu = tk.Menu(self.toolbar, tearoff="off")
        self.toolbar.add_cascade(label="Scripts", menu=self.scripts_menu)
        self.scripts_menu.add_command(label="Create New", command=self.editor_new_file)
        self.scripts_menu.add_command(label="Edit Current", command=self.editor_edit_current_file)
        self.scripts_menu.add_command(label="Edit", command=self.editor_edit_file)
        self.scripts_menu.add_command(label="Delete", command=self.delete_script)

        ###
        ### Main window grid config
        ###
        
        self.grid_rowconfigure(2, weight=1)
        #self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=1)

        ###
        ### Tree/Job View (Left side) config
        ###
        
        self.job_list_frame = tk.Frame(self, bd=1, relief="sunken")
        self.job_list = JobList(self.job_list_frame, self)
        
        ###
        ### Selected Job Data (Right) Config
        ###

        self.job_data_frame = tk.Frame(self)
        self.job_data = JobData(self.job_data_frame, self)
        
        ###
        ### Top bar frame - input bar
        ###

        self.top_bar_frame_1 = tk.Frame(self, height=24)
        # Username
        tk.Label(self.top_bar_frame_1, text=" Username:").grid(row=0, column=0)
        self.username = tk.StringVar()
        self.username_entry = ttk.Entry(self.top_bar_frame_1, width=20, textvariable=self.username).grid(row=0, column=1)
        # Password
        tk.Label(self.top_bar_frame_1, text="   Password:" ).grid(row=0, column=2)
        self.password = tk.StringVar()
        self.password_entry = ttk.Entry(self.top_bar_frame_1, width=20, textvariable=self.password, show="*").grid(row=0, column=3)
        # Job count
        tk.Label(self.top_bar_frame_1, text="   Count:").grid(row=0, column=4)
        self.job_count_entry = ttk.Entry(self.top_bar_frame_1, width=5).grid(row=0, column=5)
        # Job Selection
        tk.Label(self.top_bar_frame_1, text="   Script:").grid(row=0, column=6)

        self.script_list = [ script for script in self.scripts.keys() ]
        self.script_select = ttk.Combobox(self.top_bar_frame_1, state="readonly", values=self.script_list )
        self.script_select.bind("<<ComboboxSelected>>",lambda e: self.top_bar_frame_1.focus())
        self.script_select.current(0)
        self.script_select.grid(row=0, column=7, sticky="ew")

        # Job Selection
        tk.Label(self.top_bar_frame_1, text="   Mode:").grid(row=0, column=8)
        self.connection_mode = ttk.Combobox(self.top_bar_frame_1, state="readonly", values=["SSH", "Telnet"] )
        self.connection_mode.bind("<<ComboboxSelected>>",lambda e: self.top_bar_frame_1.focus())
        self.connection_mode.current(0)
        self.connection_mode.grid(row=0, column=9)

        ###
        ### Top(ish) bar frame, media buttons
        ###

        self.top_bar_frame_2 = tk.Frame(self, height=24)
        # Play button
        self.play_icon = tk.PhotoImage(file = r"./res/play-16.png")
        self.play_button = ttk.Button(self.top_bar_frame_2, image = self.play_icon).grid(row=1, column=0)
        # Pause button
        self.pause_icon = tk.PhotoImage(file = r"./res/pause-16.png")
        self.pause_button = ttk.Button(self.top_bar_frame_2, image = self.pause_icon).grid(row=1, column=1)
        # Pause button
        self.stop_icon = tk.PhotoImage(file = r"./res/stop-16.png")
        self.stop_button = ttk.Button(self.top_bar_frame_2, image = self.stop_icon).grid(row=1, column=2)

        ###
        ### Status bar (Bottom)
        ###

        self.status_bar_frame = tk.Frame(self, height=24)
        self.status = tk.StringVar()
        self.status.set("Idle")
        self.status_title = ttk.Label(self.status_bar_frame, textvariable=self.status)
        self.status_title.grid(row=0, column=0)

        self.top_bar_frame_1.grid(row=0, column=0, columnspan=3, sticky="ew")
        self.top_bar_frame_2.grid(row=1, column=0, columnspan=3, sticky="ew")
        self.job_list_frame.grid(row=2, column=0, columnspan=1, sticky="nsew")
        self.job_data_frame.grid(row=2, column=1, columnspan=2, sticky="nsew")
        self.status_bar_frame.grid(row=3, column=0, columnspan=3, sticky="ew")

        if self.debug:
            self.import_csv()

    def _load_scripts(self):
        self.scripts = {}
        for file in listdir("./scripts/"):
            if file != "__pycache__":
                my_module = importlib.import_module(f"scripts.{file[:-3]}")
                test = my_module.Script("")
                self.scripts[test.title] = my_module


    def update_job_status(self, row, status):
            self.device_data[row]["status"] = status
            self.job_list.update_job_status(row)
            self.update_idletasks()
            
    def get_complete_job(self):
        while True:
            #for i in range(len(selection)):
            complete_job = self.complete_queue.get()
            print(f"Job Complete! {complete_job['hostname']}")
            self.update_job_status(complete_job['index'], complete_job['status'])
            time.sleep(0.1)

    def search_job_csv(self):
        pass    

    def editor_new_file(self):
        self.editor_window = tk.Toplevel(self)
        self.editor = Editor(self.editor_window, title="Untitled - Script Editor")
        self.editor.place(relheight=1, relwidth=1)

    def editor_edit_file(self):
        self.editor_window = tk.Toplevel(self)
        script = self.scripts[self.script_select.get()].Script(0)
        self.editor = Editor(self.editor_window,
                             self,
                             title=script.title, 
                             text=script.base_script,
                             script=script)
        self.editor.place(relheight=1, relwidth=1)

    def editor_edit_current_file(self):
        self.editor_window = tk.Toplevel(self)
        script = self.scripts[self.script_select.get()].Script(0)
        self.editor = Editor(self.editor_window,
                             self,
                             title=script.title, 
                             text=script.base_script,
                             script=script)
        self.editor.place(relheight=1, relwidth=1)

    def delete_script(self):
        pass

    def save_job(self):
        pass    

    def load_job(self):
        pass

    def parse_script(self):
        pass


    def put_job_in_queue(self, selection):

        for host in selection:
            
            self.update_job_status(host, 'running')
            self.manager_queue.put({
                "username" : self.username.get(),
                "password" : self.password.get(),
                "hostname" : self.device_data[host]['hostname'],
                "index" : host,
                "device_type" : "cisco_asa",
                "script" : self.scripts[self.script_select.get()],
                "log_folder" : self.device_data[host]['log_folder'],
                "additional_data" : self.device_data[host]['additional_data']
                }
            )

    def change_focus(self, selection):
        print(selection)
        self.selection_index = selection
        #self.read_session_log()
        self.job_data.selection_change()#.job_hostname.set(self.device_data[self.selection_index]['hostname'])

    def read_session_log(self):
        text = ""
        with open(f"./{self.device_data[self.selection_index]['hostname']}.log", 'r') as session_file:
            text = session_file.read()
        self.session_log.configure(state='normal')
        self.session_log.delete(1.0, "end")
        self.session_log.insert(1.0, text)
        self.session_log.configure(state='disabled')

    def set_status(self, message, type=None):
        self.status.set(message)
        self.update_idletasks()

    def import_csv(self):
        """
        Creates a new job in the jobs folder, if a name
        has not been specified, just uses the name job_n
        n being the amount of non-named jobs.

        Creates a folder structure as below: 
        job_1
            jobdata.json
            debug.log
            input
            `---input_data.csv
            logs
            |---device_1
            |   `---&Y-&M-&D-&H-&M-&S---device_1.log
            `---device_2
                `---&Y-&M-&D-&H-&M-&S---device_2.log
                `---&Y-&M-&D-&H-&M-&S---device_2.log
            script
            `---script.py
    
        """

        if not self.debug:
            self.set_status("Loading Data...")
            filename = fd.askopenfilename()
        else:
            filename = "test.csv"

        if filename[-3:] == 'csv':
            self.device_data = []

            #self.create_job(filename)

            with open(filename, 'r') as csv_file:

                input_data = csv.DictReader(csv_file)
                
                for n, entry in enumerate(input_data):
                    additional_data = {}
                    hostname = ""
                    for key in entry.keys():
                        if key in ['hostname', 'DisplayName', 'hostname']:
                            hostname = entry[key]
                        else:
                            additional_data[key] = entry[key]
                    
                    self.device_data.append({
                        'active' : True,
                        'hostname' : hostname,
                        'address' : 'N/a',
                        'status' : 'pending',
                        'index' : n,
                        'log_folder' : f"./jobs/{filename[:-4]}/logs/{hostname}/",
                        'additional_data' : additional_data
                    })
                
            if filename[:-4] not in listdir("./jobs/"):
                os.makedirs(f"./jobs/{filename[:-4]}")
                os.makedirs(f"./jobs/{filename[:-4]}/input")
                os.makedirs(f"./jobs/{filename[:-4]}/logs")
                os.makedirs(f"./jobs/{filename[:-4]}/script")

            if not os.path.exists(f"./jobs/{filename[:-4]}/input/{filename}"):
                shutil.copyfile(filename, f"./jobs/{filename[:-4]}/input/{filename}")

            for device in self.device_data:
                self.lookup_queue.put(device)

                if not os.path.exists(f"./jobs/{filename[:-4]}/logs/{device['hostname']}"):
                    os.makedirs(f"./jobs/{filename[:-4]}/logs/{device['hostname']}")
                
            self.job_list.load_data(self.device_data)
            self.set_status(f"Loaded Data. ({len(self.device_data)} Devices)")
            self.change_focus(0)
            #self.status.set("Idle")

if __name__ == "__main__":
    root = Application()
    root.mainloop()
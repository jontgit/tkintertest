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
from entry import CustomEntry
from option_menu import CustomOptionMenu
from export_menu import ExportMenu

# TODO 
#################
# DONE    - DUPLICATE ENTRIES 
# DONE    - file error handling 
# DONE    - Unreachable - Set disabled
# DONE    - Sort by status
# PARTIAL - Export Results/Job Status (Save Job)
#         - Job System (Job files, save status)
#         - Media Buttons (Run, Run All, Pause)
#         - Preferences/Settings
#         - Input data for jobs 
#         - Return data from jobs
# PARTIAL - Custom job status from scripts
#         - Tooltips

# BUG
#################
#         - Colour isn't right on unreachable jobs after being selected
#         - Job log is created even if don't connect - will need custom log handling
#         - IP addr doesn't update unless clicked on
#         - Focused job doesn't change upon status filter selection

class Application(tk.Tk):

    def __init__(self):
        """
        This is the base application class. This class is passed to many 
        sub-classes as 'root', where function calls and variable changes
        can be made to the application as a whole.
        """
        
        super().__init__()
        self.tk.call("source", "./res/theme/azure.tcl")
        self.button_height = 35
        self.tk.call("set_theme", "dark")

        self.debug = True
        self.selection_index = 0
        self.darkmode = True
        
        self.title("mHOSE")#"Multi Host Orchistrated Session Environment")
        self.iconbitmap("./res/main/icon.ico")
        self.geometry("1200x700")

        self._load_scripts()

        self.style = ttk.Style()

        ###
        ### Scart daemon threads
        ###

        self.manager_queue = Queue()
        self.complete_queue = Queue()
        self.manager_thread = ManagerThread(self.manager_queue, self.complete_queue, self)
        self.completed_job_thread = Thread(target=self.get_complete_job, daemon=True)
        self.manager_thread.start()
        self.completed_job_thread.start()

        self.lookup_queue = Queue()
        self.namespace_lookup = NamespaceLookup(self, self.lookup_queue)
        self.namespace_lookup.start()

        ###
        ### Menu Bar config
        ###

        # File Menu
        
        self.toolbar = tk.Menu(self)
        self.config(menu = self.toolbar)

        self.file_menu = tk.Menu(self.toolbar, tearoff="off")
        self.toolbar.add_cascade(label="File", menu=self.file_menu)
        self.file_menu.add_command(label="Import CSV", command=self.request_file)
        self.file_menu.add_command(label="Open Job", command=self.request_file)
        
        # Script Menu

        self.scripts_menu = tk.Menu(self.toolbar, tearoff="off")
        self.toolbar.add_cascade(label="Scripts", menu=self.scripts_menu)
        self.scripts_menu.add_command(label="Create New", command=self.editor_new_file)
        self.scripts_menu.add_command(label="Edit Current", command=self.editor_edit_current_file)
        self.scripts_menu.add_command(label="Edit", command=self.editor_edit_file)
        self.scripts_menu.add_command(label="Delete", command=self.delete_script)
        
        # Settings Menu

        self.settings_menu = tk.Menu(self.toolbar, tearoff="off")
        self.toolbar.add_cascade(label="Settings", menu=self.settings_menu)
        self.settings_menu.add_command(label="Preferences", command=self.editor_new_file)
        self.settings_menu.add_command(label="Style", command=self.editor_edit_current_file)

        ###
        ### Tree/Job View (Left side) config
        ###
        
        self.job_list_frame = tk.Frame(self)#, bd=1, relief="sunken")
        self.job_list = JobList(self.job_list_frame, self)
        
        ###
        ### Selected Job Data (Right) Config
        ###

        self.job_data_frame = tk.Frame(self)
        self.job_data = JobData(self.job_data_frame, self)
        
        ###
        ### Top bar frame - input bar
        ###

        self.top_bar_frame_1 = tk.Frame(self)

        self.top_bar_frame_1_left = tk.Frame(self.top_bar_frame_1)
        self.top_bar_frame_1_left.place(y=0, x=0, height=35)


        self.top_bar_frame_1_right = tk.Frame(self.top_bar_frame_1)
        self.top_bar_frame_1_right.place(y=0, x=580, height=35)


        # Username
        self.username = tk.StringVar()
        self.username_entry = CustomEntry(self.top_bar_frame_1_left, self.username, "Username...", "")
        self.username_entry.grid(row=0, column=0, padx=1)
        
        # Password
        self.password = tk.StringVar()
        self.password_entry = CustomEntry(self.top_bar_frame_1_left, self.password, "Password...", "*")
        self.password_entry.grid(row=0, column=1, padx=1)

        # Enable Password

        self.enable_password_bool = tk.IntVar()
        self.enable_password_bool.set(0)
        self.enable_password = tk.StringVar()
        self.enable_password_entry = CustomEntry(self.top_bar_frame_1_left, self.enable_password, "Enable...", "*")
        self.enable_password_entry.grid(row=0, column=2, padx=1)
        self.enable_password_entry.grid_remove()
        self.enable_pass = ttk.Checkbutton(
                    self.top_bar_frame_1_left, variable=self.enable_password_bool,
                    command=self.enable_entry,
                    onvalue = 1, offvalue = 0,
                    text="Enable", style="Switch.TCheckbutton"
                )
        self.enable_pass.grid(row=0, column=3, padx=1)


        # Job count
        #tk.Label(self.top_bar_frame_1, text="   Count:").grid(row=0, column=4)
        #self.job_count_entry = ttk.Entry(self.top_bar_frame_1, width=5).grid(row=0, column=5)
        
        # Job Selection
        tk.Label(self.top_bar_frame_1_right, text="   Script:").grid(row=0, column=6)

        self.script_list = [ script for script in self.scripts.keys() ]
        self.script_var = tk.StringVar(value="Script...")
        #self.script_select = ttk.OptionMenu(self.top_bar_frame_1_right, self.script_var, *self.script_list )
        self.script_select = ttk.Combobox(self.top_bar_frame_1_right, state="readonly", values=self.script_list )
        self.script_select.current(0)
        self.script_select.grid(row=0, column=7, sticky="nsew")

        # Job Selection
        tk.Label(self.top_bar_frame_1_right, text="   Mode:").grid(row=0, column=8)
        self.connection_mode = ttk.Combobox(self.top_bar_frame_1_right, state="readonly", values=["SSH", "Telnet"] )
        #self.connection_mode.bind("<<ComboboxSelected>>",lambda e: self.top_bar_frame_1.focus())
        self.connection_mode.current(0)
        self.connection_mode.grid(row=0, column=9)

        ###
        ### Top(ish) bar frame, media buttons
        ###

        self.top_bar_frame_2 = tk.Frame(self, height=24)
        self.top_bar_frame_2.columnconfigure(0, weight=1)
        self.top_bar_frame_2.columnconfigure(1, weight=1)
        self.top_bar_frame_2.columnconfigure(2, weight=1)
        self.top_bar_frame_2.columnconfigure(3, weight=1)
        #self.top_bar_frame_2.columnconfigure(4, weight=1)


        # Darkmode button
        #self.lightmode_icon = tk.PhotoImage(file = r"./res/main/sun.png")
        #self.darkmode_button = ttk.Button(self.top_bar_frame_2, image=self.lightmode_icon, command=self.toggle_darkmode).grid(row=1, column=0, padx=1)
        # Export button
        self.export_icon = tk.PhotoImage(file = r"./res/main/download_w.png")
        self.export_button = ttk.Button(self.top_bar_frame_2, image=self.export_icon, command=self.export_current)
        self.export_button.grid(row=1, column=0, padx=1, sticky="nsew")

        # Run button
        self.run_icon = tk.PhotoImage(file = r"./res/main/run_w.png")
        self.run_button = ttk.Button(self.top_bar_frame_2, image=self.run_icon)
        self.run_button.grid(row=1, column=1, padx=1, sticky="nsew")

        # Run All button
        self.run_all_icon = tk.PhotoImage(file = r"./res/main/run_all_w.png")
        self.run_all_button = ttk.Button(self.top_bar_frame_2, image=self.run_all_icon)
        self.run_all_button.grid(row=1, column=2, padx=1, sticky="nsew")

        # Pause button
        self.pause_icon = tk.PhotoImage(file = r"./res/main/pause_w.png")
        self.pause_button = ttk.Button(self.top_bar_frame_2, image=self.pause_icon)
        self.pause_button.grid(row=1, column=3, padx=1, sticky="nsew")

        ###
        ### Status bar (Bottom)
        ###

        self.status_bar_frame = tk.Frame(self, height=self.button_height)
        self.status = tk.StringVar()
        self.status.set("Idle")
        self.status_title = ttk.Label(self.status_bar_frame, textvariable=self.status, foreground="grey90")
        self.status_title.grid(row=0, column=0)

        self.top_bar_frame_1.place(x=4, y=2, relwidth=1, width=-4, height=35)
        self.top_bar_frame_2.place(x=4, y=self.button_height+2, width=396)
        self.job_list_frame.place(x=0, y=(self.button_height*2)+2, relheight=1, height=-self.button_height*2-25, width=400)
        self.job_data_frame.place(x=400, y=(self.button_height*2)+2, relheight=1, height=-self.button_height*2-25, relwidth=1, width=-402)
        self.status_bar_frame.pack(side="bottom", fill="x")

        if self.debug:
            self.request_file("test.csv")
        
    ###
    ### General GUI Update functions
    ###
    
    def enable_entry(self):
        if self.enable_password_bool.get() == 1:
            self.enable_password_entry.grid(row=0, column=2, padx=1)
        else:
            self.enable_password_entry.grid_remove()


    def toggle_darkmode(self):
        if self.darkmode:   # go lightmode
            self.darkmode_icon = tk.PhotoImage(file = r"./res/main/moon.png")
            self.tk.call("set_theme", "light")
            self.darkmode_button.configure(image=self.darkmode_icon)
        else:               # go darkmode
            self.lightmode_icon = tk.PhotoImage(file = r"./res/main/sun.png")
            self.tk.call("set_theme", "dark")
            self.darkmode_button.configure(image=self.lightmode_icon)
        self.darkmode = not self.darkmode
            
    def set_program_status(self, message):
        """
        Sets the status in the bottom left to the message provided.
        Usefull to confirm when work is actually occurring and the
        program hasn't just hung.

        Args:
            message (str): Message to update
        """
        self.status.set(message)
        self.update_idletasks()

    def update_job_status(self, row, status):
        """
        Updates a specific row within the job list (left side). This
        is generally used by the worker threads to update the progress
        of specific jobs.

        Args:
            row (int): Index of the row to update.
            status (str): what to set the status to.
        """
        self.device_data[row]["status"] = status
        self.job_list.update_job_status(row)
        self.update_idletasks()
            
    def change_focus(self, selection):
        self.selection_index = selection
        self.job_data.selection_change()
        
    ###
    ### Editor/Script related functions
    ###

    def _load_scripts(self):
        self.scripts = {}
        self.base_script = importlib.import_module(f"base_script")
        for file in listdir("./scripts/"):
            if file != "__pycache__":
                my_module = importlib.import_module(f"scripts.{file[:-3]}")
                test = my_module.Script("")
                self.scripts[test.title] = my_module

    def editor_new_file(self):
        self.editor_window = tk.Toplevel(self)
        script = self.base_script.Script(0)
        self.editor = Editor(self.editor_window,
                             self,
                             script=script)
        self.editor.place(relheight=1, relwidth=1)

    def editor_edit_file(self):
        self.editor_window = tk.Toplevel(self)
        script = self.scripts[self.script_select.get()].Script(0)
        self.editor = Editor(self.editor_window,
                             self,
                             script=script)
        self.editor.place(relheight=1, relwidth=1)

    def editor_edit_current_file(self):
        self.editor_window = tk.Toplevel(self)
        script = self.scripts[self.script_select.get()].Script(0)
        self.editor = Editor(self.editor_window,
                             self,
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
    
    ###
    ### Job Thread functions
    ###

    def get_complete_job(self):
        while True:
            #for i in range(len(selection)):
            complete_job = self.complete_queue.get()
            print(f"Job Complete! {complete_job['hostname']}")
            #if complete_job['status'] == "complete":
            self.job_data.load_session_file(0)
            self.update_job_status(complete_job['index'], complete_job['status'])
            time.sleep(0.1)

    def put_job_in_queue(self, selection):

        if self.enable_password_bool.get():
            enable_pass = self.enable_password.get()
        else:
            enable_pass = self.password.get()

        for host in selection:
            
            self.update_job_status(host, 'connecting')
            self.manager_queue.put({
                "username" : self.username.get(),
                "password" : self.password.get(),
                "enable" : enable_pass,
                "hostname" : self.device_data[host]['hostname'],
                "index" : host,
                "device_type" : "cisco_asa",
                "script" : self.scripts[self.script_select.get()],
                "log_folder" : self.device_data[host]['log_folder'],
                "additional_data" : self.device_data[host]['additional_data']
                }
            )

    ###
    ### File/Job Load functions
    ###
    
    def export_current(self):
        ExportMenu(self, self.filename)

    def request_file(self, filename=None):
        if filename == None:
            filename = fd.askopenfilename()
        self.import_csv(filename)

    def import_csv(self, filepath):
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
        filename = filepath.split("/")[-1]

        if filename[-3:] == 'csv':
            self.filename = filename
            self.device_data = []

            #self.create_job(filename)

            with open(filepath, 'r') as csv_file:

                input_data = csv.DictReader(csv_file)
                
                index = 0
                for entry in input_data:
                    additional_data = {}
                    hostname = ""
                    for key in entry.keys():
                        if key in ['hostname', 'DisplayName', 'hostname']:
                            hostname = entry[key]
                        else:
                            additional_data[key] = entry[key]
                    
                    if hostname not in [ host['hostname'] for host in self.device_data ]:
                        self.device_data.append({
                            'active' : True,
                            'hostname' : hostname,
                            'address' : 'N/a',
                            'status' : 'pending',
                            'index' : index,
                            'log_folder' : f"./jobs/{filename[:-4]}/logs/{hostname}/",
                            'additional_data' : additional_data
                        })
                        index += 1

                print(len(self.device_data), index)
                
            if filename[:-4] not in listdir("./jobs/"):
                os.makedirs(f"./jobs/{filename[:-4]}")
                os.makedirs(f"./jobs/{filename[:-4]}/input")
                os.makedirs(f"./jobs/{filename[:-4]}/logs")
                os.makedirs(f"./jobs/{filename[:-4]}/script")
                os.makedirs(f"./jobs/{filename[:-4]}/tmp")

            if not os.path.exists(f"./jobs/{filename[:-4]}/input/{filename}"):
                shutil.copyfile(filename, f"./jobs/{filename[:-4]}/input/{filename}")

            for device in self.device_data:
                self.lookup_queue.put(device)

                if not os.path.exists(f"./jobs/{filename[:-4]}/logs/{device['hostname']}"):
                    os.makedirs(f"./jobs/{filename[:-4]}/logs/{device['hostname']}")
                
            self.job_list.load_data(self.device_data)
            self.set_program_status(f"Loaded Data. ({len(self.device_data)} Devices)")
            self.change_focus(0)
            #self.status.set("Idle")

if __name__ == "__main__":
    root = Application()
    root.mainloop()
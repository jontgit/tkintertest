import tkinter as tk
from tkinterdnd2 import *
import tkinter.filedialog as fd
from tkinter import ttk

import csv
import time
import importlib
import os
import shutil
import json

from threading import Thread, Event
from queue import Queue
from os import listdir
from functools import partial

from ide import Editor
from manager import ManagerThread
from namespace_lookup import NamespaceLookup
from jobdata import JobData
from joblist import JobList
from joblist import ListFilter
from entry import CustomEntry
from option_menu import CustomOptionMenu
from export_menu import ExportMenu
from tooltip import CreateToolTip

# TODO 
#################
# DONE    - DUPLICATE ENTRIES 
# DONE    - file error handling 
# DONE    - Unreachable - Set disabled
# DONE    - Sort by status
# DONE    - Export Results/Job Status (Still need to export to JSON)
# DONE    - Custom job status from scripts (will need to change the way icon images are handled in the job list)
# DONE    - Input data for jobs 
# DONE    - Return data from jobs
# PARTIAL - Job System (Export/import job files)
# DONE    - Media Buttons (Run, Run All, Pause) - Only pause left to do
# DONE    - Tooltips
# DONE    - Right Click menu buttons (Reset, clear, open ssh connection)
# DONE    - Drag and Drop Support for CSV/JSON input
#         - IDE Improvements (Script generator syntax, hotkeys, syntax highlighting, line numbers, default script)
#         - Preferences/Settings

# BUG
#################
# FIXED   - Colour isn't right on unreachable jobs after being selected
# FIXED   - Sessions don't refresh properly when job running
# FIXED   - Job log is created even if don't connect - will need custom log handling
# FIXED   - IP addr doesn't update unless clicked on
#         - Focused job doesn't change upon status filter selection
# FIXED   - Unreachable Updates don't change colour/Status
# FIXED   - DNS lookup still tries to update even if filter is inplace
# FIXED   - Importing csv doesn't fully clear the joblist

class Application(TkinterDnD.Tk):

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
        self.pause = False
        self.pause_event = Event()
        self.selection_index = 0
        self.darkmode = True
        
        self.title("mHOSE")#"Multi Host Orchistrated Session Environment")
        self.iconbitmap("./res/main/icon.ico")
        self.geometry("1200x700")
        
        self.drop_target_register(DND_FILES)
        self.dnd_bind('<<Drop>>', self.import_file)

        self._load_scripts()

        self.style = ttk.Style()

        ###
        ### Scart daemon threads
        ###

        self.manager_queue = Queue()
        self.complete_queue = Queue()
        self.manager_thread = ManagerThread(self.manager_queue, self.complete_queue, self, self.pause_event)
        self.completed_job_thread = Thread(target=self.get_complete_job, daemon=True)
        self.manager_thread.start()
        self.completed_job_thread.start()

        self.lookup_queue = Queue()
        self.namespace_lookup = NamespaceLookup(self, self.lookup_queue)
        self.namespace_lookup.start()

        self.option_add("*TCombobox*Listbox*Background", 'grey40')
        self.option_add("*TCombobox*Listbox*Foreground", 'grey90')
        self.option_add('*Menu*Listbox.Justify', 'center') 

        ###
        ### Menu Bar config
        ###

        # File Menu
        
        self.toolbar = tk.Menu(self)
        self.config(menu = self.toolbar)

        self.file_menu = tk.Menu(self.toolbar, tearoff="off")
        self.toolbar.add_cascade(label="File", menu=self.file_menu)
        self.file_menu.add_command(label="Import File", command=self.request_file)
        self.file_menu.add_command(label="Export File", command=self.request_file)
        self.file_menu.add_separator()
        self.update_file_menu()
        
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
        
        self.list_filter_frame = tk.Frame(self)
        self.list_filter = ListFilter(self.list_filter_frame, self)
        self.list_filter.place(relheight=1, relwidth=1)
        
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
        self.top_bar_frame_1_left.place(y=0, x=0, height=35, relwidth=1)


        #self.top_bar_frame_1_right = tk.Frame(self.top_bar_frame_1)
        #self.top_bar_frame_1_right.place(y=0, x=580, height=35)

        # Job count
        #tk.Label(self.top_bar_frame_1, text="   Count:").grid(row=0, column=4)
        #self.job_count_entry = ttk.Entry(self.top_bar_frame_1, width=5).grid(row=0, column=5)
        
        # Job Selection
        #tk.Label(self.top_bar_frame_1_right, text="   Script:").grid(row=0, column=6)

        self.script_list = [ script for script in self.scripts.keys() ]
        self.script_list.insert(0, "Script...")
        self.script_var = tk.StringVar(value="Script...")
        self.script_select = ttk.Combobox(self.top_bar_frame_1_left, justify='center', state="readonly", values=self.script_list)#, validate="focusout", validatecommand=self.check_entry)
        self.script_select.current(0)
        self.script_select.place(x=1, width=196)
        self.script_select_ttp = CreateToolTip(self.script_select, "Script selection")
        #self.script_select.grid(row=0, column=7, sticky="nsew")
        self.script_select.bind("<<ComboboxSelected>>", self.change_script_selection)
        self.script_select.option_add('*TCombobox*Listbox.Justify', 'center') 

        # Job Selection
        self.device_types = {
            "Juniper Junos" : "juniper_junos",
            "Mellanox" : "mellanox",
            "Fortigate" : "fortinet",
            "Cisco IOS" : "cisco_ios",
            "Cisco ASA" : "cisco_asa",
            "Arista EOS" : "arista_eos",
            "Juniper Junos Telnet" : "juniper_junos_telnet",
            "Cisco IOS Telnet" : "cisco_ios_telnet",
            "Arista EOS Telnet" : "arista_eos_telnet"
        }
        
        #tk.Label(self.top_bar_frame_1_right, text="   Mode:").grid(row=0, column=8)
        self.device_selection = list(self.device_types.keys())
        self.device_selection.insert(0, "Device Type...")
        self.device_selection_entry = ttk.Combobox(self.top_bar_frame_1_left, justify='center', state="readonly", values=self.device_selection)
        self.device_selection_entry.current(0)
        self.device_selection_entry.place(x=199, width=196)
        self.device_selection_entry_ttp = CreateToolTip(self.device_selection_entry, "Device type")
        self.device_selection_entry.bind("<<ComboboxSelected>>", self.change_device_selection)
        self.device_selection_entry.option_add('*TCombobox*Listbox.Justify', 'center') 
        #self.device_selection_entry.grid(row=0, column=9, padx=2)





        # Username
        self.username = tk.StringVar()
        self.username_entry = CustomEntry(self.top_bar_frame_1_left, self.username, "Username...", "")
        self.username_entry.place(x=397, width=170)
        self.username_entry_ttp = CreateToolTip(self.username_entry, "Username for SSH")
        #self.username_entry.grid(row=0, column=0, padx=1)
        
        # Password
        self.password = tk.StringVar()
        self.password_entry = CustomEntry(self.top_bar_frame_1_left, self.password, "Password...", "*")
        self.password_entry.place(x=569, width=170)
        self.password_entry_ttp = CreateToolTip(self.password_entry, "Password for SSH")
        #self.password_entry.grid(row=0, column=1, padx=1)

        # Enable Password

        self.enable_password_grid = tk.Frame(self.top_bar_frame_1_left)
        self.enable_password_grid.place(x=740, height=35)
        self.enable_password_bool = tk.IntVar()
        self.enable_password_bool.set(0)
        self.enable_password = tk.StringVar()
        self.enable_password_entry = CustomEntry(self.enable_password_grid, self.enable_password, "Enable...", "*")
        self.enable_password_entry.grid(row=0, column=0, padx=1, sticky="nesw")
        self.enable_password_entry_ttp = CreateToolTip(self.enable_password_entry, "Enable for SSH")
        self.enable_password_entry.grid_remove()
        self.enable_pass = ttk.Checkbutton(
                    self.enable_password_grid, variable=self.enable_password_bool,
                    command=self.enable_entry,
                    onvalue = 1, offvalue = 0,
                    text="Enable", style="Switch.TCheckbutton"
        )
        self.enable_pass_ttp = CreateToolTip(self.enable_pass, "Different Enable password to primary password")
        self.enable_pass.grid(row=0, column=3, padx=1, sticky="nesw")

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
        self.export_button_ttp = CreateToolTip(self.export_button, "Export job data")

        # Run button
        self.run_icon = tk.PhotoImage(file = r"./res/main/run_one.png")
        self.run_button = ttk.Button(self.top_bar_frame_2, image=self.run_icon, command=self.run_next)
        self.run_button.grid(row=1, column=1, padx=1, sticky="nsew")
        self.run_button_ttp = CreateToolTip(self.run_button, "Add next pending to queue")

        # Run All button
        self.run_all_icon = tk.PhotoImage(file = r"./res/main/run_all.png")
        self.run_all_button = ttk.Button(self.top_bar_frame_2, image=self.run_all_icon, command=self.run_all)
        self.run_all_button.grid(row=1, column=2, padx=1, sticky="nsew")
        self.run_all_button_ttp = CreateToolTip(self.run_all_button, "Add all pending to queue")

        # Pause button
        self.play_icon = tk.PhotoImage(file = r"./res/main/play_w.png")
        self.pause_icon = tk.PhotoImage(file = r"./res/main/pause_w.png")
        self.pause_button = ttk.Button(self.top_bar_frame_2, image=self.pause_icon, command=self.pause_command)
        self.pause_button.grid(row=1, column=3, padx=1, sticky="nsew")
        self.pause_button_ttp = CreateToolTip(self.pause_button, "Pause")

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
        self.list_filter_frame.place(x=5, y=(self.button_height*2)+1, height=self.button_height, width=400)
        self.job_list_frame.place(x=0, y=(self.button_height*3)+2, relheight=1, height=-self.button_height*3-25, width=400)
        self.job_data_frame.place(x=401, y=(self.button_height*1)+2, relheight=1, height=-self.button_height*1-25, relwidth=1, width=-404)
        self.status_bar_frame.pack(side="bottom", fill="x")

        if self.debug:
            self.username.set("test")
            self.password.set("test")
            self.script_select.current(2)
            self.device_selection_entry.current(5)
            self.request_file("test.csv")
        
    ###
    ### General GUI Update functions
    ###

    def import_file(self, event):
        if event.data.endswith(".csv") or event.data.endswith(".job"):
            self.import_csv(event.data)

    def pause_command(self):
        self.pause = not self.pause
        
        if not self.pause:
            self.pause_button.config(image=self.pause_icon)
            self.pause_event.clear()
        else:
            self.pause_button.config(image=self.play_icon)
            self.pause_event.set()
        #self.pause_event.s
        print(f"Paused: {self.pause}")
        
    def run_all(self):
        if self.check_entry():
            while True:
                for n, device in enumerate(self.device_data):
                    if device['status'] == "pending":
                        self.put_job_in_queue([n])
                break    

    def run_next(self):
        if self.check_entry():
            while True:
                for n, device in enumerate(self.device_data):
                    if device['status'] == "pending":
                        self.put_job_in_queue([n])
                        break
                break

    def update_file_menu(self):
        directory = __file__[:-15].replace("\\", "/")
        for folder in os.listdir(f"{directory}/jobs"):
            self.file_menu.add_command(label=folder, command=partial(self.open_job, folder))
            
    def open_job(self, folder):
        directory = __file__[:-15].replace("\\", "/")
        #print(f"{directory}/jobs/{folder}/input/{folder}.csv")
        self.request_file(f"{directory}/jobs/{folder}/input/{folder}.csv")
        
    def refresh_file_menu(self):
        #self.file_menu.destroy()
        self.update_file_menu()

    def check_entry(self):
        valid = True
        
        # Check Username
        if self.username.get() == "Username...":
            self.username_entry.state(["invalid"])
            valid = False
            
        if self.password.get() == "Password...":
            self.password_entry.state(["invalid"])
            valid = False
            
        if self.enable_password_bool.get():
            if self.enable_password.get() == "Enable...":
                self.enable_password_entry.state(["invalid"])
                valid = False
            
        if self.script_select.get() == "Script...":
            self.script_select.state(["invalid"])
            valid = False
            
        if self.script_select.get() == "Script...":
            self.script_select.state(["invalid"])
            valid = False
            
        if self.device_selection_entry.get() == "Device Type...":
            self.device_selection_entry.state(["invalid"])
            valid = False
            
        return valid

    def change_script_selection(self, event):
        self.script_select.selection_clear()
        
    def change_device_selection(self, event):
        self.device_selection_entry.selection_clear()

    def check_device_filter(self, index):
        pass
        """if self.device_data[index]['status'].capitalize() == self.job_list.status_header.get() or\
            self.job_list.status_header.get() == "Status":
            return True
        else:
            return False"""

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

    #def update_job_icon(self, row, icon):
    #    self.job_list.jobs[row][1].configure(image=self.job_list.active_status_images[icon])
    #    self.update_idletasks()

    #def update_job_status(self, row, status):
        """
        Updates a specific row within the job list (left side). This
        is generally used by the worker threads to update the progress
        of specific jobs.

        Args:
            row (int): Index of the row to update.
            status (str): what to set the status to.
        """
        
    #    self.device_data[row]["status"] = status
    #    self.job_list.jobs[row][2].configure(text=self.device_data[row]['status'].capitalize())
        #self.device_data[row]["status"] = status
        #self.job_list.update_job_status(row, icon)
        
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
            while not self.complete_queue.empty():
                complete_job = self.complete_queue.get()
                self.device_data[complete_job['index']]['return_data'] = complete_job['return_data']
                print(f"Job Complete! {complete_job['hostname']}")
                #print(json.dumps(self.device_data[complete_job['index']], indent=4))

                self.job_data.load_session_file(0)
                self.job_data.populate_return_data()
                
                self.job_list.update_job_status(complete_job['index'], complete_job['status'])
                self.job_list.update_job_icon(complete_job['index'], complete_job['icon'])
                
                self.write_job_data()
            time.sleep(0.1)

    def put_job_in_queue(self, selection):
        if self.check_entry():

            if self.enable_password_bool.get():
                enable_pass = self.enable_password.get()
            else:
                enable_pass = self.password.get()

            for host in selection:
                
                self.job_list.update_job_status(host, 'queued')
                self.job_list.update_job_icon(host, 'queued')
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
    
    def parse_return_data(self, device):
        
        export_line = [device['hostname'], device['status']]
        
        if device['return_data'] != "":
            if isinstance(device['return_data'], str):
                export_line.append(device['return_data'])
                
                
            elif isinstance(device['return_data'], list):
                #for entry in device['return_data']:
                export_line.append(f"\"{','.join(device['return_data'])}\"")
                    
                    
            elif isinstance(device['return_data'], dict):
                export_line.append(f"{json.dumps(device['return_data'])}")    
        
        return export_line
                
    def export_current(self):
        csv_file = fd.asksaveasfilename(initialdir = "/<file_name>", defaultextension='.csv', filetypes=(("CSV File", "*.csv"), ("JSON File", "*.json")))
        
        if csv_file[-4:] == ".csv": # CSV 
            export_data = [['Hostname', 'Status']]
            
            _filter = self.list_filter.status_header.get()
            if _filter == "Status": # No Filter
                for device in self.device_data:
                    export_data.append(self.parse_return_data(device))

            else:
                for device in self.device_data:
                    if device['status'] == _filter:
                        export_data.append(self.parse_return_data(device))


            with open(f"{csv_file}", 'w') as csv_file:
                for line in export_data:
                    csv_file.write(f"{','.join(line)}\n")

        else:                       # JSON
            export_data = []
            for device in self.device_data:
                export_data.append({
                    "hostname" : device['hostname'],
                    "status" : device['status'],
                    "output" : device['return_data']
                })
            
            
            with open(f"{csv_file}", 'w') as csv_file:
                csv_file.write(json.dumps(export_data, indent=4))

    def request_file(self, filename=None):
        if filename == None:
            filename = fd.askopenfilename(title="Import data file...", filetypes=(("CSV File", "*.csv"), ("JSON File", "*.json")))
        self.import_csv(filename)

    def write_job_data(self):
        try:
            with open(f"./jobs/{self.filename}/jobdata.json", 'w') as job_data_file:
                job_data = {
                    "username" : self.username.get(),
                    "enable_mode" : self.enable_password_bool.get(),
                    "script" : self.script_select.current(),
                    "device_type" : self.device_selection_entry.current(),
                    "device_data" : self.device_data
                }
                job_data_file.write(json.dumps(job_data))
        except:
            pass

    def read_job_data(self):
        with open(f"./jobs/{self.filename}/jobdata.json", 'r') as job_data_file:
            job_data = json.load(job_data_file)
            self.username.set(job_data['username'])
            self.enable_password_bool.set(job_data['enable_mode'])
            self.script_select.current(job_data['script'])
            self.device_selection_entry.current(job_data['device_type'])
            self.device_data = job_data['device_data']
            
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
            self.filename = filename[:-4]
            self.device_data = []

            if self.filename not in listdir("./jobs/"):
                os.makedirs(f"./jobs/{self.filename}")
                os.makedirs(f"./jobs/{self.filename}/input")
                os.makedirs(f"./jobs/{self.filename}/logs")
                os.makedirs(f"./jobs/{self.filename}/script")
                os.makedirs(f"./jobs/{self.filename}/tmp")
            #self.create_job(filename)

                with open(filepath, 'r') as csv_file:

                    input_data = csv.DictReader(csv_file)
                    
                    index = 0
                    for entry in input_data:
                        additional_data = {}
                        hostname = ""
                        for key in entry.keys():
                            if key in ['hostname', 'DisplayName', 'Hostname']:
                                hostname = entry[key]
                            else:
                                additional_data[key] = entry[key]
                        
                        if hostname not in [ host['hostname'] for host in self.device_data ]:
                            self.device_data.append({
                                'active' : True,
                                'hostname' : hostname,
                                'address' : 'N/a',
                                'status' : 'pending',
                                'icon' : 'pending',
                                'index' : index,
                                'log_folder' : f"./jobs/{self.filename}/logs/{hostname}/",
                                'additional_data' : additional_data,
                                'return_data' : ""
                            })
                            index += 1
                    


                if not os.path.exists(f"./jobs/{self.filename}/input/{filename}"):
                    shutil.copyfile(filepath, f"./jobs/{self.filename}/input/{filename}")

                for device in self.device_data:
                    self.lookup_queue.put(device)

                    if not os.path.exists(f"./jobs/{self.filename}/logs/{device['hostname']}"):
                        os.makedirs(f"./jobs/{self.filename}/logs/{device['hostname']}")
                    
                self.job_list.load_data(self.device_data)
                self.set_program_status(f"Loaded Data. ({len(self.device_data)} Devices)")
                
                self.write_job_data()
                self.refresh_file_menu()
                self.change_focus(0)
                
            else:
                self.read_job_data()
                self.job_list.load_data(self.device_data)
                for device in self.device_data:
                    if device['address'] == "N/a":
                        self.lookup_queue.put(device)

                self.change_focus(0)
            

if __name__ == "__main__":
    root = Application()
    root.mainloop()
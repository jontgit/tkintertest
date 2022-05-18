import tkinter as tk
import tkinter.filedialog as fd
from tkinter import ttk

import tkinter.font as font
#from lib.pythonping import ping
import csv
import json
import re
import socket
import time
import sys
import yaml
import importlib
import os
import shutil
import datetime

from threading import Thread
from queue import Queue
from os import listdir

from ide import Editor

from netmiko import (
    ConnectHandler,
    NetmikoTimeoutException,
    NetmikoAuthenticationException,
)

CONCURRENT_SSH_LIMIT = 5

class NamespaceLookup(Thread):
    
    def __init__(self, root, lookup_queue):
        Thread.__init__(self)
        self.daemon = True
        self.lookup_queue = lookup_queue
        self.root = root
        self.time_out = False
        
    def run(self):
        while True:
            if not self.lookup_queue.empty():
                device = self.lookup_queue.get()
                Thread(target=self.lookup, daemon=True, args=(device,)).start()
                
            else:
                time.sleep(0.1)

    def lookup(self, device):
        try:
            time.sleep(0.1)
            address = socket.gethostbyname(device['hostname'])
            self.root.device_data[device["index"]]['address'] = address
        except socket.gaierror:
            self.root.device_data[device["index"]]['active'] = False
            self.root.device_data[device["index"]]['status'] = "unreachable"
            
        self.root.job_list.update_job_status(device["index"])
        self.lookup_queue.task_done()

class RemoteConnection():

    def __init__(self, job):
        self.read_job_data(job)  # Read Job data first
        self.connect_to_device() # Connect to the device next
        if self.status == "running":
            self.run_script()        # The main commands are issued via this function
            self.logout()            # Once we're here, we can logout and close the session

    def read_job_data(self, job):
        self.return_data = {}
        self.hostname = job['hostname']
        self.username = job['username']
        self.password = job['password']
        self.device_type = job['device_type']
        self.folder = job['log_folder']
        self.additional_data = job['additional_data']
        self.script = job['script'].Script(self)

        self.status = "running"
        self.config = False

    def connect_to_device(self):
        current_time = datetime.datetime.now()
        self.device = {
            "device_type": self.device_type,
            "host": self.hostname,
            "username": self.username,
            "password": self.password,
            "secret": self.password,
            "session_log": f"{self.folder}{current_time.strftime('%Y-%m-%d-%H-%M-%S')}---{self.hostname}.log",
        }

        try:
            self.remote_connection = ConnectHandler(**self.device)
            self.remote_connection.enable()
            
        except NetmikoTimeoutException as error:
            print(error)
            self.status = "unreachable"
            #exit()
            
        except NetmikoAuthenticationException as error:
            print("auth error")
            self.status = "auth error"
            #exit()
            
        except: # Handle everything unexpected - I imagine this probably isn't PEP8 compliant... I just want the thread to close after something unexpected.
            print("Unexpected error:", sys.exc_info()[0])
            self.status = "program error"
            raise
                    
    def logout(self):
        self.remote_connection.disconnect()
        self.status = "complete"

    def send_command(self, command) -> str:
        # TODO - generic error handling of '^'
        
        if self.config:
            if command == 'end':
                self.config = False
            
            response = self.remote_connection.send_command(command, expect_string='.*#')#, read_timeout=10)

        else:
            if command in ['conf t', 'configure t', 'configure terminal']:
                self.config = True
                response = self.remote_connection.send_command(command, expect_string='.*#')#, read_timeout=10)
            else:

                response = self.remote_connection.send_command(command)#, read_timeout=10)



        return response

    def run_script(self):
        """
        The selected script is parsed here.
        
        
        """
        
        self.return_data = self.script.run()

        print(json.dumps(self.return_data, indent=4))

        self.logout()

class WorkerThread(Thread):
    def __init__(self, work_queue, complete_queue):
        """
        Worker threads handle spinning up the actual remote-connection
        class in order to initiate a SSH/Telnet session and run commands.
        These will recieve work from the work queue, which is a 'job'
        template. This will contain all the relevant information like the 
        below: 
            Username
            Password
            Hostname/IP address
            Job Index
            Device Type (If ASA/IOS or SSH/Telnet)
            Additional Data
            
        Additional Data can be used to pass additional data that may be needed
        for the script that we're running. For instance if we're making a custom
        object-group on an ASA, we could pass a number of IP addresses unique to
        each device.
        
        Args:
            work_queue (_type_): _description_
            complete_queue (_type_): _description_
        """

        Thread.__init__(self)
        self.daemon = True
        self.work_queue = work_queue
        self.complete_queue = complete_queue

    def run(self):
        """
        Has a while loop running to constantly find a job to do. Once a job
        is available, this will spin up the RemoteConnection Class to complete
        the script in question. Once this script has finished, the status of
        the class will no longer be 'running', and at this point the job is 
        complete and added back to the complete where the main process loop
        is waiting for the relevant data.
        """
        while True:
            if not self.work_queue.empty():
                job = self.work_queue.get()
                remote_connection = RemoteConnection(job)
                if remote_connection.status != 'running':
                    self.complete_queue.put({
                        "username" : remote_connection.username,
                        "hostname" : remote_connection.hostname,
                        "index" : job['index'],
                        "status" : remote_connection.status,
                        "return_data" : remote_connection.return_data
                        })
                    self.work_queue.task_done()
            time.sleep(0.1)

class ManagerThread(Thread):
    def __init__(self, manager_queue, complete_queue):
        """
        Manager thread handles sending out jobs to all the worker
        threads and spins up the relevant amount of threads to run
        job concurrently. 
        Args:
            manager_queue (_type_): _description_
            complete_queue (_type_): _description_
        """
        
        Thread.__init__(self)
        self.daemon = True
        self.manager_queue = manager_queue
        self.work_queue = Queue(maxsize=CONCURRENT_SSH_LIMIT)
        self.worker_threads = []
        for i in range(CONCURRENT_SSH_LIMIT):
            self.worker_threads.append(WorkerThread(self.work_queue, complete_queue).start())

    def run(self):
        while True:
            if not self.manager_queue.empty():
                if not self.work_queue.full():
                    self.work_queue.put(self.manager_queue.get())
            time.sleep(0.1)

class JobList(tk.Canvas):
    
    def __init__(self, parent, root):
        """
        This is a widget class for the list of jobs on the left. Was orginally
        going to use a TreeView for this, but it didn't give me the options I
        wanted so I made this one.
        The main program is accessible via root, so primarily for changing the
        focus/selection via this window.
        """
        super().__init__(parent, bg="#FFFFFF")
        self.root = root
        self.parent = parent
        self.scrollbar = tk.Scrollbar(parent, orient="vertical")
        self.scrollbar.pack(side="left", fill="y")
        self.config(yscrollcommand=self.scrollbar.set)
        self.scrollbar.config(command=self.yview)
        
        self.jobs = []
        self.selected_jobs = []
        self.focus_frame = ".!frame.!joblist.!frame.!frame"
        self.skip_select = True
                
        self.frame = tk.Frame(self)
        self.drop_down = tk.Menu(self.frame, tearoff=False)
        self.drop_down.add_command(label="Disable", command=self._toggle_enabled)
        self.drop_down.add_command(label="Reset")
        self.drop_down.add_command(label="Run", command= lambda: self.root.put_job_in_queue(self.selected_jobs))
        self.drop_down.add_command(label="Remove")
        self.drop_down.add_separator()
        self.drop_down.add_command(label="Edit")
        self.drop_down.add_command(label="Clear Selection")
        
        self.pack(side="right", fill="both", expand=True)
        self.create_window(0, 0, window=self.frame, anchor='nw', width=382)
        
        self.bind("<MouseWheel>", self._on_mousewheel)
        self.bind('<Enter>', self._bound_to_mousewheel)
        self.bind('<Leave>', self._unbound_to_mousewheel)

        self.selected_font = font.Font(family='Courier New', size=10,  weight="bold", slant="italic")
        self.standard_font = font.Font(family='Courier New', size=10,  weight="normal")
        
        self.load_images()
        
        parent.update()
        self.config(scrollregion=self.bbox("all"))

    ###
    ### MOUSE WHEEL BINDINGS
    ###

    def _bound_to_mousewheel(self, event):
        self.bind_all("<MouseWheel>", self._on_mousewheel)

    def _unbound_to_mousewheel(self, event):
        self.unbind_all("<MouseWheel>")

    def _on_mousewheel(self, event):
        if self.winfo_height() <= self.frame.winfo_height():
            self.yview_scroll(int(-1*(event.delta/120)), "units")


    ###
    ### GENERIC FUNCTIONS
    ###

    def _get_row_index(self, frame) -> int:
        """
        This receiveds a frame and essentially just runs a regex
        against its name, to get the index of the frame (line on
        the job list) that the frame reprisents, and then sends
        this in the return as an int.
        """
        if str(frame) == ".!frame.!joblist.!frame.!frame":
            return 0
        else:
            return int(re.search('(\d+)$', str(frame)).group())-1

    def update_job_status(self, row):
        self.jobs[row][1].configure(image=self.active_status_images[self.root.device_data[row]['status']])
        self.jobs[row][2].configure(text=self.root.device_data[row]['status'].capitalize())
        
        if self.root.device_data[row]['active']:
            self._set_row_enabled(row)
        else:
            self._set_row_disabled(row)

    ###
    ### ROW COLOUR/ATTRIBUTE FUNCTIONS
    ###
    
    def _set_row_colour(self, frame, colour):
        """
        Recieves a direct frame, or an index of a frame. And
        then goes through each child (cell) of the row.
        This sets all the frames backgrounds to the colour
        depending on if they're highlighted/focused.        
        """
        if isinstance(frame, int):
            frame = self.jobs[frame][3]
        for cell in frame.children:
            frame.children[cell].configure(bg=f"{colour}")

    def _set_row_border(self, frame, colour):
        """
        Sets the border of the row to a specific colour.
        Can handle the frame coming in as an int or the
        directly referenced object.
        """
        if isinstance(frame, int):
            frame = self.jobs[frame][3]
        frame.configure(highlightbackground = f"{colour}", highlightcolor= f"{colour}", highlightthickness=1)

    def _set_row_disabled(self, row):
        """
        Sets the row in question into 'disabled' mode.
        If a job is not active, it cannot be run at all.
        """
        self.jobs[row][0].configure(fg="#A1A1A1", bg="white")
        self.jobs[row][1].configure(image=self.disabled_status_images[self.root.device_data[row]['status']], bg="white")
        self.jobs[row][2].configure(fg="#A1A1A1", bg="white")
        if self.jobs[row][3] != self.focus_frame:
            self._set_row_border(self.jobs[row][3], "white")
        else:
            self._set_row_border(self.jobs[row][3], "black")

    def _set_row_enabled(self, row):
        """
        Sets the row in question into 'enabled' mode.
        If a job is not active, it cannot be run at all.
        """
        self.jobs[row][0].configure(fg="black", bg="white")
        self.jobs[row][1].configure(image=self.active_status_images[self.root.device_data[row]['status']], bg="white") 
        self.jobs[row][2].configure(fg="black", bg="white")
        if self.jobs[row][3] != self.focus_frame:
            self._set_row_border(self.jobs[row][3], "white")
        else:
            self._set_row_border(self.jobs[row][3], "black")

    def _focus_row(self, event):
        """
        Changes the currently focused job, changing the
        data displayed on the right of the screen.
        
        """
        frame = self.jobs[self.highlight][3]
    
        if not str(frame.master) == self.focus_frame:
            # Reset colour of old focus frame
            if self._get_row_index(self.focus_frame) in self.selected_jobs:
                self._set_row_border(self.focus_frame, 'lightskyblue')
            else:
                self._set_row_border(self.focus_frame, 'white')

            # Set colour of new foux
            self._set_row_border(frame, 'black')

            self.focus_frame = frame
            self.root.change_focus(self._get_row_index(self.focus_frame))

    def _shift_select_row(self, event):
        """
        To handle shift-selecting multiple lines.
        This goes and calculates all the relevant
        lines from the last clicked line up/down
        depending on the next selection.
        """

        # If there's no current selection, we have
        # to use this as a selection.
        if len(self.selected_jobs) < 1:
            self._select_row(event)

        else:
            if self.selected_jobs[-1] < self.highlight:
                lower = self.selected_jobs[-1]+1
                upper = self.highlight+1
            else:
                lower = self.highlight
                upper = self.selected_jobs[-1]
                
            # Once we've got the range, add them to
            # the selection
            for row in range(lower, upper):
                frame = self.jobs[row][3]

                self._set_row_colour(frame, "lightskyblue")
                if not frame == self.focus_frame:
                    self._set_row_border(frame, "lightskyblue")
                    
                if row not in self.selected_jobs:
                    self.selected_jobs.append(row)
    
    def _select_row(self, event):
        """
        Goes and adds the row to the current selection.
        We have to check if this is hitting the frame if
        user clicks right on the border - as this then
        goes ahead and selects twice. Below is a little hacky
        but sorts this out.
        """
        frame = event.widget.master
        if str(frame) == ".!frame.!joblist.!frame":
            self.skip_select = not self.skip_select
            
        if str(frame) != ".!frame.!joblist.!frame" or self.skip_select:
        
            frame = self.jobs[self.highlight][3]
            
            if self.highlight not in self.selected_jobs:
                self._set_row_colour(frame, "lightskyblue")
                if not frame == self.focus_frame:
                    self._set_row_border(frame, "lightskyblue")
                self.selected_jobs.append(self.highlight)
                
            else:
                self._set_row_colour(frame, "white")
                if not frame == self.focus_frame:
                    self._set_row_border(frame, "white")
                self.selected_jobs.remove(self.highlight)

    def _highlight_row(self, event):
        """
        Highlights row if user hovers over a frame.
        We have to bind all the mouse clicks to this
        as we also bind the mousewheel.
        """

        self.bind_all("<Button-1>", self._focus_row)
        self.bind_all("<Control-Button-1>", self._select_row)
        self.bind_all("<Shift-Button-1>", self._shift_select_row)
        self.bind_all("<Button-3>", self._job_menu)
        
        frame = event.widget
        self.highlight = self._get_row_index(frame)
        if not self._get_row_index(frame) in self.selected_jobs:
            self._set_row_colour(frame, "lightblue")
            if not frame == self.focus_frame:
                self._set_row_border(frame, "lightblue")
        else:
            self._set_row_colour(frame, "deepskyblue")
    
    def _unhighlight_row(self, event):
        """
        Unhighlights row if user hovers over a frame.
        We have to unbind all the mouse clicks to this
        as we also bind the mousewheel.
        """

        self.unbind_all("<Button-1>")
        self.unbind_all("<Control-Button-1>")
        self.unbind_all("<Shift-Button-1>")
        self.unbind_all("<Button-3>")
        frame = event.widget
        self.highlight = -1

        if not self._get_row_index(frame) in self.selected_jobs:
            self._set_row_colour(frame, "white")
            if not frame == self.focus_frame:
                self._set_row_border(frame, "white")
        else:
            self._set_row_colour(frame, "lightskyblue")
                
        if self.root.device_data[self._get_row_index(frame)]['status'] == "disabled":
            self._set_row_colour(frame, "#A1A1A1")
            self._set_row_border(frame, "#A1A1A1")
        
    def _job_menu(self, event):
        """
        This is the configuration for the right click menu.
        Some work needs to be done with this.
        
        """
        try:
            frame = event.widget.master
            clicked_off = False
            self.right_clicked_frame = self.highlight
            if str(frame) == ".!frame.!joblist.!frame":
                self.skip_select = not self.skip_select
                
            if str(frame) != ".!frame.!joblist.!frame" or self.skip_select:

                if len(self.selected_jobs) == 0:
                    
                    if self.highlight not in self.selected_jobs:
                        self._select_row(event)
                        clicked_off = True
                
                if not self.root.device_data[self.highlight]['active']:
                    if len(self.selected_jobs) > 0:
                        enable_disable_label = f"({len(self.selected_jobs)}) Enable"
                    else:
                        enable_disable_label = "Enable"
                else:
                    if len(self.selected_jobs) > 0:
                        enable_disable_label = f"({len(self.selected_jobs)}) Disable"
                    else:
                        enable_disable_label = "Disable"

                self.drop_down.entryconfigure(0, label=enable_disable_label)
                
                if len(self.selected_jobs) > 0:
                    self.drop_down.entryconfigure(1, label=f"({len(self.selected_jobs)}) Reset")
                    self.drop_down.entryconfigure(2, label=f"({len(self.selected_jobs)}) Run")
                    self.drop_down.entryconfigure(3, label=f"({len(self.selected_jobs)}) Remove")
                    
                
                self.drop_down.tk_popup(event.x_root, event.y_root)
            
        finally:
            #if not self._get_row_index(frame) in self.selected_jobs:
            #self._set_row_colour(self.right_clicked_frame, "white")
            #if not self.right_clicked_frame == self.focus_frame:
            #    self._set_row_border(frame, "white")
            
            self.drop_down.grab_release()
            print("MEMES")

    def _toggle_enabled(self):
        for job in self.selected_jobs:
            self.root.device_data[job]['active'] = not self.root.device_data[job]['active']
            if self.root.device_data[job]['active']:
                #self._remove_row_bold(job)
                self._set_row_enabled(job)
            else:
                self._set_row_disabled(job)
                

        self.selected_jobs = []

    def load_images(self):

        self.active_status_images = {
            "paused" : tk.PhotoImage(file="./res/active/pause.png"),
            "config error" : tk.PhotoImage(file="./res/active/warning.png"),
            "program error" : tk.PhotoImage(file="./res/active/error.png"),
            "running" : tk.PhotoImage(file="./res/active/play.png"),
            "unreachable" : tk.PhotoImage(file="./res/active/down.png"),
            "complete" : tk.PhotoImage(file="./res/active/ok.png"),
            "pending" : tk.PhotoImage(file="./res/active/pending.png"),
            "auth error" : tk.PhotoImage(file="./res/active/auth.png")
        }
        self.disabled_status_images = {
            "paused" : tk.PhotoImage(file="./res/disabled/pause.png"),
            "config error" : tk.PhotoImage(file="./res/disabled/warning.png"),
            "program error" : tk.PhotoImage(file="./res/disabled/error.png"),
            "running" : tk.PhotoImage(file="./res/disabled/play.png"),
            "unreachable" : tk.PhotoImage(file="./res/disabled/down.png"),
            "complete" : tk.PhotoImage(file="./res/disabled/ok.png"),
            "pending" : tk.PhotoImage(file="./res/disabled/pending.png"),
            "auth error" : tk.PhotoImage(file="./res/disabled/auth.png")
        }

    def load_data(self, data):
        self.create_headers()
        for n, line in enumerate(data, 1):
            
            line_frame = tk.Frame(self.frame, highlightbackground = "white", highlightcolor= "white", highlightthickness=1)#, relief="solid", bd=1)
            line_frame.grid(row=n, column=0, ipadx=3, columnspan=4, sticky="nesw")
            
            line_frame.bind("<Button-1>", self._focus_row)
            line_frame.bind("<Control-Button-1>", self._select_row)
            line_frame.bind("<Shift-Button-1>", self._shift_select_row)
            line_frame.bind("<Button-3>", self._job_menu)
            line_frame.bind("<Enter>", self._highlight_row)
            line_frame.bind("<Leave>", self._unhighlight_row)

            line_frame.grid_columnconfigure(4, weight=1)
            
            if len(line['hostname']) > 30:
                hostname = f"{line['hostname'][:30]}..."
            else:
                hostname = line['hostname'].ljust(33)
            
            hostname = tk.Label(line_frame, text=hostname, font=('Consolas', 10), borderwidth=1, relief="flat", bg="#FFFFFF")
            if not line['active']:
                hostname.configure(fg="#A1A1A1")
            hostname.grid(row=0, column=1, ipadx=3, sticky="nesw")
            
            if not line['active']:
                status_icon = tk.Label(line_frame, image=self.disabled_status_images[line['status']], borderwidth=1, relief="flat", bg="#FFFFFF")
            else:
                status_icon = tk.Label(line_frame, image=self.active_status_images[line['status']], borderwidth=1, relief="flat", bg="#FFFFFF")
                
            status_icon.grid(row=0, column=3, ipadx=3, sticky="nesw")
            
            status = tk.Label(line_frame, font=('Consolas', 10), text=line['status'].capitalize(), anchor="w", borderwidth=1, relief="flat", bg="#FFFFFF")
            if not line['active']:
                status.configure(fg="#A1A1A1")
            status.grid(row=0, column=4, ipadx=3, sticky="nesw")
            
            if str(line_frame) == self.focus_frame:
                self._set_row_border(line_frame, "black")
                self.focus_frame = line_frame
                         
            self.jobs.append((hostname, status_icon, status, line_frame))
    
        self.parent.update()
        self.config(scrollregion=self.bbox("all"))

    def create_headers(self):

        self.frame.grid_columnconfigure(1, weight=1)
        self.frame.grid_columnconfigure(2, weight=1)
        self.frame.grid_columnconfigure(3, weight=1)

        #self.check_all_button = ttk.Checkbutton(self.frame, command=self.check_all_rows)#, borderwidth=1, relief="raised")
        #self.check_all_button.grid(row=0, column=0, sticky="nesw")
        
        self.hostname_header = tk.Label(self.frame, text="Hostname")#, borderwidth=1, relief="ridge")
        self.hostname_header.grid(row=0, column=1, sticky="nesw")
        
        self.status_header = tk.Label(self.frame, text="Status")#, borderwidth=1, relief="ridge")
        self.status_header.grid(row=0, column=2, columnspan=2, sticky="nesw")
        
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

        self.session_log = tk.Text(self.session_log_tab, relief=tk.FLAT, highlightthickness=1, highlightbackground="darkgrey")
        self.session_log.place(relwidth=1, y=24, relheight=1, height=-25)
        self.session_log.configure(state='disabled')
        
    def selection_change(self):
        self.selection_info = self.root.device_data[self.root.selection_index]
        self.job_hostname.set(self.selection_info['hostname'])
        print(self.selection_info)
        self.populate_overview()

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
        
class Application(tk.Tk):

    def __init__(self):
        super().__init__()

        self.all_selected = False
        self.debug = True
        self.selection_index = 0
        
        self.title("Cisco Remote Access Program")
        self.iconbitmap("./res/ssh_icon.ico")
        self.geometry("900x500")

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
        self.editor = Editor(self.editor_window, title=f"{script.title} - Script Editor", text=script.base_script)
        self.editor.place(relheight=1, relwidth=1)

    def editor_edit_current_file(self):
        self.editor_window = tk.Toplevel(self)
        script = self.scripts[self.script_select.get()].Script(0)
        self.editor = Editor(self.editor_window, title=f"{script.title} - Script Editor", text=script.base_script)
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
                "device_type" : "cisco_ios",
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
            filename = "test_firewalls.csv"

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
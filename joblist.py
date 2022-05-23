import tkinter as tk
from tkinter import ttk
import tkinter.font as font
import re

class JobList(tk.Canvas):
    
    def __init__(self, parent, root):
        """
        This is a widget class for the list of jobs on the left. Was orginally
        going to use a TreeView for this, but it didn't give me the options I
        wanted so I made this one.
        The main program is accessible via root, so primarily for changing the
        focus/selection via this window.
        """
        super().__init__(parent)
        self.root = root
        
        self.parent = parent
        self.scrollbar = ttk.Scrollbar(parent, orient="vertical")
        self.scrollbar.pack(side="left", fill="y")
        self.config(yscrollcommand=self.scrollbar.set)
        self.scrollbar.config(command=self.yview)
        
        self.jobs = []
        self.selected_jobs = []
        self.focus_frame = ".!frame2.!joblist.!frame.!frame"
        self.skip_select = True
        
        self.focus_index = 0
        self.highlight_index = -1
                
        self.frame = tk.Frame(self)
        self.drop_down = tk.Menu(self.frame, tearoff=False)
        self.drop_down.add_command(label="Disable", command=self._toggle_enabled)
        self.drop_down.add_command(label="Reset")
        self.drop_down.add_command(label="Run", command=self._run_jobs)
        self.drop_down.add_command(label="Remove")
        self.drop_down.add_separator()
        self.drop_down.add_command(label="Edit")
        self.drop_down.add_command(label="Clear Selection")
        
        self.pack(side="right", fill="both", expand=True)
        self.create_window(0, 0, window=self.frame, anchor='nw', width=382)
        
        self.bind("<MouseWheel>", self._on_mousewheel)
        self.bind('<Enter>', self._bound_to_mousewheel)
        self.bind('<Leave>', self._unbound_to_mousewheel)
        
        self.load_images()
        
        self.colour_pallete = {
            "default" : {
                "fg" : "grey90",
                "bg" : "grey20",
                "bd" : "grey20"
            },
            "highlight" : {
                "fg" : "grey90",
                "bg" : "lightsteelblue4",
                "bd" : "lightsteelblue4"
            },
            "selection" : {
                "fg" : "grey90",
                "bg" : "lightblue4",
                "bd" : "lightblue4"
            },
            "selection_highlight" : {
                "fg" : "grey90",
                "bg" : "slategray4",
                "bd" : "slategray4"
            },
            "focus" : {
                "fg" : "grey90",
                "bg" : "grey20",
                "bd" : "grey90"
            },
            "focus_highlight" : {
                "fg" : "grey90",
                "bg" : "lightsteelblue4",
                "bd" : "grey90"
            },
            "focus_selection" : {
                "fg" : "grey90",
                "bg" : "lightblue4",
                "bd" : "grey90"
            },
            "focus_highlight_selection" : {
                "fg" : "grey90",
                "bg" : "slategray4",
                "bd" : "grey90"
            },
            "disabled" : {
                "fg" : "grey50",
                "bg" : "grey20",
                "bd" : "grey20"
            },
            "disabled_focus" : {
                "fg" : "grey50",
                "bg" : "grey20",
                "bd" : "grey20"
            },
            "disabled_highlight" : {
                "fg" : "grey50",
                "bg" : "grey20",
                "bd" : "grey20"
            },
        }

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
        if str(frame) == ".!frame2.!joblist.!frame.!frame":
            return 0
        else:
            search = re.search('(\d+)$', str(frame)).group()
            return int(search)-1

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
    
    def _set_row_colour_(self, frame):
        if isinstance(frame, int):
            frame = self.jobs[frame][3]
            
        #print(f"Input: {self._get_row_index(frame)} | Focus: {self.focus_index} | Highlight {self.highlight_index} | Selection: {self.selected_jobs}")
        
        # Default (If none of the below apply)
        colour = self.colour_pallete['default']
        
        # Highlighted 
        if self.highlight_index != -1 and \
            frame == self.jobs[self.highlight_index][3]:
            colour = self.colour_pallete['highlight']

        # Selected
        if self._get_row_index(frame) in self.selected_jobs:
            colour = self.colour_pallete['selection']

        # Selected & Highlighted
        if self._get_row_index(frame) in self.selected_jobs and \
            self.highlight_index != -1 and frame == self.jobs[self.highlight_index][3]:
            colour = self.colour_pallete['selection_highlight']

        # Focused
        if self._get_row_index(frame) == self.focus_index:
            colour = self.colour_pallete['focus']
            
        # Focused & Highlighted
        if self._get_row_index(frame) == self.focus_index and \
            self._get_row_index(frame) == self.highlight_index:
            colour = self.colour_pallete['focus_highlight']
            
        # Focused & Selected
        if self._get_row_index(frame) == self.focus_index and \
            self._get_row_index(frame) in self.selected_jobs:
            colour = self.colour_pallete['focus_selection']
            
        # Focused & Selected & Highlighted
        if self._get_row_index(frame) == self.focus_index and \
            self._get_row_index(frame) in self.selected_jobs and \
            self.highlight_index != -1 and frame == self.jobs[self.highlight_index][3]:
            colour = self.colour_pallete['focus_highlight_selection']
            
        # Disabled
        if not self.root.device_data[self._get_row_index(frame)]['active']:
            colour = self.colour_pallete['disabled']
            
        # Disabled & Focused
        if not self.root.device_data[self._get_row_index(frame)]['active'] and \
            self._get_row_index(frame) == self.focus_index:
            colour = self.colour_pallete['disabled_focus']
            
        # Disabled & Highlighted
        if not self.root.device_data[self._get_row_index(frame)]['active'] and \
            self._get_row_index(frame) == self.highlight_index:
            colour = self.colour_pallete['disabled_highlight']
            
            
        for cell in frame.children:
            frame.children[cell].configure(bg=colour['bg'])
            frame.children[cell].configure(fg=colour['fg'])
            
        frame.configure(highlightbackground=colour['bd'], highlightcolor=colour['bd'], highlightthickness=1)
    
    def _set_row_disabled(self, row):
        """
        Sets the row in question into 'disabled' mode.
        If a job is not active, it cannot be run at all.
        """
        frame = self.jobs[row]
        frame[1].configure(image=self.disabled_status_images[self.root.device_data[row]['status']])
        self._set_row_colour_(frame[3])

    def _set_row_enabled(self, row):
        """
        Sets the row in question into 'enabled' mode.
        If a job is not active, it cannot be run at all.
        """
        frame = self.jobs[row]
        frame[1].configure(image=self.active_status_images[self.root.device_data[row]['status']])
        self._set_row_colour_(frame[3])

    ###
    ### ROW SELECTION FUNCTIONS
    ###

    def _focus_row(self, event):
        """
        Changes the currently focused job, changing the
        data displayed on the right of the screen.
        
        """
        old_frame = self.focus_frame
        frame = self.jobs[self.highlight_index][3]
        if not str(frame) == self.focus_frame:
            self.focus_frame = frame
            self.focus_index = self._get_row_index(frame)
            self.root.change_focus(self.focus_index)
            self._set_row_colour_(old_frame)
            self._set_row_colour_(self.focus_frame)

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
            if self.selected_jobs[-1] < self.highlight_index:
                lower = self.selected_jobs[-1]+1
                upper = self.highlight_index+1
            else:
                lower = self.highlight_index
                upper = self.selected_jobs[-1]
                
            # Once we've got the range, add them to
            # the selection
            for row in range(lower, upper):
                frame = self.jobs[row][3]

                if row not in self.selected_jobs:
                    self.selected_jobs.append(row)
                
                self._set_row_colour_(frame)
    
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
        
            frame = self.jobs[self.highlight_index][3]
            
            if self.highlight_index not in self.selected_jobs:
                self.selected_jobs.append(self.highlight_index)
                
            else:
                self.selected_jobs.remove(self.highlight_index)
            
            self._set_row_colour_(frame)

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
        self.highlight_index = self._get_row_index(frame)
        self._set_row_colour_(frame)
    
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
        self.highlight_index = -1
        
        self._set_row_colour_(frame)
                
        if self.root.device_data[self._get_row_index(frame)]['status'] == "disabled":
            self._set_row_colour(frame, "#A1A1A1")
            self._set_row_border(frame, "#A1A1A1")
     
    ###
    ### RIGHT CLICK MENU FUNCTIONS
    ###
    def _clear_job_selection(self):
        ran_jobs = self.selected_jobs
        self.selected_jobs = []
        for job in ran_jobs:
            self._set_row_colour_(job)
        
    def _run_jobs(self):
        print(self.selected_jobs)
        self.root.put_job_in_queue(self.selected_jobs)
        self._clear_job_selection()
        
    def _job_menu(self, event):
        """
        This is the configuration for the right click menu.
        Some work needs to be done with this.
        
        """
        
        empty_selection = True if len(self.selected_jobs) == 0 else False
        try:
            frame = event.widget.master
            self.right_clicked_frame = self.highlight_index
            if str(frame) == ".!frame.!joblist.!frame":
                self.skip_select = not self.skip_select
                
            if str(frame) != ".!frame.!joblist.!frame" or self.skip_select:

                if empty_selection:
                    if self.highlight_index not in self.selected_jobs:
                        self._select_row(event)
                
                if not self.root.device_data[self.highlight_index]['active']:
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
            
            self.drop_down.grab_release()
            if empty_selection:
                print(self.selected_jobs)
                self._clear_job_selection()

    def _toggle_enabled(self):
        for job in self.selected_jobs:
            self.root.device_data[job]['active'] = not self.root.device_data[job]['active']
            if self.root.device_data[job]['active']:
                self._set_row_enabled(job)
            else:
                self._set_row_disabled(job)
                
        self.selected_jobs = []

    ###
    ### DATA LOAD FUNCTIONS
    ###

    def load_images(self):

        self.active_status_images = {
            "paused" : tk.PhotoImage(file="./res/active/pause.png"),
            "config error" : tk.PhotoImage(file="./res/active/warning.png"),
            "program error" : tk.PhotoImage(file="./res/active/error.png"),
            "running" : tk.PhotoImage(file="./res/active/play.png"),
            "unreachable" : tk.PhotoImage(file="./res/active/down.png"),
            "complete" : tk.PhotoImage(file="./res/active/ok.png"),
            "pending" : tk.PhotoImage(file="./res/active/pending.png"),
            "auth error" : tk.PhotoImage(file="./res/active/auth.png"),
            "connecting" : tk.PhotoImage(file="./res/active/connect.png"),
            "connected" : tk.PhotoImage(file="./res/active/connected.png"),
            "queued" : tk.PhotoImage(file="./res/active/queued.png")
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
            
            line_frame = tk.Frame(self.frame)#, highlightbackground = self.background_colour, highlightcolor= self.background_colour, highlightthickness=1)#, relief="solid", bd=1)
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
            
            hostname = tk.Label(line_frame, text=hostname, font=('Consolas', 10))#, borderwidth=1, relief="flat", bg=self.background_colour)
            if not line['active']:
                hostname.configure(fg="#A1A1A1")
            hostname.grid(row=0, column=1, ipadx=3, sticky="nesw")
            
            if not line['active']:
                status_icon = tk.Label(line_frame, image=self.disabled_status_images[line['status']])#, borderwidth=1, relief="flat", bg=self.background_colour)
            else:
                status_icon = tk.Label(line_frame, image=self.active_status_images[line['status']])#, borderwidth=1, relief="flat", bg=self.background_colour)
                
            status_icon.grid(row=0, column=3, ipadx=3, sticky="nesw")
            
            status = tk.Label(line_frame, font=('Consolas', 10), text=line['status'].capitalize(), anchor="w")#, borderwidth=1, relief="flat", bg=self.background_colour)
            if not line['active']:
                status.configure(fg="#A1A1A1")
            status.grid(row=0, column=4, ipadx=3, sticky="nesw")
            
            if str(line_frame) == self.focus_frame:
                #self._set_row_border(line_frame)#, self.focus_border_colour)
                self.focus_frame = line_frame
                         
            self.jobs.append((hostname, status_icon, status, line_frame))
            self._set_row_colour_(line_frame)
    
        self.parent.update()
        self.config(scrollregion=self.bbox("all"))

    def create_headers(self):

        self.frame.grid_columnconfigure(1, weight=1)
        self.frame.grid_columnconfigure(2, weight=1)
        self.frame.grid_columnconfigure(3, weight=1)

        self.hostname_header = tk.Label(self.frame, text="Hostname", background="grey15")#, borderwidth=1, relief="ridge")
        self.hostname_header.grid(row=0, column=1, sticky="nesw")
        
        self.status_header = tk.Label(self.frame, text="Status", background="grey15")#, borderwidth=1, relief="ridge")
        self.status_header.grid(row=0, column=2, columnspan=2, sticky="nesw")
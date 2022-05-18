import tkinter as tk
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

import tkinter as tk
from tkinter import ttk
import tkinter.font as font
import re
from turtle import width

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
        
        self.jobs = []
        self.selected_jobs = []
        self.focus_frame = ""
        self.skip_select = True
        
        self.focus_index = 0
        self.highlight_index = -1
        
        self.frame = tk.Frame(self)
        self.create_drop_down()


        self.header_frame = tk.Frame(self)
        self.header_frame.place(x=0, y=0, relheight=1, relwidth=1)
        
        self.list_canvas = tk.Canvas(self)
        self.list_canvas.place(x=0, y=37, relheight=1, relwidth=1)
        self.list_frame = tk.Frame(self.list_canvas)
        self.list_frame.place(relheight=1, relwidth=1)

        self.pack(side="right", fill="both", expand=True)
        self.create_window(0, 0, window=self.list_frame, anchor='nw', width=382)
        
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
                "bg" : "grey10",
                "bd" : "grey20"
            },
            "disabled_focus" : {
                "fg" : "grey50",
                "bg" : "grey10",
                "bd" : "grey90"
            },
            "disabled_highlight" : {
                "fg" : "grey50",
                "bg" : "grey15",
                "bd" : "grey20"
            },
            "disabled_highlight_focus" : {
                "fg" : "grey50",
                "bg" : "grey20",
                "bd" : "grey90"
            },
        }
        self.create_headers()

        self.scrollbar = ttk.Scrollbar(parent, orient="vertical")
        self.scrollbar.pack(side="left", fill="y")
        
        self.list_canvas.config(yscrollcommand=self.scrollbar.set)
        self.scrollbar.config(command=self.list_canvas.yview)

        parent.update()
        self.config(scrollregion=self.list_canvas.bbox("all"))

    ###
    ### MOUSE WHEEL BINDINGS
    ###

    def _bound_to_mousewheel(self, event):
        self.bind_all("<MouseWheel>", self._on_mousewheel)

    def _unbound_to_mousewheel(self, event):
        self.unbind_all("<MouseWheel>")

    def _on_mousewheel(self, event):
        if self.winfo_height() <= self.frame.winfo_height():
            self.list_canvas.yview_scroll(int(-1*(event.delta/120)), "units")

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
        search = re.search('(\d+)$', str(frame)).group()
        return int(search)

    def _set_command(self, command):
        pass

    def update_job_icon(self, row, severity):
        self.jobs[row][1].configure(image=self.active_status_images[self.root.device_data[row]['status']])

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
    
    def _set_row_colour_(self, frame_index):
        """if isinstance(frame, int):
            frame = self.jobs[frame][3]"""
            
        #print(f"Input: {self._get_row_index(frame)} | Focus: {self.focus_index} | Highlight {self.highlight_index} | Selection: {self.selected_jobs}")
        
        # Default (If none of the below apply)
        if  self.root.device_data[frame_index]['active']:
            colour = self.colour_pallete['default']
        else:
            colour = self.colour_pallete['disabled']


        #print(frame_index, self.highlight_index)

        if self.highlight_index != None:

            # Highlighted 
            if frame_index == self.highlight_index:
                colour = self.colour_pallete['highlight']
                #print("Highlight")

            # Selected & Highlighted
            if frame_index in self.selected_jobs and \
                self.highlight_index != -1 and \
                frame_index == self.highlight_index:

                colour = self.colour_pallete['selection_highlight']
                #print("Selected & Highlighted")

            # Focused & Highlighted
            if frame_index == self.focus_index and \
                frame_index == self.highlight_index:

                colour = self.colour_pallete['focus_highlight']
                #print("Focused & Highlighted")
            
            # Focused & Selected & Highlighted
            if frame_index == self.focus_index and \
                frame_index in self.selected_jobs and \
                self.highlight_index != -1 and \
                frame_index == frame_index:

                colour = self.colour_pallete['focus_highlight_selection']
                #print("Focused & Selected & Highlighted")
            
            
            # Disabled & Highlighted
            if not self.root.device_data[frame_index]['active'] and \
                frame_index == self.highlight_index:

                colour = self.colour_pallete['disabled_highlight']
                #print("Disabled & Highlighted")
                
            # Disabled & Highlighted & Focused
            if not self.root.device_data[frame_index]['active'] and \
                frame_index == self.highlight_index and \
                frame_index == self.focus_index:

                colour = self.colour_pallete['disabled_highlight_focus']
                #print("Disabled & Highlighted & Focused")
                
        else:    
                
            # Selected
            if frame_index in self.selected_jobs:

                colour = self.colour_pallete['selection']
                #print("Selected")

            # Focused
            if frame_index == self.focus_index:

                colour = self.colour_pallete['focus']
                #print("Focused")

                
            # Focused & Selected
            if frame_index == self.focus_index and \
                frame_index in self.selected_jobs:

                colour = self.colour_pallete['focus_selection']
                #print("Focused & Selected")

            # Disabled
            if not self.root.device_data[frame_index]['active']:

                colour = self.colour_pallete['disabled']
                #print("Disabled")
                
            # Disabled & Focused
            if not self.root.device_data[frame_index]['active'] and \
                frame_index == self.focus_index:

                colour = self.colour_pallete['disabled_focus']
                #print("Disabled & Focused")


        for cell in self.jobs[frame_index][3].winfo_children():
            cell.configure(bg=colour['bg'])
            cell.configure(fg=colour['fg'])
            
        self.jobs[frame_index][3].configure(highlightbackground=colour['bd'], highlightcolor=colour['bd'], highlightthickness=1)
    
    def _set_row_disabled(self, row):
        """
        Sets the row in question into 'disabled' mode.
        If a job is not active, it cannot be run at all.
        """
        frame = self.jobs[row]
        frame[1].configure(image=self.disabled_status_images[self.root.device_data[row]['status']])
        self._set_row_colour_(row)

    def _set_row_enabled(self, row):
        """
        Sets the row in question into 'enabled' mode.
        If a job is not active, it cannot be run at all.
        """
        frame = self.jobs[row]
        frame[1].configure(image=self.active_status_images[self.root.device_data[row]['status']])
        self._set_row_colour_(row)

    ###
    ### ROW SELECTION FUNCTIONS
    ###

    def _focus_row(self, event):
        """
        Changes the currently focused job, changing the
        data displayed on the right of the screen.
        
        """
        old_frame_index = self.focus_index
        frame = self.jobs[self.highlight_index][3]
        if not str(frame) == self.focus_frame:
            self.focus_frame = frame

            self.focus_index = self.highlight_index
            self.root.change_focus(self.focus_index)

            self._set_row_colour_(old_frame_index)
            self._set_row_colour_(self.focus_index)

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
                
                self._set_row_colour_(row)
            self.empty_selection = False
    
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
            
            self._set_row_colour_(self.highlight_index)
        self.empty_selection = False

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

        self.highlight_index = self._get_row_index(event.widget)
        self._set_row_colour_(self.highlight_index)
    
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
        
        
        old_highlight = self.highlight_index
        self.highlight_index = None
        self._set_row_colour_(old_highlight)

    ###
    ### RIGHT CLICK MENU FUNCTIONS
    ###

    def _clear_job_selection(self):
        ran_jobs = self.selected_jobs
        self.selected_jobs = []
        for job in ran_jobs:
            self._set_row_colour_(job)
        
    def _job_menu(self, event):
        """
        This is the configuration for the right click menu.
        Some work needs to be done with this.
        
        """

        #print(f"RIGHT - {self.empty_selection} - {self.selected_jobs} ")
        
        self.empty_selection = True if len(self.selected_jobs) == 0 else False
        try:
            frame = event.widget.master
            if str(frame) == ".!frame2.!joblist.!frame":
                self.skip_select = not self.skip_select
                
            if str(frame) != ".!frame2.!joblist.!frame" or self.skip_select:

                if self.empty_selection:
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

                self.drop_down.entryconfigure(4, label=enable_disable_label)
                self.drop_down.tk_popup(event.x_root, event.y_root)
            
        finally:

            self.drop_down.grab_release()

        
    def _run_jobs(self):
        print("RUNNING: ",self.selected_jobs)
        self.root.put_job_in_queue(self.selected_jobs)
        self._clear_job_selection()

    def _toggle_enabled(self):
        for job in self.selected_jobs:
            self.root.device_data[job]['active'] = not self.root.device_data[job]['active']
            if self.root.device_data[job]['active']:
                self._set_row_enabled(job)
            else:
                self._set_row_disabled(job)
                
        self.selected_jobs = []

    def _reset_jobs(self):
        pass

    def _remove_jobs(self):
        pass

    ###
    ### DATA LOAD FUNCTIONS
    ###

    def create_drop_down(self):
        self.drop_down = tk.Menu(self.frame, tearoff=False)
        self.drop_down.add_command(label="Run", command=self._run_jobs)#self._set_command("run_jobs"))
        self.drop_down.add_command(label="Reset", command=self._reset_jobs)
        self.drop_down.add_command(label="Remove", command=self._remove_jobs)
        self.drop_down.add_separator()
        self.drop_down.add_command(label="Disable", command=self._toggle_enabled)
        self.drop_down.add_command(label="Mark Complete", command=self._set_command("clear"))
        self.drop_down.add_command(label="Clear Selection", command=self._set_command("clear"))

    def clear_frame(self):
        self.list_frame.pack_forget()
        for widget in self.list_frame.winfo_children():
            widget.destroy()
        self.create_drop_down()
        self.parent.update()
        self.config(scrollregion=self.list_frame.bbox("all"))

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

    def load_device_gui(self, index, line, position):
        line_frame = tk.Frame(self.list_frame, name=f"!frame{index}")
        print(index)
        line_frame.place(x=0, y=position*25, height=25, width=386)
        
        line_frame.bind("<Button-1>", self._focus_row)
        line_frame.bind("<Control-Button-1>", self._select_row)
        line_frame.bind("<Shift-Button-1>", self._shift_select_row)
        line_frame.bind("<Button-3>", self._job_menu)
        line_frame.bind("<Enter>", self._highlight_row)
        line_frame.bind("<Leave>", self._unhighlight_row)

        #line_frame.grid_columnconfigure(4, weight=1)
        
        # HOSTNAME
        if len(line['hostname']) > 30:
            hostname = f"{line['hostname'][:30]}..."
        else:
            hostname = line['hostname'].ljust(33)
        hostname = line['hostname'].ljust(20)
        
        hostname = tk.Label(line_frame, text=hostname, font=('Consolas', 10), anchor="w")
        if not line['active']:
            hostname.configure(fg="#A1A1A1")
        hostname.place(x=0, y=0, relheight=1, width=200)
        
        # STATUS IMAGES
        if not line['active']:
            status_icon = tk.Label(line_frame, image=self.disabled_status_images[line['status']])
        else:
            status_icon = tk.Label(line_frame, image=self.active_status_images[line['status']])
        status_icon.place(x=200, y=0, relheight=1, width=50)

        # STATUS 
        status = tk.Label(line_frame, font=('Consolas', 10), text=line['status'].capitalize())
        if not line['active']:
            status.configure(fg="#A1A1A1")
        status.place(x=250, y=0, relheight=1, width=134)
        
        if str(line_frame) == self.focus_frame:
            self.focus_frame = line_frame
                        
        self.jobs.append((hostname, status_icon, status, line_frame))
        self._set_row_colour_(index)

    def load_data(self, data, in_filter="Status"):
        self.clear_frame()
        
        if in_filter == "Status":
            for n, line in enumerate(data, 0):
                self.load_device_gui(n, line, n)
                
        else:
            display_count = 0
            for n, line in enumerate(data, 0):
                if line['status'].capitalize() == in_filter:
                    self.load_device_gui(n, line, display_count)
                    display_count += 1
                    
        print(self.list_frame.winfo_height())
        self.parent.update()
        self.config(scrollregion=self.list_frame.bbox("all"))

    def get_statuses(self, event):
        statuses = ["Status"]
        for device in self.root.device_data:
            if device['status'].capitalize() not in statuses:
                statuses.append(device['status'].capitalize())
        self.status_header.configure(values=statuses)

    def status_filter(self, event):
        self.status_header.selection_clear()
        self.clear_frame()
        self.load_data(self.root.device_data, self.status_header.get())

    def create_headers(self):

        self.hostname_header = ttk.Button(self.header_frame, text="Hostname")
        self.hostname_header.place(x=0, y=0, width=191)
        self.status_header = ttk.Combobox(self.header_frame, state="readonly", values=["Status"] )
        self.status_header.current(0)
        self.status_header.bind('<<ComboboxSelected>>', self.status_filter)
        self.status_header.bind('<1>', self.get_statuses)
        self.status_header.place(x=193, y=0, width=191)


class JobList_(tk.Frame):
    
    def __init__(self, parent):
        super().__init__(parent)
        
        self.scrollbar = tk.Scrollbar(self)
        self.list_canvas = tk.Canvas(self, yscrollcommand=self.scrollbar.set)
        self.scrollbar.place(relheight=1)
        
        self.list_frame = tk.Frame(self.list_canvas)
        self.list_canvas.place(relheight=1, width=380)
        
        self.list_canvas.create_window(0, 0, window=self.list_frame, anchor='nw')
        
        for i in range(100):
            tk.Label(self.list_frame,wraplength=350 ,text=r"Det er en kendsgerning, at man bliver distraheret af læsbart indhold på en side, når man betragter dens websider, som stadig er på udviklingsstadiet. Der har været et utal af websider, som stadig er på udviklingsstadiet. Der har været et utal af variationer, som er opstået enten på grund af fejl og andre gange med vilje (som blandt andet et resultat af humor).").pack()
            tk.Button(self.list_frame,text="anytext").pack()        
        
        self.update()
        self.list_canvas.config(scrollregion=self.list_canvas.bbox("all"))
    """
    root=tk.Tk()

    vscrollbar = tk.Scrollbar(root)

    c= tk.Canvas(root,background = "#D2D2D2",yscrollcommand=vscrollbar.set)

    vscrollbar.config(command=c.yview)
    vscrollbar.pack(side=tk.LEFT, fill=tk.Y) 

    f=tk.Frame(c) #Create the frame which will hold the widgets

    c.pack(side="left", fill="both", expand=True)

    #Updated the window creation
    c.create_window(0,0,window=f, anchor='nw')

    #Added more content here to activate the scroll
    for i in range(100):
        tk.Label(f,wraplength=350 ,text=r"Det er en kendsgerning, at man bliver distraheret af læsbart indhold på en side, når man betragter dens websider, som stadig er på udviklingsstadiet. Der har været et utal af websider, som stadig er på udviklingsstadiet. Der har været et utal af variationer, som er opstået enten på grund af fejl og andre gange med vilje (som blandt andet et resultat af humor).").pack()
        tk.Button(f,text="anytext").pack()

    #Removed the frame packing
    #f.pack()

    #Updated the screen before calculating the scrollregion
    root.update()
    c.config(scrollregion=c.bbox("all"))

    root.mainloop()"""

if __name__ == "__main__":
    root = tk.Tk()
    jlist = JobList_(root)
    jlist.place(x=0, y=0, width=100)
    root.mainloop()
import tkinter as tk
import tkinter.filedialog as fd
import csv, json
from pathlib import Path
from tkinter import ttk

test_data = [
    {
        'active' : True,
        'hostname' : 'man4-sw990.ukfast.net',
        'status' : 'complete',
    },
    {
        'active' : True,
        'hostname' : 'man4-sw991.ukfast.net',
        'status' : 'complete'
    },
    {
        'active' : True,
        'hostname' : 'man4-sw992.ukfast.net',
        'status' : 'config error'
    },
    {
        'active' : True,
        'hostname' : 'man4-sw993.ukfast.net',
        'status' : 'program error'
    },
    {
        'active' : True,
        'hostname' : 'man4-sw994.ukfast.net',
        'status' : 'running'
    },
    {
        'active' : True,
        'hostname' : 'man4-sw995.ukfast.net',
        'status' : 'running'
    },
    {
        'active' : True,
        'hostname' : 'man4-sw996.ukfast.net',
        'status' : 'running'
    },
    {
        'active' : False,
        'hostname' : 'man4-sw997.ukfast.net',
        'status' : 'running'
    },
    {
        'active' : False,
        'hostname' : 'man4-sw998.ukfast.net',
        'status' : 'running'
    },
    {
        'active' : False,
        'hostname' : 'man4-sw999.ukfast.net',
        'status' : 'pending'
    },
    {
        'active' : False,
        'hostname' : 'man4-sw990.ukfast.net',
        'status' : 'pending'
    },
    {
        'active' : True,
        'hostname' : 'man4-sw991.ukfast.net',
        'status' : 'pending'
    },
    {
        'active' : True,
        'hostname' : 'man4-sw992.ukfast.net',
        'status' : 'unreachable'
    },
    {
        'active' : True,
        'hostname' : 'man4-sw993.ukfast.net',
        'status' : 'pending'
    },
    {
        'active' : True,
        'hostname' : 'man4-sw994.ukfast.net',
        'status' : 'pending'
    },
    {
        'active' : True,
        'hostname' : 'man4-sw995.ukfast.net',
        'status' : 'pending'
    },
    {
        'active' : True,
        'hostname' : 'man4-sw996.ukfast.net',
        'status' : 'pending'
    },
    {
        'active' : True,
        'hostname' : 'man4-sw997.ukfast.net',
        'status' : 'pending'
    },
    {
        'active' : True,
        'hostname' : 'man4-sw998.ukfast.net',
        'status' : 'pending'
    },
    {
        'active' : False,
        'hostname' : 'man4-sw999.ukfast.net',
        'status' : 'pending'
    },
    {
        'active' : True,
        'hostname' : 'man4-sw990.ukfast.net',
        'status' : 'pending'
    },
    {
        'active' : True,
        'hostname' : 'man4-sw991.ukfast.net',
        'status' : 'pending'
    },
    {
        'active' : True,
        'hostname' : 'man4-sw992.ukfast.net',
        'status' : 'pending'
    },
    {
        'active' : True,
        'hostname' : 'man4-sw993.ukfast.net',
        'status' : 'pending'
    },
    {
        'active' : True,
        'hostname' : 'man4-sw994.ukfast.net',
        'status' : 'pending'
    },
    {
        'active' : True,
        'hostname' : 'man4-sw995.ukfast.net',
        'status' : 'pending'
    },
    {
        'active' : True,
        'hostname' : 'man4-sw996.ukfast.net',
        'status' : 'pending'
    },
    {
        'active' : True,
        'hostname' : 'man4-sw997.ukfast.net',
        'status' : 'pending'
    },
    {
        'active' : True,
        'hostname' : 'man4-sw998.ukfast.net',
        'status' : 'pending'
    },
    {
        'active' : False,
        'hostname' : 'man4-sw999.ukfast.net',
        'status' : 'pending'
    }
]

class Application(tk.Tk):

    def _fixed_map(self, option):
        # Fix for setting text colour for Tkinter 8.6.9
        # From: https://core.tcl.tk/tk/info/509cafafae
        #
        # Returns the style map for 'option' with any styles starting with
        # ('!disabled', '!selected', ...) filtered out.

        # style.map() returns an empty list for missing options, so this
        # should be future-safe.
        return [elm for elm in self.style.map('Treeview', query_opt=option) if
            elm[:2] != ('!disabled', '!selected')]

    def highlight_row(self, event):
        tree = event.widget
        item = tree.identify_row(event.y)
        tree.tk.call(tree, "tag", "remove", "highlight")
        tree.tk.call(tree, "tag", "add", "highlight", item)

    def on_double_click(self, event):
        tree = event.widget
        item = tree.identify_row(event.y)
        if event.x > 18:
            selection_index = self.job_list_treeview.item(item)['tags'][0]
            test_data[selection_index]['selected'] = not test_data[selection_index]['selected']
        self.refresh_treeview_data()
            
    def on_click(self, event):
        tree = event.widget
        item = tree.identify_row(event.y)
    
        #self.all_selected = self.check_all_selected()

        if event.x <= 18:
        
            if event.y <= 23:
                if not self.all_selected:
                    for n, entry in enumerate(test_data):
                        test_data[n]['selected'] = True
                else:
                    for n, entry in enumerate(test_data):
                        test_data[n]['selected'] = False
        
            else:
                selection_index = tree.item(item)['tags'][0]
                test_data[selection_index]['selected'] = not test_data[selection_index]['selected']
                
        else:
            self.selection_index = tree.item(item)['tags'][0]
            self.job_hostname.set(test_data[self.selection_index]['hostname'])
            self.read_session_log()
            
        self.refresh_treeview_data()

    def read_session_log(self):
        text = ""
        with open(f"./{test_data[self.selection_index]['hostname']}.log", 'r') as session_file:
            text = session_file.read()
        self.session_log.configure(state='normal')
        self.session_log.delete(1.0, "end")
        self.session_log.insert(1.0, text)
        self.session_log.configure(state='disabled')
        
    def check_all_selected(self):
        total = sum([ 1 for entry in test_data if entry['selected'] == True])
        if total == len(test_data):
            self.job_list_treeview.heading('selected', text='☒')
            self.all_selected = True
        else:
            self.job_list_treeview.heading('selected', text='☐')
            self.all_selected =  False

    def refresh_treeview_data(self):
        self.job_list_treeview.delete(*self.job_list_treeview.get_children())

        for n, entry in enumerate(test_data):
            data = ('☒' if entry['selected'] else '☐', entry['hostname'], entry['status'])
            if n % 2 == 0:
                checker = "odd"
            else:
                checker = "even"
                
            if entry['status'] == 'idle':
                self._img = tk.PhotoImage(file="./res/pause-16.png") 
            elif entry['status'] == 'config error':
                self._img = tk.PhotoImage(file="./res/warning-orange-16.png") 
            elif entry['status'] == 'program error':
                self._img = tk.PhotoImage(file="./res/warning-red-16.png") 
            elif entry['status'] == 'unreachable':
                self._img = tk.PhotoImage(file="./res/warning-red-16.png") 
            elif entry['status'] == 'complete':
                self._img = tk.PhotoImage(file="./res/warning-red-16.png") 
            elif entry['status'] == 'running':
                self._img = tk.PhotoImage(file="./res/warning-red-16.png") 
                
            self.job_list_treeview.insert('', tk.END, text="", image=self._img, values=data, tags=(n, checker))

        self.check_all_selected()

    def __init__(self):
        super().__init__()
        
        self.all_selected = False
        self.selection_index = 0
        
        self.title("Cisco Remote Access Program")
        #self.iconbitmap("")
        self.main_frame = tk.Frame(self)
        #self.main_frame.pack(fill="both", expand="true")
        self.geometry("900x500")

        self.style=ttk.Style()
        self.style.configure("Treeview", background="white")

        ###
        ### Menu Bar config
        ###

        self.toolbar = tk.Menu(self)
        self.config(menu = self.toolbar)

        self.file_menu = tk.Menu(self.toolbar, tearoff="off")
        self.toolbar.add_cascade(label="File", menu=self.file_menu)
        self.file_menu.add_command(label="Import CSV", command=self.import_csv)
        self.file_menu.add_command(label="Open Job", command=self.import_csv)

        ###
        ### Main window grid config
        ###
        
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=2)
        self.grid_columnconfigure(2, weight=1)

        ###
        ### Tree/Job View (Left side) config
        ###

        self.job_list_frame = tk.Frame(self, bg="white", width=100)
        self.treeview_frame = tk.Frame(self.job_list_frame)
        self.treeview_frame.place()
        self.treeview_scrollbar_frame = tk.Frame(self.job_list_frame)
        self.treeview_scrollbar_frame.place(x=17, width=-17, relheight=1, relwidth=1)
        
        columns = ("selected", "hostname", "status")#, "status_image")
        self.job_list_treeview = ttk.Treeview(self.treeview_scrollbar_frame, columns=columns, show='headings', selectmode="browse")
        self.job_list_treeview.place(relheight=1, relwidth=1)
        
        if tk.Tcl().eval('info patchlevel') == '8.6.9':
            self.style.map('Treeview', foreground=self._fixed_map('foreground'), background=self._fixed_map('background'))
        
        self.job_list_treeview.bind("<Button-1>", self.on_click)
        self.job_list_treeview.bind("<Double-1>", self.on_double_click)
        self.job_list_treeview.bind("<Motion>", self.highlight_row)

        self.job_list_treeview.column('selected', stretch=False, width=20)
        self.job_list_treeview.column('hostname', stretch=True, width=50)
        self.job_list_treeview.column('status', stretch=True, width=8)
        #self.job_list_treeview.column('status_image', stretch=True, width=8)

        self.job_list_treeview.heading('selected', text='☒' if self.all_selected else '☐')
        self.job_list_treeview.heading('hostname', text='Hostname')
        self.job_list_treeview.heading('status', text='Status')
       # self.job_list_treeview.heading('status_image', text='')

        self.job_list_scrollbar = ttk.Scrollbar(self.job_list_frame, orient="vertical", command=self.job_list_treeview.yview)
        self.job_list_scrollbar.place(relheight=1)
        self.job_list_treeview.configure(yscrollcommand=self.job_list_scrollbar.set)
        
        self.job_list_treeview.tag_configure('highlight', background='lightblue')
        self.job_list_treeview.tag_configure('even', background='#F1F1F1')
        self.job_list_treeview.tag_configure('odd', background='white')

        self.refresh_treeview_data()

        ###
        ### Selected Job Data (Right) Config
        ###

        self.job_data_frame = tk.Frame(self, bg="white")
        self.job_data_frame.place()
        
        self.job_hostname = tk.StringVar()
        self.job_hostname.set(test_data[self.selection_index]['hostname'])
        self.job_data_title = tk.Label(self.job_data_frame, textvariable=self.job_hostname)
        self.job_data_title.place(relwidth=1)
        
        self.job_data_window = ttk.Notebook(self.job_data_frame)
        self.job_data_window.place(relwidth=1, relheight=1, y=21)
        
        self.session_log_tab = tk.Frame(self.job_data_window)
        self.job_data_window.add(self.session_log_tab, text="Session Log")
        
        self.session_log = tk.Text(self.session_log_tab, relief=tk.FLAT, highlightthickness=1, highlightbackground="darkgrey")
        self.session_log.place(relwidth=1, relheight=1, height=-18)
        self.session_log.configure(state='disabled')
        self.read_session_log()
        
        
        self.overview_tab = tk.Frame(self.job_data_window)
        self.job_data_window.add(self.overview_tab, text="Overview")

        ###
        ### Top bar frame - input bar
        ###

        self.top_bar_frame_1 = tk.Frame(self, height=24)
        # Username
        tk.Label(self.top_bar_frame_1, text=" Username:").grid(row=0, column=0)
        self.username_entry = ttk.Entry(self.top_bar_frame_1, width=20).grid(row=0, column=1)
        # Password
        tk.Label(self.top_bar_frame_1, text="   Password:" ).grid(row=0, column=2)
        self.password_entry = ttk.Entry(self.top_bar_frame_1, width=20, show="*").grid(row=0, column=3)
        # Job count
        tk.Label(self.top_bar_frame_1, text="   Count:").grid(row=0, column=4)
        self.job_count_entry = ttk.Entry(self.top_bar_frame_1, width=5).grid(row=0, column=5)

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
        tk.Label(self.status_bar_frame, text="Idle").grid(row=0, column=0)

        self.top_bar_frame_1.grid(row=0, column=0, columnspan=3, sticky="ew")
        self.top_bar_frame_2.grid(row=1, column=0, columnspan=3, sticky="ew")
        self.job_list_frame.grid(row=2, column=0, sticky="nsew")
        self.job_data_frame.grid(row=2, column=1, columnspan=2, sticky="nsew")
        self.status_bar_frame.grid(row=3, column=0, columnspan=3, sticky="ew")

    def import_csv(self):
        pass

if __name__ == "__main__":
    root = Application()
    root.mainloop()
import enum
import tkinter as tk
import tkinter.filedialog as fd
import csv, json
from pathlib import Path
from tkinter import Scrollbar, ttk
from turtle import bgcolor

test_data = [
    {
        'selected' : True,
        'hostname' : 'test 1',
        'status' : 'idle'
    },
    {
        'selected' : True,
        'hostname' : 'test 2',
        'status' : 'idle'
    },
    {
        'selected' : True,
        'hostname' : 'test 3',
        'status' : 'idle'
    },
    {
        'selected' : True,
        'hostname' : 'test 4',
        'status' : 'idle'
    },
    {
        'selected' : True,
        'hostname' : 'test 5',
        'status' : 'idle'
    },
    {
        'selected' : True,
        'hostname' : 'test 6',
        'status' : 'idle'
    },
    {
        'selected' : True,
        'hostname' : 'test 7',
        'status' : 'idle'
    },
    {
        'selected' : True,
        'hostname' : 'test 8',
        'status' : 'idle'
    },
    {
        'selected' : True,
        'hostname' : 'test 9',
        'status' : 'idle'
    },
    {
        'selected' : False,
        'hostname' : 'test 10',
        'status' : 'idle'
    }
]

class Application(tk.Tk):

    def OnDoubleClick(self, event):
        item = self.job_list_treeview.selection()
        selection_index = self.job_list_treeview.item(item)['tags'][0]
        test_data[selection_index]['selected'] = not test_data[selection_index]['selected']
        self.refresh_treeview_data()


    def refresh_treeview_data(self):
        self.job_list_treeview.delete(*self.job_list_treeview.get_children())

        for n, entry in enumerate(test_data):
            data = ('☒' if entry['selected'] else '☐', entry['hostname'], entry['status'])
            self.job_list_treeview.insert('', tk.END, values=data, tags=n)

    def __init__(self):
        super().__init__()
        self.title("Cisco Remote Access Program")
        #self.iconbitmap("")
        self.main_frame = tk.Frame(self)
        #self.main_frame.pack(fill="both", expand="true")
        self.geometry("900x500")

        self.toolbar = tk.Menu(self)
        self.config(menu = self.toolbar)

        self.file_menu = tk.Menu(self.toolbar, tearoff="off")
        self.toolbar.add_cascade(label="File", menu=self.file_menu)
        self.file_menu.add_command(label="Import CSV", command=self.import_csv)
        self.file_menu.add_command(label="Open Job", command=self.import_csv)

        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=1)

        
        self.job_list_frame = tk.Frame(self, bg="white")
        columns = ("selected", "hostname", "status")
        self.job_list_treeview = ttk.Treeview(self.job_list_frame, columns=columns, show='headings')
        self.job_list_treeview.place(relheight=1, relwidth=1)
        
        self.job_list_treeview.bind("<Double-1>", self.OnDoubleClick)

        self.job_list_treeview.column('selected', stretch=False, width=22)
        self.job_list_treeview.column('hostname', stretch=True, width=50)
        self.job_list_treeview.column('status', stretch=True, width=10)

        self.job_list_treeview.heading('selected', text='')
        self.job_list_treeview.heading('hostname', text='Hostname')
        self.job_list_treeview.heading('status', text='Status')

        for n, entry in enumerate(test_data):
            data = ('☒' if entry['selected'] else '☐', entry['hostname'], entry['status'])
            self.job_list_treeview.insert('', tk.END, values=data, tags=n)




        self.job_data_frame = tk.Frame(self, bg="red")
        self.job_data_frame.place()


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
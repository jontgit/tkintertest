from tkinter import *

root = Tk()

def move_window(event):
    root.geometry('+{0}+{1}'.format(event.x_root, event.y_root))

root.overrideredirect(True) # turns off title bar, geometry
root.geometry('400x100+200+200') # set new geometry

# make a frame for the title bar
title_bar = Frame(root, bg='grey10', height=30)

# put a close button on the title bar
close = PhotoImage(file = r"./res/titlebar/close.png")
close_button = Button(title_bar, image=close, command=root.destroy, bg="grey10", relief=FLAT)

# a canvas for the main area of the window
window = Canvas(root, bg='black')

# pack the widgets
title_bar.place(height=30, relwidth=1)
close_button.pack(side=RIGHT)
window.pack(expand=1, fill=BOTH)

# bind title bar motion to the move window function
title_bar.bind('<B1-Motion>', move_window)

root.mainloop()
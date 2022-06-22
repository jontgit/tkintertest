import tkinter as tk

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

root.mainloop()
import re
import tkinter as tk
from tkinter import ttk
import tkinter.font as tkfont

class TextLineNumbers(tk.Canvas):
    def __init__(self, *args, **kwargs):
        tk.Canvas.__init__(self, *args, **kwargs)
        self.textwidget = None

    def attach(self, text_widget):
        self.textwidget = text_widget
        
    def redraw(self, *args):
        '''redraw line numbers'''
        self.delete("all")

        i = self.textwidget.index("@0,0")
        while True :
            dline= self.textwidget.dlineinfo(i)
            if dline is None: break
            y = dline[1]
            linenum = str(i).split(".")[0]
            self.create_text(2,y,anchor="nw", text=linenum)
            i = self.textwidget.index("%s+1line" % i)

class LineCount(tk.Canvas):
    def __init__(self, parent):
        super().__init__(parent, bg="grey15")
        
        #self.scrollbar = tk.Scrollbar(parent, orient="vertical")
        #self.scrollbar.pack(side="left", fill="y")
        #self.config(yscrollcommand=self.scrollbar.set)
        #self.scrollbar.config(command=self.yview)
        
        self.bind("<MouseWheel>", self._on_mousewheel)
        self.bind('<Enter>', self._bound_to_mousewheel)
        self.bind('<Leave>', self._unbound_to_mousewheel)
        
        self.frame = tk.Frame(self, bg="grey15")
        self.pack(fill="both", expand=True)
        
        self.create_window(0, 0, window=self.frame, anchor='nw', width=382)

        
        
        #self.frame.place(relheight=1, relwidth=1)
        for i in range(100):
            label = tk.Label(self.frame, bg="grey15", fg="grey80", text=f"{i}", font=("Consolas", 14, "bold"))
            label.place(y=(22*i)+1, x=0, height=22)
            #label.grid(row=i, column=0)


        
        self.config(scrollregion=self.bbox("all"))
        parent.update()

    def _bound_to_mousewheel(self, event):
        self.bind_all("<MouseWheel>", self._on_mousewheel)

    def _unbound_to_mousewheel(self, event):
        self.unbind_all("<MouseWheel>")

    def _on_mousewheel(self, event):
        if self.winfo_height() <= self.winfo_height():
            print(self.winfo_height())
            self.yview_scroll(int(-1*(event.delta/120)), "units")
            print(self.yview_scroll, int(-1*(event.delta/120)))

class CustomText(tk.Text):
    """
    Wrapper for the tkinter.Text widget with additional methods for
    highlighting and matching regular expressions.

    highlight_all(pattern, tag) - Highlights all matches of the pattern.
    highlight_pattern(pattern, tag) - Cleans all highlights and highlights all matches of the pattern.
    clean_highlights(tag) - Removes all highlights of the given tag.
    search_re(pattern) - Uses the python re library to match patterns.
    """
    def __init__(self, master, *args, **kwargs):
        super().__init__(master, *args, **kwargs, bg="grey15", fg="grey80", insertbackground="grey80", font=("Consolas", 14, "bold"))
        self.master = master
        
        font = tkfont.Font(font=self["font"])
        tab_size = font.measure('    ')
        self.config(tabs=tab_size)
        
        # sample tag
        self.tag_config("variable_assignment", foreground="SkyBlue")
        self.tag_config("function_call", foreground="khaki")
        self.tag_config("double_quotes", foreground="burlywood3")
        self.tag_config("single_quotes", foreground="burlywood3")
        self.tag_config("brackets", foreground="yellow")
        self.tag_config("loop_statement", foreground="plum3")
        

        # create a proxy for the underlying widget
        self._orig = self._w + "_orig"
        self.tk.call("rename", self._w, self._orig)
        self.tk.createcommand(self._w, self._proxy)

    def _proxy(self, *args):
        # let the actual widget perform the requested action
        cmd = (self._orig,) + args
        result = self.tk.call(cmd)

        # generate an event if something was added or deleted,
        # or the cursor position changed
        if (args[0] in ("insert", "replace", "delete") or 
            args[0:3] == ("mark", "set", "insert") or
            args[0:2] == ("xview", "moveto") or
            args[0:2] == ("xview", "scroll") or
            args[0:2] == ("yview", "moveto") or
            args[0:2] == ("yview", "scroll")
        ):
            self.event_generate("<<Change>>", when="tail")

        # return what the actual widget returned
        return result   
        
        
    def highlight(self, tag, start, end):
        self.tag_add(tag, start, end)
    
    def highlight_all(self, pattern, tag):
        for match in self.search_re(pattern):
            self.highlight(tag, match[0], match[1])

    def clean_highlights(self, tag):
        self.tag_remove(tag, "1.0", tk.END)

    def search_re(self, pattern):
        """
        Uses the python re library to match patterns.

        Arguments:
            pattern - The pattern to match.
        Return value:
            A list of tuples containing the start and end indices of the matches.
            e.g. [("0.4", "5.9"]
        """
        matches = []
        text = self.get("1.0", tk.END).splitlines()
        for i, line in enumerate(text):
            for match in re.finditer(pattern, line):
                matches.append((f"{i + 1}.{match.start()}", f"{i + 1}.{match.end()}"))
        
        return matches

    def highlight_pattern(self, pattern, tag="match"):
        """
        Cleans all highlights and highlights all matches of the pattern.

        Arguments:
            pattern - The pattern to match.
            tag - The tag to use for the highlights.
        """
        self.clean_highlights(tag)
        self.highlight_all(pattern, tag)

                
     
if __name__ == '__main__':
    root = tk.Tk()

    test_frame = tk.Frame(root, bg="grey15")
    test_frame.place(relheight=1, relwidth=1)
    
    # Example usage
    def highlight_text(args):
        text.highlight_pattern(r"([\w\_\d\-\.]+)(?=\s*\=)", "variable_assignment")
        text.highlight_pattern(r"([\w\_\d\-\.]+)(?:\()", "function_call")
        text.highlight_pattern(r"\".*\"", "double_quotes")
        text.highlight_pattern(r"\'.*\'", "single_quotes")
        text.highlight_pattern(r"[\(\)]", "brackets")
        text.highlight_pattern(r"(^|\s+)(in|for|while|return|break|import)\s+", "loop_statement")

    text = CustomText(test_frame)
    text.place(relheight=1, relwidth=1, x=40, width=-40)
    line_count = TextLineNumbers(test_frame)
    line_count.attach(text)
    line_count.place(relheight=1, width=40)
    #text.pack(side="right", fill="both", expand=True)

    # This is not the best way, but it works.
    # instead, see: https://stackoverflow.com/a/40618152/14507110
    text.bind("<KeyRelease>", highlight_text)

    root.mainloop()

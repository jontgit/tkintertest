import re
import tkinter as tk
from tkinter import ttk
import tkinter.font as tkfont

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

class ScriptEditor(tk.Canvas):
    
    def __init__(self, parent):
        super().__init__(parent)
        
        self.frame = tk.Frame(self)
        self.frame.place(relheight=1, relwidth=1)
        
        self.toolbar = tk.Menu(parent)
        parent.config(menu = self.toolbar)

        self.file_menu = tk.Menu(self.toolbar, tearoff="off")
        self.toolbar.add_cascade(label="File", menu=self.file_menu)
        self.file_menu.add_command(label="Import CSV")
        self.file_menu.add_command(label="Open Job")
        
        self.top_bar_frame_1 = tk.Frame(self, height=24)
        self.top_bar_frame_1.place(relheight=1, height=24)
        
        self.textbox = CustomText(self.frame)
        self.textbox.place(relheight=1, relwidth=1, y=24, height=-24)
                
     
if __name__ == '__main__':
    root = tk.Tk()

    # Example usage
    def highlight_text(args):
        text.highlight_pattern(r"\bhello\b")
        text.highlight_pattern(r"\bworld\b", "match2")
        text.highlight_pattern(r"([\w\_\d\-\.]+)(?=\s*\=)", "variable_assignment")
        text.highlight_pattern(r"([\w\_\d\-\.]+)(?:\()", "function_call")
        text.highlight_pattern(r"\".*\"", "double_quotes")
        text.highlight_pattern(r"\'.*\'", "single_quotes")
        text.highlight_pattern(r"[\(\)]", "brackets")
        text.highlight_pattern(r"(^|\s+)(in|for|while|return|break|import)\s+", "loop_statement")

    text = CustomText(root)
    text.pack()

    # This is not the best way, but it works.
    # instead, see: https://stackoverflow.com/a/40618152/14507110
    text.bind("<KeyRelease>", highlight_text)

    root.mainloop()

import re
import tkinter as tk
from tkinter import ttk
import tkinter.font as tkfont
"""
        text.highlight_pattern(r"([\w\_\d\-\.]+)(?=\s*\=)", "variable_assignment")
        text.highlight_pattern(r"([\w\_\d\-\.]+)(?:\()", "function_call")
        text.highlight_pattern(r"\".*\"", "double_quotes")
        text.highlight_pattern(r"\'.*\'", "single_quotes")
        text.highlight_pattern(r"[\(\)]", "brackets")
        text.highlight_pattern(r"(^|\s+)(in|for|while|return|break|import)\s+", "loop_statement")
"""
syntax = [
    {
        "regex" : r"([\w\_\d\-\.]+)(?=\s*\=|\s+in)",
        "tag" : "variable_assignment",
        "fg" : "skyblue"
    },
    {
        "regex" : r"(^|\s+)()",
        "tag" : "variable_reference",
        "fg" : "skyblue"
    },
    {
        "regex" : r"([\w\_\d\-]+)(?:\()",
        "tag" : "function_call",
        "fg" : "lightgoldenrod"
    },
    {
        "regex" : r"[\(\)]",
        "tag" : "brackets",
        "fg" : "yellow"
    },
    {
        "regex" : r"(r|f)(?=\")",
        "tag" : "text_prepend",
        "fg" : "royalblue"
    },
    {
        "regex" : r"\".*\"",
        "tag" : "double_quotes",
        "fg" : "lightsalmon1"
    },
    {
        "regex" : r"\'.*\'",
        "tag" : "single_quotes",
        "fg" : "lightsalmon1"
    },
    {
        "regex" : r"import\s+([\w\_\-\.]+)",
        "tag" : "import_statement",
        "fg" : "darkcyan"
    },
    {
        "regex" : r"(^|\s+)(in|for|while|return|break|import)\s+",
        "tag" : "loop_statement",
        "fg" : "plum3"
    },
    {
        "regex" : r"\.",
        "tag" : "dot",
        "fg" : "white"
    }
]


class Editor(tk.Frame):
    def __init__(self, parent, title="Untitled - Script Editor", text=""):
        super().__init__(parent, bg="grey15")

        self.toolbar = tk.Menu(self)
        parent.title(title)
        parent.config(menu = self.toolbar)
        parent.geometry("900x500")

        self.file_menu = tk.Menu(self.toolbar, tearoff="off")
        self.toolbar.add_cascade(label="File", menu=self.file_menu)
        self.file_menu.add_command(label="New", command=self.new_file)
        self.file_menu.add_command(label="Open", command=self.open_file)
        self.file_menu.add_command(label="Save", command=self.save)
        self.file_menu.add_command(label="Save As", command=self.save_as)
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Exit", command=self.exit)

        self.edit_menu = tk.Menu(self.toolbar, tearoff="off")
        self.toolbar.add_cascade(label="Edit", menu=self.edit_menu)
        self.edit_menu.add_command(label="Undo", command=self.undo)
        self.edit_menu.add_separator()
        self.edit_menu.add_command(label="Cut", command=self.cut)
        self.edit_menu.add_command(label="Copy", command=self.copy)
        self.edit_menu.add_command(label="Paste", command=self.paste)
        self.edit_menu.add_command(label="Delete", command=self.delete)
        self.edit_menu.add_separator()
        self.edit_menu.add_command(label="Find", command=self.find)

        text = CustomText(self, text)
        text.place(relheight=1, relwidth=1, x=40, width=-40)

    def new_file(self):
        pass

    def open_file(self):
        pass

    def save(self):
        pass

    def save_as(self):
        pass

    def exit(self):
        pass

    def undo(self):
        pass

    def cut(self):
        pass

    def copy(self):
        pass

    def paste(self):
        pass

    def delete(self):
        pass

    def find(self):
        pass

    def non(self):
        pass

class CustomText(tk.Text):
    """
    Wrapper for the tkinter.Text widget with additional methods for
    highlighting and matching regular expressions.

    highlight_all(pattern, tag) - Highlights all matches of the pattern.
    highlight_pattern(pattern, tag) - Cleans all highlights and highlights all matches of the pattern.
    clean_highlights(tag) - Removes all highlights of the given tag.
    search_re(pattern) - Uses the python re library to match patterns.
    """
    def __init__(self, master, text):
        super().__init__(master, bg="grey15", fg="grey80", insertbackground="grey80", font=("Consolas", 14, "bold"), wrap="none")
        self.master = master

        self.insert("end", text)
        if text != "":
            self.highlight_text(0)

        font = tkfont.Font(font=self["font"])
        tab_size = font.measure('    ')
        self.config(tabs=tab_size)
        
        for highlight in syntax:
            self.tag_config(highlight["tag"], foreground=highlight["fg"])
        
        self.bind("<KeyRelease>", self.highlight_text)
        self.bind("<Return>", self.include_tab)

    def include_tab(self, event):
        previous_line = self.get(str(float(self.index("end"))-1),str(float(self.index("end"))))[:-1]
        if re.match(".*:\s*$", previous_line):
            self.insert("end", "\n    ")

    def highlight_text(self, event):
        self.variables = []
        for highlight in syntax:
            if highlight["tag"] == "variable_reference":
                vars = ""
                for var in self.variables:
                    vars += f"{var}|"
                self.highlight_pattern(rf"(?![^\w\_])({vars})(?=[^\w\_])", highlight["tag"])
            else:
                self.highlight_pattern(highlight["regex"], highlight["tag"])
        
    def highlight(self, tag, start, end):
        self.tag_add(tag, start, end)
    
    def highlight_all(self, pattern, tag):
        for match in self.search_re(pattern):
            self.highlight(tag, match[0], match[1])
            if tag == "variable_assignment":
                self.variables.append(match[2])

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
                matches.append((f"{i + 1}.{match.start()}", f"{i + 1}.{match.end()}", match.group()))
        
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


    text = Editor(root)
    text.place(relheight=1, relwidth=1)
    #line_count = TextLineNumbers(test_frame)
    #line_count.attach(text)
    #line_count.place(relheight=1, width=40)
    #text.pack(side="right", fill="both", expand=True)

    # This is not the best way, but it works.
    # instead, see: https://stackoverflow.com/a/40618152/14507110
    #text.bind("<KeyRelease>", highlight_text)

    root.mainloop()

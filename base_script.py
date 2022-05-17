class Script():
    def __init__(self, remote_connection):
        self.remote_connection = remote_connection
        self.title = ""
        self.description = ""
        self.device = ""
        self.base_script = ""

    def run(self):
        pass

        vars = locals()
        del(vars["self"])
        return vars
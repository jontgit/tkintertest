class Script():
    def __init__(self, remote_connection):
        self.remote_connection = remote_connection
        self.title = "Untitled"
        self.description = ""
        self.device = ""
        self.base_script = """# To run commands, enter anything you want to send to a deivce
# within the quotation marks of the below function.
# What ever the device returns will be stored in the 'data' variable.
data = send_command("")

# Anything assigned to the 'returned_data' variable will be visable
# in the 'Return Data' tab, this can be exported per device.
return_data = data
"""

    def run(self):
        pass

        vars = locals()
        del(vars["self"])
        return vars
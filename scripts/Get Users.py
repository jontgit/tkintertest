
class Script():
    def __init__(self, remote_connection):
        self.remote_connection = remote_connection
        self.title = "Get Users"
        self.description = "Gets all users on a firewall and returns them"
        self.device = "Cisco ASA"
        self.base_script = """users = send_command("show run | i username").split('\n')
for user in users:
    print(user)
"""

    def run(self):
        users = self.remote_connection.send_command("show run | i username").split('\n')
        for user in users:
            print(user)
        


        vars = locals()
        del(vars["self"])
        return vars
        
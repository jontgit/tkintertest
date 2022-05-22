
class Script():
    def __init__(self, remote_connection):
        self.remote_connection = remote_connection
        self.title = "Get Users"
        self.description = "Gets all users on a firewall and returns them"
        self.device = "Cisco ASA"
        self.base_script = """users = send_command("show run | i username").split('\\n')
for user in users:
    print(user)

send_command("show int ip br")
send_command("show int ip br")

send_command("copy /noconfirm tftp://10.255.10.12/GitHubDesktopSetup-x64.exe disk0:/")



"""

    def run(self):
        users = self.remote_connection.send_command("show run | i username").split('\n')
        for user in users:
            print(user)
        
        self.remote_connection.send_command("show int ip br")
        self.remote_connection.send_command("show int ip br")
        
        self.remote_connection.send_command("copy /noconfirm tftp://10.255.10.12/GitHubDesktopSetup-x64.exe disk0:/")
        
        
        
        


        vars = locals()
        del(vars["self"])
        return vars
        
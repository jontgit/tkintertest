class Script():
    def __init__(self, remote_connection):
        self.remote_connection = remote_connection
        self.title = "License Auth"
        self.description = "Gets all psks on a firewall and returns them"
        self.device = "Cisco ASA"
        self.base_script = "psks = send_command(\"license smart renew auth\")"

    def run(self):
        self.remote_connection.send_command("license smart renew auth")

        vars = locals()
        del(vars["self"])
        return vars
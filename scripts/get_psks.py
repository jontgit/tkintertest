class Script():
    def __init__(self, remote_connection):
        self.remote_connection = remote_connection
        self.title = "Get PSKs"
        self.description = "Gets all psks on a firewall and returns them"
        self.device = "Cisco ASA"
        self.base_script = "psks = send_command(\"more system:running-config | i ipsec-attributes|pre-shared\").split(\'\n\')"

    def run(self):
        psks = self.remote_connection.send_command("more system:running-config | i ipsec-attributes|pre-shared").split('\n')

        vars = locals()
        del(vars["self"])
        return vars
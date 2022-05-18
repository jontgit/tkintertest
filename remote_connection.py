import datetime
import sys
import json

from netmiko import (
    ConnectHandler,
    NetmikoTimeoutException,
    NetmikoAuthenticationException,
)

class RemoteConnection():

    def __init__(self, job):
        self.read_job_data(job)  # Read Job data first
        self.connect_to_device() # Connect to the device next
        if self.status == "running":
            self.run_script()        # The main commands are issued via this function
            self.logout()            # Once we're here, we can logout and close the session

    def read_job_data(self, job):
        self.return_data = {}
        self.hostname = job['hostname']
        self.username = job['username']
        self.password = job['password']
        self.device_type = job['device_type']
        self.folder = job['log_folder']
        self.additional_data = job['additional_data']
        self.script = job['script'].Script(self)

        self.status = "running"
        self.config = False

    def write_error_log(self, error):
        with open(f"{self.folder}{self.current_time.strftime('%Y-%m-%d-%H-%M-%S')}---{self.hostname}.log", 'w') as log_file:
            log_file.write(str(error))

    def connect_to_device(self):
        self.current_time = datetime.datetime.now()
        self.device = {
            "device_type": self.device_type,
            "host": self.hostname,
            "username": self.username,
            "password": self.password,
            "secret": self.password,
            "session_log": f"{self.folder}{self.current_time.strftime('%Y-%m-%d-%H-%M-%S')}---{self.hostname}.log",
        }

        try:
            self.remote_connection = ConnectHandler(**self.device)
            self.remote_connection.enable()
            
        except NetmikoTimeoutException as error:
            print(error)
            self.status = "unreachable"
            self.write_error_log(error)
            #exit()
            
        except NetmikoAuthenticationException as error:
            print("auth error")
            self.status = "auth error"
            self.write_error_log(error)
            #exit()
            
        except: # Handle everything unexpected - I imagine this probably isn't PEP8 compliant... I just want the thread to close after something unexpected.
            print("Unexpected error:", sys.exc_info()[0])
            self.status = "program error"
            raise
                    
    def logout(self):
        self.remote_connection.disconnect()
        self.status = "complete"

    def send_command(self, command) -> str:
        # TODO - generic error handling of '^'
        
        if self.config:
            if command == 'end':
                self.config = False
            
            response = self.remote_connection.send_command(command, expect_string='.*#')#, read_timeout=10)

        else:
            if command in ['conf t', 'configure t', 'configure terminal']:
                self.config = True
                response = self.remote_connection.send_command(command, expect_string='.*#')#, read_timeout=10)
            else:

                response = self.remote_connection.send_command(command)#, read_timeout=10)



        return response

    def run_script(self):
        """
        The selected script is parsed here.
        
        
        """
        
        self.return_data = self.script.run()

        print(json.dumps(self.return_data, indent=4))

        self.logout()
import datetime
import sys
import json
import os
import time

from netmiko import *

class RemoteConnection():

    def __init__(self, job, root):
        self.root = root
        self._read_job_data(job)  # Read Job data first
        self._connect_to_device() # Connect to the device next
        if self.thread_status == "connected":
            self._run_script()        # The main commands are issued via this function
            self._logout()            # Once we're here, we can _logout and close the session

    def _read_job_data(self, job):
        self.return_data = {}
        self.hostname = job['hostname']
        self.username = job['username']
        self.password = job['password']
        self.enable = job['enable']
        self.device_type = job['device_type']
        self.folder = job['log_folder']
        self.index = job['index']
        self.additional_data = job['additional_data']
        self.script = job['script'].Script(self)

        self.thread_status = "connecting" # Specficially used for the worker to keep track of the job
        self.status = "connecting"
        self.config = False

    def _write_error_log(self):
        time.sleep(0.1)
        os.remove(f"{self.folder}{self.current_time.strftime('%Y-%m-%d-%H-%M-%S')}---{self.hostname}.log")

    def _write_error_log(self, error):
        with open(f"{self.folder}{self.current_time.strftime('%Y-%m-%d-%H-%M-%S')}---{self.hostname}.log", 'w') as log_file:
            log_file.write(str(error))

    def _set_gui_status(self, status, image="normal"):
        self.root.device_data[self.index]['status'] = status
        self.root.job_list.update_job_status(self.index)

    def _connect_to_device(self):
        self.current_time = datetime.datetime.now()
        print(f"connecting to {self.hostname}")
        self.set_status("connecting")
        self.device = {
            "device_type": self.device_type,
            "host": self.hostname,
            "username": self.username,
            "password": self.password,
            "secret": self.enable,
            "fast_cli" : False,
            "session_log": f"{self.folder}{self.current_time.strftime('%Y-%m-%d-%H-%M-%S')}---{self.hostname}.log",
        }

        try:
            self.remote_connection = ConnectHandler(**self.device)
            
            print("MSDMASMDMASMDMASD")
            print(self.remote_connection.find_prompt())

            #self.remote_connection.enable()

            self.thread_status = "connected"
            
        except NetmikoTimeoutException as error:
            #self.remote_connection.disconnect()
            print(f"{self.hostname} unreachable")
            self.root.device_data[self.index]['active'] = False
            self.set_status("unreachable")
            self.thread_status = "unreachable"
            
            #self._write_error_log()
            #exit()
            
        except ReadTimeout as error:
            #self.remote_connection.disconnect()
            print(f"{self.hostname} unreachable")
            self.root.device_data[self.index]['active'] = False
            self.set_status("unreachable")
            self.thread_status = "unreachable"
            
            #self._write_error_log()
            #exit()
            
        except NetmikoAuthenticationException as error:
            #self.remote_connection.disconnect()
            print("auth error")
            self.set_status("auth error")
            self.thread_status = "auth error"
            #self._write_error_log()
            #self._write_error_log(error)
            #exit()
            
        except: # Handle everything unexpected - I imagine this probably isn't PEP8 compliant... I just want the thread to close after something unexpected.
            print("Unexpected error:", sys.exc_info()[0])
            self.set_status("program error")
            self.thread_status = "program error"
            self._write_error_log(sys.exc_info()[0])
            raise
                    
    def _logout(self):
        self.remote_connection.disconnect()

        if self.status == "running": # Else custom status
            self.set_status("complete")

        self.thread_status = "complete"

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

            elif 'copy' in command:
                # If we're copying, need to put a huge delay factor in as the file will take some time to transfer
                response = self.remote_connection.send_command(command, expect_string=".*#", delay_factor=40)

            else:
                response = self.remote_connection.send_command(command)#, read_timeout=10)

        return response

    def set_status(self, status):
        self.status = status
        self.root.device_data[self.index]['status'] = status
        self.root.job_list.update_job_status(self.index)

    def _run_script(self):
        self.thread_status = "running"
        self.set_status("running")
        """
        The selected script is parsed here.        
        """
        
        self.return_data = self.script.run()

        print(json.dumps(self.return_data, indent=4))

        self._logout()
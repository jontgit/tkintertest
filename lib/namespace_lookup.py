from threading import Thread
import time
import socket

class NamespaceLookup(Thread):
    
    def __init__(self, root, lookup_queue):
        Thread.__init__(self)
        self.daemon = True
        self.lookup_queue = lookup_queue
        self.root = root


    def run(self):
        while True:
            if not self.lookup_queue.empty():
                device = self.lookup_queue.get()
                Thread(target=self.lookup, daemon=True, args=(device,)).start()
                
            else:
                time.sleep(0.1)

    def lookup(self, device):
        address = None
        try:
            time.sleep(0.1)
            address = socket.gethostbyname(device['hostname'])
            if device["index"] < len(self.root.device_data):
                if self.root.device_data[device["index"]]['hostname'] == device['hostname']:
                    self.root.device_data[device["index"]]['address'] = address
                    if self.root.job_list.focus_index == device['index']:
                        self.root.job_data.update_address()
                    
        except socket.gaierror:
            if device["index"] < len(self.root.device_data):
                if self.root.device_data[device["index"]]['hostname'] == device['hostname']:
                    self.root.device_data[device["index"]]['active'] = False
                    self.root.job_list.update_job_status(device["index"], "unreachable")
                    self.root.job_list.update_job_icon(device["index"], "unreachable")

        self.lookup_queue.task_done()

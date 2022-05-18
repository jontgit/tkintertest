from threading import Thread
import time
import socket

class NamespaceLookup(Thread):
    
    def __init__(self, root, lookup_queue):
        Thread.__init__(self)
        self.daemon = True
        self.lookup_queue = lookup_queue
        self.root = root
        self.time_out = False
        
    def run(self):
        while True:
            if not self.lookup_queue.empty():
                device = self.lookup_queue.get()
                Thread(target=self.lookup, daemon=True, args=(device,)).start()
                
            else:
                time.sleep(0.1)

    def lookup(self, device):
        try:
            time.sleep(0.1)
            address = socket.gethostbyname(device['hostname'])
            self.root.device_data[device["index"]]['address'] = address
        except socket.gaierror:
            self.root.device_data[device["index"]]['active'] = False
            self.root.device_data[device["index"]]['status'] = "unreachable"
            
        self.root.job_list.update_job_status(device["index"])
        self.lookup_queue.task_done()
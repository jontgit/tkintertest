
from remote_connection import RemoteConnection
from threading import Thread
import time

class WorkerThread(Thread):
    def __init__(self, work_queue, complete_queue, root):
        """
        Worker threads handle spinning up the actual remote-connection
        class in order to initiate a SSH/Telnet session and run commands.
        These will recieve work from the work queue, which is a 'job'
        template. This will contain all the relevant information like the 
        below: 
            Username
            Password
            Hostname/IP address
            Job Index
            Device Type (If ASA/IOS or SSH/Telnet)
            Additional Data
            
        Additional Data can be used to pass additional data that may be needed
        for the script that we're running. For instance if we're making a custom
        object-group on an ASA, we could pass a number of IP addresses unique to
        each device.
        
        Args:
            work_queue (_type_): _description_
            complete_queue (_type_): _description_
        """

        Thread.__init__(self)
        self.daemon = True
        self.work_queue = work_queue
        self.complete_queue = complete_queue
        self.root = root

    def run(self):
        """
        Has a while loop running to constantly find a job to do. Once a job
        is available, this will spin up the RemoteConnection Class to complete
        the script in question. Once this script has finished, the status of
        the class will no longer be 'running', and at this point the job is 
        complete and added back to the complete where the main process loop
        is waiting for the relevant data.
        """
        while True:
            if not self.work_queue.empty():
                job = self.work_queue.get()
                remote_connection = RemoteConnection(job, self.root)
                if remote_connection.thread_status not in ['connecting','connected','running']:
                    f"Job Finished: {remote_connection.hostname}"
                    self.complete_queue.put({
                        "username" : remote_connection.username,
                        "hostname" : remote_connection.hostname,
                        "index" : job['index'],
                        "status" : remote_connection.status,
                        "return_data" : remote_connection.return_data
                        })
                    self.work_queue.task_done()

            time.sleep(0.1)

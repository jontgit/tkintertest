from threading import Thread
from worker import WorkerThread
from queue import Queue
import time

CONCURRENT_SSH_LIMIT = 5

class ManagerThread(Thread):
    def __init__(self, manager_queue, complete_queue):
        """
        Manager thread handles sending out jobs to all the worker
        threads and spins up the relevant amount of threads to run
        job concurrently. 
        Args:
            manager_queue (_type_): _description_
            complete_queue (_type_): _description_
        """
        
        Thread.__init__(self)
        self.daemon = True
        self.manager_queue = manager_queue
        self.work_queue = Queue(maxsize=CONCURRENT_SSH_LIMIT)
        self.worker_threads = []
        for i in range(CONCURRENT_SSH_LIMIT):
            self.worker_threads.append(WorkerThread(self.work_queue, complete_queue).start())

    def run(self):
        while True:
            if not self.manager_queue.empty():
                if not self.work_queue.full():
                    self.work_queue.put(self.manager_queue.get())
            time.sleep(0.1)
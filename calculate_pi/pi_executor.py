#!/usr/bin/env python
# Author: Robin Dong <robin.k.dong@gmail.com>

import sys
import time
import random
import threading
from multiprocessing import Process,Queue

import mesos.interface
from mesos.interface import mesos_pb2
import mesos.native

NR_ITERATE = 10000000

# The monte carlo algorithm for calculating PI:
# https://learntofish.wordpress.com/2010/10/13/calculating-pi-with-the-monte-carlo-method/
def monte_carlo(queue):
    circle_area = 0
    square_area = 0

    for i in range(0, NR_ITERATE):
        x = random.random()
        y = random.random()
        # if in circle
        if (x**2 + y**2) <= 1:
            circle_area = circle_area + 1
        square_area = square_area + 1
    queue.put([circle_area, square_area])

class PiExecutor(mesos.interface.Executor):
    def launchTask(self, driver, task):

        def run_thread():
            # The threading of python can not use up multi-cores:
            # (https://en.wikipedia.org/wiki/Global_Interpreter_Lock)
            # so we use multi-processes to run monte carlo algorithm and 
            # send all calculating results by multi-threads.
            queue = Queue()
            process = Process(target=monte_carlo, args=(queue,))
            process.start()
            values = queue.get()

            update = mesos_pb2.TaskStatus()
            update.task_id.value = task.task_id.value
            update.state = mesos_pb2.TASK_FINISHED
            update.data = "%u, %u" % (values[0], values[1])
            driver.sendStatusUpdate(update)
            print "Sent status update"

        thread = threading.Thread(target=run_thread)
        thread.start()

if __name__ == "__main__":
    print "Starting executor"
    driver = mesos.native.MesosExecutorDriver(PiExecutor())
    sys.exit(0 if driver.run() == mesos_pb2.DRIVER_STOPPED else 1)

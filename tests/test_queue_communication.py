import random
import time
import multiprocessing
from pymulproc import factory, mpq_protocol


class ChildProcess:
    def __init__(self, identifier, parent_pid, conn):
        self.id = identifier
        self.conn = conn
        self.parent_pid = parent_pid
        self.pid = multiprocessing.current_process().pid

    def is_message_for_me(self, message):
        '''The message is for me if either the recipient_pid is coincides with my pid or is None - None indicates
        that the message is for everyone
        '''
        return message[mpq_protocol.S_PID_OFFSET + 1] == self.pid or not message[mpq_protocol.S_PID_OFFSET + 1]

    def run(self, **kwargs):
        '''it defines the behaviour of the child process as follows:

        1) If the data is provided as argument => the child process just send the received data back to the parent
        2) Otherwise fetch the front message of the queue and check if it is for us:

            2.1) Either the recipient pid coincides with ours => our identifier is sent back to the parent...
            2.2) Or eventually we get an instruction to die and we do so.
        '''

        data = kwargs.get('data', None)
        if data:
            self.conn.send(mpq_protocol.REQ_FINISHED, data=data)
        else:
            stop = False
            while not stop:
                time.sleep(0.1)
                message = self.conn.receive(func=self.is_message_for_me)
                if message:
                    if message[mpq_protocol.S_PID_OFFSET - 1] == mpq_protocol.REQ_DIE:
                        stop = True
                    else:
                        self.conn.send(mpq_protocol.REQ_FINISHED, recipient_pid=self.parent_pid, data=self.id)


def call_child(identifier, parent_pid, q_factory, data):
    child = ChildProcess(identifier, parent_pid, q_factory.child())
    child.run(data=data)


def parent_full_duplex_communication_with_children(min_processes, max_processes):
    '''A parent send a message to a specific child and this, and only this, responds with its identifier. Once the the
    parent confirms that such message has been received, it sends an DIE request to all children for them all to die.
    '''
    queue_factory = factory.QueueCommunication()
    parent = queue_factory.parent()
    parent_pid = multiprocessing.current_process().pid

    # (1) Prepare list of processes to start and pass the value = 3 to each child process
    child_processes = []
    for offset in range(max_processes):
        child_process = multiprocessing.Process(name=f'child_process_{offset}',
                                                target=call_child,
                                                args=(offset + 1, parent_pid, queue_factory, None))
        child_processes.append({'process': child_process})

    # (2) Start processes
    for child in child_processes:
        child['process'].start()
        child['pid'] = child['process'].pid

    # (3) Send a message 3th process
    identifier = min_processes
    parent.send(mpq_protocol.REQ_DO, recipient_pid=child_processes[identifier - 1]['pid'])
    time.sleep(1)

    # (4) Wait for answer from process 3th
    stop = False
    message = False
    while not stop:
        message = parent.receive(func=lambda sms: sms[mpq_protocol.R_PID_OFFSET] == parent_pid)
        if message:
            stop = True

    # (5) Only one message for us parent was in the queue and it should contain the identifier of process 3
    assert message[mpq_protocol.S_PID_OFFSET + 2] == identifier
    assert parent.queue_empty()

    # (6) Indicate all process to die
    for _ in range(len(child_processes)):
        parent.send(mpq_protocol.REQ_DIE)

    # (7) Wait for all processes to finish
    for child in child_processes:
        child['process'].join()

    # Ensure the queue is actually empty - meaning all child processes did fetch their targeted DIE message
    parent.queue_join()


def test_children_to_parent_communication():
    '''Simple test where all child processes send a message to the parent process

    All children are initiated with a value that is sent to the parent for it to process it.
    '''

    queue_factory = factory.QueueCommunication()
    parent = queue_factory.parent()
    parent_pid = multiprocessing.current_process().pid

    # Prepare list of processes to start and pass the value = 3 to each child process
    child_processes = []
    val = 3
    for offset in range(5):
        child_process = multiprocessing.Process(name=f'child_process_{offset}',
                                                target=call_child,
                                                args=(offset + 1, parent_pid, queue_factory, val))
        child_processes.append(child_process)

    # Start processes
    for child in child_processes:
        child.start()

    # Wait for the processes to finish
    for child in child_processes:
        child.join()

    # Receive the data from all children
    counter = 0
    data_offset = mpq_protocol.S_PID_OFFSET + 2
    while not parent.queue_empty():
        message = parent.receive()
        counter += message[data_offset]

    # Ensure the queue is empty - no loose strings
    parent.queue_join()

    # Ensure we got the right data from children
    assert counter == val * len(child_processes)


def test_parent_full_duplex_communication_with_children_stress_test():
    '''A stress test to ensure the full duplex communication is working as expected. For example, that the
    'time.sleep(x)' does not have an undesired effect by correcting out tests when these should be wrong
    '''
    for _ in range(10):
        min_p = random.randint(1, 5)
        max_p = random.randint(min_p, 10)
        parent_full_duplex_communication_with_children(min_p, max_p)

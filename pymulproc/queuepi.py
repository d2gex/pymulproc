import queue

from pymulproc import errors
from pymulproc import mpq_protocol, interfaces

QUEUE_PUT_TIMEOUT_OP = 0.1
NUM_ATTEMPTS = 10


class QueueCommunicationApi(interfaces.CommunicationApiInterface):
    '''Class that implements the CommunicationApi interface for JOINED QUEUE communication between two process in a
        1 to N pattern
    '''

    def __init__(self, *args, **kwargs):
        super().__init__(*args)
        self.timeout = kwargs.get('timeout', QUEUE_PUT_TIMEOUT_OP)
        self.loops = kwargs.get('loops', NUM_ATTEMPTS)

    def send(self, request, sender_pid=None, recipient_pid=None, data=None):
        '''sends a message down the JOINED QUEUE

        it will try to put a message into the QUEUE for a few attempts before raising an exception
        '''

        message = [request, self.pid if not sender_pid else sender_pid, recipient_pid, data]
        stop = False
        loops = self.loops
        while not stop:
            try:
                self.conn.put(message, timeout=self.timeout)
            except queue.Full as ex:
                loops -= 1
                if not loops:
                    raise errors.QueuesCommunicationError(f"Process {self.pid} tried unsuccessfully to put the "
                                                          f"following {message} in the queue") from ex
            else:
                stop = True
        return message

    def receive(self, **kwargs):
        '''High Order function that checks if a message is ready to be fetched from a JOINED QUEUE and if it is whether
        is for the process doing the enquiry or not.

        1) If not 'func' keyword parameter is passed to this function => the process will always fetch the message
        in front of the queue, if there exist one.
        2) If by contrary a 'func' parameter is associated to a function, such function is applied to the message
        at the front of the queue and if the result is True the the process will fetch the message from the queue.
        Otherwise it will reinsert the message at the back of the queue.
        '''

        try:
            message = self.conn.get(block=False)
        except queue.Empty:  # Is the queue empty?...
            message = False
        else:  # ... Otherwise check if this message meets the criteria of the function passed as parameter
            func = kwargs.get('func', lambda x: True)
            if not func(message):
                args = [message[mpq_protocol.S_PID_OFFSET - 1]]
                # As the message isn't for us
                kwargs = {
                    'sender_pid': message[mpq_protocol.S_PID_OFFSET],
                    'recipient_pid': message[mpq_protocol.S_PID_OFFSET + 1]
                }
                if len(message) == 4:
                    kwargs['data'] = message[mpq_protocol.S_PID_OFFSET + 2]
                self.send(*args, **kwargs)  # We put the message again back into the queue as it was not for us
                message = False
            # conn.get() did actually remove a message from the queue needs to be aware of such removal
            self.conn.task_done()

        return message

    def queue_empty(self):
        '''Wrapper method for the queue.emtpy() that check if the queue is empty
        '''
        return self.conn.empty()

    def queue_join(self):
        '''Wrapper method for the queue.join() that wait until all tasks have been done
        '''
        self.conn.join()


class Parent(QueueCommunicationApi):
    '''Class that will instantiate the parent process' peer - It's QUEUE-based communication end
    '''

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.peer = mpq_protocol.PARENT_COMM_INTERFACE


class Child(QueueCommunicationApi):
    '''Class that will instantiate the child process' peer - It's QUEUE-based communication end
    '''

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parent = mpq_protocol.CHILD_COMM_INTERFACE

import queue

from pymulproc import errors
from pymulproc import mpq_protocol, interfaces

QUEUE_PUT_TIMEOUT_OP = 0.1
NUM_ATTEMPTS = 10


class QueueCommunicationApi(interfaces.CommunicationApi):
    '''Class that implements the CommunicationApi interface for JOINED QUEUE communication between two process in a
        1 to N pattern
    '''

    def __init__(self, *args):
        super().__init__(args[0])
        self.timeout = args[1]

    def send(self, request, recipient_pid=None, data=None):
        '''sends a message down the JOINED QUEUE

        it will try to put a message into the QUEUE for a few attempts before raising an exception
        '''

        message = [request, str(self.pid), recipient_pid]
        if data:
            message.append(data)

        stop = False
        loops = NUM_ATTEMPTS
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

    def receive(self, func):
        '''Check if a message is ready to be fetched from a JOINED QUEUE

        This High order function that takes another function as parameter in order to check if the latest message in the
        queue meets a certain criteria. The criteria usually is to check if the message received is for us.
        '''

        try:
            message = self.conn.get(block=False)
        except queue.Empty:  # Is the queue empty?...
            message = False
        else:  # ... Otherwise check if this message meets the criteria of the function passed as parameter
            if not func(message):
                args = [message[0]]
                kwargs = {
                    'recipient_pid': message[2]
                }
                if len(message) == 4:
                    kwargs['data'] = message[-1]
                self.send(*args, **kwargs)  # We put the message again back into the queue as it was not for us
                message = False
            # conn.get() did actually remove a message from the queue needs to be aware of such removal
            self.conn.task_done()

        return message

    def join(self):
        '''Wrapper method for the queue.join() that wait until all tasks have been done
        '''
        self.conn.join()


class ParentQueueComm(QueueCommunicationApi):
    '''Class that will instantiate the parent process' peer - It's QUEUE-based communication end
    '''

    def __init__(self, *args):
        super().__init__(*args)
        self.peer = mpq_protocol.PARENT_COMM_INTERFACE


class ChildQueueComm(QueueCommunicationApi):
    '''Class that will instantiate the child process' peer - It's QUEUE-based communication end
    '''

    def __init__(self, *args):
        super().__init__(*args)
        self.parent = mpq_protocol.CHILD_COMM_INTERFACE


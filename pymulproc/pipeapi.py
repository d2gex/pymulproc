from pymulproc import mpq_protocol, interfaces


class PipeCommunicationApi(interfaces.CommunicationApiInterface):
    '''Class that implements the CommunicationApi interface for PIPE communication between two process in a
    1 to 1 pattern
    '''

    def __init__(self, *args, **kwargs):
        super().__init__(*args)

    def send(self, request, sender_pid=None, recipient_pid=None, data=None):
        '''sends a message down the PIPE
        '''
        message = [request, self.pid, recipient_pid, data]
        self.conn.send(message)
        return message

    def receive(self, **kwargs):
        '''Check if a message is ready to be caught from the PIPE
        '''
        if self.conn.poll():
            return self.conn.recv()
        return False


class Parent(PipeCommunicationApi):
    '''Class that will instantiate the parent process' peer - It's PIPE communication end
    '''

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.peer = mpq_protocol.PARENT_COMM_INTERFACE


class Child(PipeCommunicationApi):
    '''Class that will instantiate the child process' peer - It's PIPE communication end
    '''

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.peer = mpq_protocol.CHILD_COMM_INTERFACE

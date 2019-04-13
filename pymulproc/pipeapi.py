from pymulproc import mpq_protocol, interfaces


class PipeCommunicationApi(interfaces.CommunicationApi):
    '''Class that implements the CommunicationApi interface for PIPE communication between two process in a
    1 to 1 pattern
    '''

    def __init__(self, *args):
        super().__init__(*args)

    def send(self, request, recipient_pid=None, data=None):
        '''sends a message down the PIPE
        '''
        message = [request, str(self.pid), recipient_pid]
        if data:
            message.append(data)
        self.conn.send(message)

    def receive(self):
        '''Check if a message is ready to be caught from the PIPE
        '''
        if self.conn.poll():
            return self.conn.recv()
        return False


class ParentPipeComm(PipeCommunicationApi):
    '''Class that will instantiate the parent process' peer - It's PIPE communication end
    '''

    def __init__(self, *args):
        super().__init__(*args)
        self.peer = mpq_protocol.PARENT_COMM_INTERFACE


class ChildPipeComm(PipeCommunicationApi):
    '''Class that will instantiate the child process' peer - It's PIPE communication end
    '''

    def __init__(self, *args):
        super().__init__(*args)
        self.peer = mpq_protocol.CHILD_COMM_INTERFACE




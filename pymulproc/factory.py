import multiprocessing

from pymulproc import interfaces, pipeapi, queuepi


class PipeCommunication(interfaces.CommInterfaceFactory):
    '''Class Factory used to create PIPE-based connection peers
    '''

    def __init__(self):
        self.parent_conn, self.child_conn = multiprocessing.Pipe()

    def parent(self, *args):
        '''it will create the parent process's connection peer
        '''
        return pipeapi.ParentPipeComm(self.parent_conn)

    def child(self, *args):
        '''it will create the child process's connection peer
        '''
        return pipeapi.ChildPipeComm(self.child_conn)


class QueueCommunication(interfaces.CommInterfaceFactory):
    '''Class Factory used to create QUEUE-based connection peers
    '''

    def __init__(self, maxsize=0):
        self.queue = multiprocessing.JoinableQueue(maxsize)

    def parent(self, *args):
        '''it will create the parent process's connection peer
        '''
        try:
            timeout = args[0]
        except IndexError:
            return queuepi.ParentQueueComm(self.queue, queuepi.QUEUE_PUT_TIMEOUT_OP)
        else:
            return queuepi.ParentQueueComm(self.queue, timeout)

    def child(self, *args):
        '''it will create the child process's connection peer
        '''
        try:
            timeout = args[0]
        except IndexError:
            return queuepi.ChildQueueComm(self.queue, queuepi.QUEUE_PUT_TIMEOUT_OP)
        else:
            return queuepi.ChildQueueComm(self.queue, timeout)
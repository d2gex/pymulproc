import multiprocessing

from pymulproc import interfaces, pipeapi, queuepi


class PipeCommunication():
    '''Class Factory used to create PIPE-based connection peers
    '''

    def __init__(self):
        self.parent_conn, self.child_conn = multiprocessing.Pipe()

    def parent(self, **kwargs):
        '''it will create the parent process's connection peer
        '''
        return pipeapi.Parent(self.parent_conn, **kwargs)

    def child(self, **kwargs):
        '''it will create the child process's connection peer
        '''
        return pipeapi.Child(self.child_conn, **kwargs)


class QueueCommunication():
    '''Class Factory used to create QUEUE-based connection peers
    '''

    def __init__(self, **kwargs):
        max_size = kwargs.get('max_size', 0)
        self.queue = multiprocessing.JoinableQueue(max_size)

    def parent(self, **kwargs):
        '''it will create the parent process's connection peer
        '''
        return queuepi.Parent(self.queue, **kwargs)

    def child(self, **kwargs):
        '''it will create the child process's connection peer
        '''
        return queuepi.Child(self.queue, **kwargs)

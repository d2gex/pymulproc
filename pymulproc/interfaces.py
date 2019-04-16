import abc
import multiprocessing


class CommunicationApiInterface(abc.ABC):
    '''Define the interface that each end wil handler to communicate with each other
    '''
    def __init__(self, conn):
        self.conn = conn
        self.pid = multiprocessing.current_process().pid

    @abc.abstractmethod
    def send(self, request, sender_pid=None, recipient_pid=None, data=None):
        ''''send' method to be implemented at each end and used to send information down the PIPE or to a
        Joined Queue, respectively

        :param request: type of action requested to the other end
        :param sender_pid: pid of the sender process
        :param recipient_pid: pid of the process to which the request is addressed to
        :param data: extra data to be passed on
        '''
        pass

    @abc.abstractmethod
    def receive(self, **kwargs):
        ''''send' method to be implemented at each end and used to catch or fetch information from the PIPE or a Joined
        Queue, respectively.
        '''
        pass

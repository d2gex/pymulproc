import abc
import multiprocessing


class CommunicationInterfaceApi(abc.ABC):
    '''Define the interface that each end wil handler to communicate with each other
    '''
    def __init__(self, conn):
        self.conn = conn
        self.pid = multiprocessing.current_process().pid

    @abc.abstractmethod
    def send(self, request, recipient_pid=None, data=None):
        ''''send' method to be implemented at each end and used to send information down the PIPE or to a
        Joined Queue, respectively

        :param request: type of action requested to the other end
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


class CommInterfaceFactory(abc.ABC):
    '''Define the factory that will create the two different ends that will use the CommunicationApi interface
    to communicate with each other
    '''

    @abc.abstractmethod
    def parent(self, *args):
        ''''parent' method to be implemented and used to create the end connection that a parent process will
        hold.
        '''
        pass

    @abc.abstractmethod
    def child(self, *args):
        ''''child' method to be implemented and used to create the end connection that a child process will hold
        '''
        pass


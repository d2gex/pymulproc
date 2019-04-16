==========================================================
``pymulproc`` a tiny multiprocessing communication library
==========================================================

.. image:: https://travis-ci.com/d2gex/pymulproc.svg?branch=master
    :target: https://travis-ci.com/d2gex/pymulproc

.. image:: https://img.shields.io/badge/pypi_package-0.1.1-brightgreen.svg
    :target: #

**pymulproc** is a tiny library to handle the communication between multiple processes without external
dependencies other than Python's standard library. It is based purely in the multiprocessing library and provides a
common interface for both PIPE and QUEUE communication.

pymulproc Protocol
===================
**pymulproc** uses a simple python list as the basis of the communication with the following fields:

1. ``request``: a **required** string indicating the other peer what the operation is about.
2. ``sender pid``: a **required** integer indicating the PID of the processing sending the datagram.
3. ``recipient pid``: an **optional** integer indicating the PID of the process which this message is targeted to.
4. ``data``: an **optional** python data structure containing the information intended for the other peer.

In turns the requests sent in the data structure could be anything however **pymulproc** uses the following standards:

6. ``REQ_DO``: requests that indicates the other peer to do a task.
7. ``REQ_FINISHED``: requests that indicates the other peer that the task has been done.
8. ``REQ_DIE``: requests that indicates the other peer to stop and die as soon as possible. Practically a poison pill.

Example of valid message structures are shown below. **The message must always have a length of 4**:

.. code-block:: python

    ['DO', 1234, 12345, {'value': 20}]  # request, sender PID, recipient PID, data
    ['DO', 1234, 12345, None]  # request, sender PID, recipient PID
    ['DIE', 1234, None, None]  # request, sender PID

pymulproc API
===================
**pymulproc** offers a common API interface for the conversation exchange between a parent process and its children
for both PIPE and QUEUE communication as follows:

9.  ``send``: sends a message down the PIPE for 1:1 conversation or put a message in a JoinedQueue for 1:M, M:1 and M:M
    conversations.
10. ``receive``: check if there is a message in the PIPE or at the front of the QUEUE for the process making such
    an enquiry. if the message is not intended for the process making the enquiry False is returned. In case the
    communication is done via QUEUEs, the method puts back the message in the queue so that the targeted process can
    later on fetch it.

Queue's communication add two more specific method: ``queue_empty`` to check if the queue is empty of tasks and
``queue_join`` to wait there until all the queue is empty.

Among the optional parameters of the  ``send`` method signature shown below, is worthwhile highlighting ``sender_pid``.
If provided, such integer is added to the message as sender PID. Otherwise the process will add its own
PID.

``send`` will try to place the message in the queue, for queue communication only, a few times before raising an
exception. The amount of tries can be configured when instantiating the connection handler - see ``QueueCommunicationApi``
class' constructor for further details.

.. code-block:: python

    @abc.abstractmethod
        def send(self, request, sender_pid=None, recipient_pid=None, data=None):

``receive`` is a High Order function and may take a ``func`` keyword argument associated to a function that applies
an operation to the message at the front of the queue. If the result is True, then the message is for the enquiring
process. Otherwise it is 'reinserted' at the back of the queue for other processes to check on it.

If not parameters are passed, it is understood that the message at front of the queue is always for enquiring process.
An example where the criteria to check if the message is for the enquiring process always fails, is shown below:

.. code-block:: python

    child.receive(lambda x: False)


Installing pymulproc
====================

**pymulproc** is available on PyPI_, so you can install it with ``pip``::

    $ pip install pymulproc


pymulproc PIPE communication example
======================================
Below a simple example of PIPE communication betwen a parent and a single child process is shown:

.. code-block:: python

    import multiprocessing
    from pymulproc import factory, mpq_protocol

    def test_simple_pipe_communication():

        pipe_factory = factory.PipeCommunication()
        parent = pipe_factory.parent()
        child = pipe_factory.child()

        def call_child(_child):
            _child.send(mpq_protocol.REQ_TEST_CHILD)

        child_process = multiprocessing.Process(name='child_process_',
                                                target=call_child,
                                                args=(child, ))
        child_process.start()
        child_process.join()
        message = parent.receive()
        request_offset = mpq_protocol.S_PID_OFFSET - 1
        assert message[request_offset] == mpq_protocol.REQ_TEST_CHILD

pymulproc simple 1:N QUEUE communication example
=================================================
The example below shows how child processes send some data back to the parent. Notice how the parent passes no ``func``
parameter to ``receive`` as all messages placed in the queue by the child processes are intended for the parent itself:

.. code-block:: python

    import multiprocessing
    from pymulproc import factory, mpq_protocol


    class ChildProcess:
        def __init__(self, identifier, parent_pid, conn):
            self.id = identifier
            self.conn = conn
            self.parent_pid = parent_pid
            self.pid = multiprocessing.current_process().pid

        def is_message_for_me(self, message):
            '''The message is for me if either the recipient_pid coincides with my pid or is None - None indicates
            that the message is for everyone
            '''
            return message[mpq_protocol.S_PID_OFFSET + 1] == self.pid or not message[mpq_protocol.S_PID_OFFSET + 1]

        def run(self, **kwargs):
            '''Sends the data passed as keyword parameter to the parent process:
            '''

            data = kwargs.get('data', None)
            self.conn.send(mpq_protocol.REQ_FINISHED, data=data)


    def call_child(identifier, parent_pid, q_factory, data):
        child = ChildProcess(identifier, parent_pid, q_factory.child())
        child.run(data=data)


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


More examples
=============

For a more complex example look at the test test_parent_full_duplex_communication_with_children_stress_test_ where
a full duplex communication between the parent and child processes occurs. Also a poison pill is sent to all children
when they are no longer needed.

.. _test_parent_full_duplex_communication_with_children_stress_test: https://github.com/d2gex/pymulproc/blob/master/tests/test_queue_communication.py
.. _PyPI: http://pypi.python.org/pypi/bleach

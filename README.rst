==========================================================
``pymulproc`` a tiny multiprocessing communication library
==========================================================

**pymulproc** is a tiny `stdlib-only` library to handle the communication between multiple processes without external
dependencies other than Python's standard library. It is based purely in the multiprocessing library and provides a
common interface for both PIPE and QUEUE communication.

===================
Pymulproc Protocol
===================
**pymulproc** uses a simple data structure as the basis of the communication as follows:

1. ``request``: a **required** string indicating the other peer what the operation is about.
2. ``sender pid``: an **required** integer indicating the pid of the processing sending the datagram.
3. ``recipient pid``: an **optional** integer indicating the pid of the process which this message is targeted to.
4. ``data``: an **optional** python data structure containing the information intended for the other peer.

In turn the requests sent in the data structure could be anything however **pymulproc** uses the following standards:

6. ``REQ_DO``: requests that indicates the other peer to do a task
7. ``REQ_FINISHED``: requests that indicates the other peer that the task has been done
8. ``REQ_DIE``: requests that indicates the other peer to stop and die as soon as possible. Practically a poison pill.


===================
Pymulproc API
===================
**pymulproc** offers a common API interface for the conversation exchange between a parent process and its children
for both PIPE and QUEUE communication as follows:

9.  ``send``: sends a message down the PIPE for 1:1 conversation or put a message in a JoinedQueue for 1:M, M:1 and M:M
    conversations
10. ``receive``: check if there is a message in the PIPE or at the front of the QUEUE for the process making such
    an enquiry. if the message is not intended for the process making the enquiry False is returned. In case the
    communication is done via QUEUEs, the method puts back the message in the queue so that the targeted process can
    later on fetch it.

Queue's communication add two more specific method: ``queue_empty`` to check if the queue is empty of tasks and
``queue_join`` to wait there until all the queue is empty.

Among the optional parameters of the  ``send`` method signature shown below, is worthwhile highlighting ``sender_pid``.
If provided, such integer is added to the message data structure as sender PID otherwise the process will add its own
PID.

The ``receive`` method takes as parameter another function that in turn takes the message extracted from the queue

.. code-block:: python

@abc.abstractmethod
    def send(self, request, sender_pid=None, recipient_pid=None, data=None):



===================
Pymulproc examples
===================

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


.. code-block:: python

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
            message = parent.receive(lambda x: True)
            counter += message[data_offset]

        # Ensure the queue is empty - no loose strings
        parent.queue_join()

        # Ensure we got the right data from children
        assert counter == val * len(child_processes)
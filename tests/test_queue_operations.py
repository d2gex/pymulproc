import pytest
import time
import queue
import multiprocessing

from pymulproc import errors
from pymulproc import mpq_protocol, factory
from unittest.mock import patch


def test_queue_api_params():
    '''Check that timeout and loops are taking in consideration in the .send method of the Communication Api
    for processes communicating via a queue as follows:

    1) timeout is respected by the put method of the queue
    2) num loops is respected by the put method of the queue. The loops are exhausted, an exception is thrown and
    the put method is called loops times
    '''

    # (1)
    queue_factory = factory.QueueCommunication()
    timeout = 20
    parent = queue_factory.parent(timeout=timeout)
    with patch.object(parent.conn, 'put') as mock_put:
        parent.send(mpq_protocol.REQ_TEST_PARENT)

    message = [mpq_protocol.REQ_TEST_PARENT, parent.pid, None, None]
    mock_put.assert_called_with(message, timeout=timeout)

    # (2)
    parent = queue_factory.parent(timeout=timeout, loops=20)
    assert parent.loops == 20
    mock_put.reset_mock()
    with patch.object(parent.conn, 'put', side_effect=queue.Full()) as mock_put:
        with pytest.raises(errors.QueuesCommunicationError):
            parent.send(mpq_protocol.REQ_TEST_PARENT)
    assert mock_put.call_count == parent.loops


def test_queue_operations():
    '''Test queue operations send and receive in isolation

    1) Check .receive return False when nothing is in the queue
    2) Check .send does add successfully elements in the queue when the queue isn't full
    3) check .receive remove the message from the queue when the next available message in the queue is for the client
    requesting it
    4) Check that .receive does not remove a message from the queue when the next available message in the queue is not
    for the the client that request it
    5) Check .send throws an exception when queue is full and not other element can be placed
    6) Check that .receive does count the task to be done properly for both when the passed function return True and
    False.
    '''

    put_timeout = 0.1
    queue_factory = factory.QueueCommunication()
    test_comm = queue_factory.parent(timeout=put_timeout)
    pid = multiprocessing.current_process().pid

    # (1)
    assert test_comm.conn.empty()
    message = test_comm.receive()
    assert message is False

    # (2)
    test_comm.send(mpq_protocol.REQ_FINISHED)
    time.sleep(0.1)
    assert not test_comm.conn.empty()

    # (3)
    message = test_comm.receive()
    assert message[mpq_protocol.S_PID_OFFSET - 1] == mpq_protocol.REQ_FINISHED
    time.sleep(0.1)
    assert test_comm.conn.empty()

    # (4)
    # --> Again we send a message to the queue
    recipient_pid = 1122
    test_comm.send(mpq_protocol.REQ_FINISHED, recipient_pid=recipient_pid)
    time.sleep(0.1)
    assert not test_comm.conn.empty()

    # --> Now we try to receive a message from the queue that isn't ours. The queue doesn't change
    message = test_comm.receive(func=lambda x: False)
    assert message is False
    time.sleep(0.1)
    assert not test_comm.conn.empty()

    # --> If the message as it was has been replaced it should be the same as the one before calling 'receive'.
    message = test_comm.receive()
    assert message[mpq_protocol.S_PID_OFFSET - 1] == mpq_protocol.REQ_FINISHED
    assert message[mpq_protocol.S_PID_OFFSET] == pid
    assert message[mpq_protocol.R_PID_OFFSET] == recipient_pid
    time.sleep(0.1)
    assert test_comm.conn.empty()

    # (5)
    max_size = 1  # max number of items that can be placed in the queue
    queue_factory = factory.QueueCommunication(max_size=max_size)
    test_comm = queue_factory.parent(timeout=put_timeout)
    test_comm.send(mpq_protocol.REQ_FINISHED)
    time.sleep(0.1)
    assert not test_comm.conn.empty()
    with pytest.raises(errors.QueuesCommunicationError):
        test_comm.send(mpq_protocol.REQ_FINISHED)

    # (6)
    # As we have been using .receive with lambda True and False, if the counting down of the elements being taken off
    # the queue was wrong this test would never end and block indefinitely
    test_comm.receive()
    time.sleep(0.1)
    assert test_comm.conn.empty()
    test_comm.conn.join()

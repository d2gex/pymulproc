import pytest
import time
import queue
import multiprocessing

from pymulproc import errors
from pymulproc import mpq_protocol, factory
from unittest.mock import patch


@pytest.fixture
def test_comm():
    queue_factory = factory.QueueCommunication()
    return queue_factory.parent(timeout=0.1)


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


def test_receive_nothing(test_comm):
    '''Check .receive return False when nothing is in the queue
    '''
    assert test_comm.conn.empty()
    message = test_comm.receive()
    assert message is False


def test_send_and_receive_successfully(test_comm):
    '''Check .send does add successfully elements in the queue when the queue isn't full and .receive remove the
    message from the queue when the next available message in the queue is for the client requesting it
    '''
    test_comm.send(mpq_protocol.REQ_FINISHED)
    time.sleep(0.1)
    assert not test_comm.conn.empty()

    message = test_comm.receive()
    assert message[mpq_protocol.S_PID_OFFSET - 1] == mpq_protocol.REQ_FINISHED
    time.sleep(0.1)
    assert test_comm.conn.empty()


def test_receive_do_not_remove_message_not_targeted_to_us(test_comm):
    '''Check that .receive does not remove a message from the queue when the next available message in the queue is not
    for the the client that request it
    '''

    pid = multiprocessing.current_process().pid
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


def test_send_thows_exception_queue_full():
    '''Check .send throws an exception when queue is full and not other element can be placed
    '''

    max_size = 1  # max number of items that can be placed in the queue
    queue_factory = factory.QueueCommunication(max_size=max_size)
    test_comm = queue_factory.parent(timeout=0.1)
    test_comm.send(mpq_protocol.REQ_FINISHED)
    time.sleep(0.1)
    assert not test_comm.conn.empty()
    with pytest.raises(errors.QueuesCommunicationError):
        test_comm.send(mpq_protocol.REQ_FINISHED)


def test_receive_count_tasks_done_properly(test_comm):
    '''Check that .receive does count the task to be done properly for both when the passed function return True and
    False.
    '''

    test_comm.send(mpq_protocol.REQ_FINISHED)
    time.sleep(0.1)

    test_comm.receive(func=lambda x: False)
    time.sleep(0.1)
    assert not test_comm.conn.empty()

    test_comm.receive(func=lambda x: True)
    time.sleep(0.1)
    assert test_comm.conn.empty()

    test_comm.conn.join()  # This would block indefinitely if any message was in the queue


def test_receive_blocking_when_block_false():
    '''Check that .receive blocks if nothing is in the queue and block flag is passed as false
    '''

    # (1) Sample with receive not blocking
    queue_factory = factory.QueueCommunication()
    parent = queue_factory.parent(timeout=0.1)
    message = parent.receive()
    # No blocking at receive() therefore receive will return False as no message was in the queue when we queried it
    assert message is False

    def add_message_to_queue_after_delay(q_factory):
        time.sleep(1)
        child = q_factory.child()
        child.send(mpq_protocol.REQ_FINISHED)

    # (2) Sample with receive blocking until something is ready in the queue
    child_process = multiprocessing.Process(target=add_message_to_queue_after_delay, args=(queue_factory, ))
    child_process.start()
    message = parent.receive(block=True)  # we block for a while
    parent.queue_join()  # if parent did not block in the queue and pick the message we would wait here indefinitely
    assert message is not False

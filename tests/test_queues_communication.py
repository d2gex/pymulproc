import pytest
import time

from pymulproc import errors
from pymulproc import mpq_protocol, factory


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
    test_comm = queue_factory.parent(put_timeout)

    # (1)
    assert test_comm.conn.empty()
    message = test_comm.receive(None)
    assert message is False

    # (2)
    test_comm.send(mpq_protocol.REQ_FINISHED)
    time.sleep(0.1)
    assert not test_comm.conn.empty()

    # (3)
    message = test_comm.receive(lambda x: True)
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
    message = test_comm.receive(lambda x: False)
    assert message is False
    time.sleep(0.1)
    assert not test_comm.conn.empty()

    # --> If the message as it was has been replaced it should be the same as the one before calling 'receive'.
    message = test_comm.receive(lambda x: True)
    assert message[mpq_protocol.S_PID_OFFSET - 1] == mpq_protocol.REQ_FINISHED
    assert message[mpq_protocol.D_PID_OFFSET] == recipient_pid
    time.sleep(0.1)
    assert test_comm.conn.empty()

    # (5)
    max_size = 1  # max number of items that can be placed in the queue
    queue_factory = factory.QueueCommunication(max_size)
    test_comm = queue_factory.parent(put_timeout)
    test_comm.send(mpq_protocol.REQ_FINISHED)
    time.sleep(0.1)
    assert not test_comm.conn.empty()
    with pytest.raises(errors.QueuesCommunicationError):
        test_comm.send(mpq_protocol.REQ_FINISHED)

    # (6)
    # As we have been using .receive with lambda True and False, if the counting down of the elements being taken off
    # the queue was wrong this test would never end and block indefinitely
    test_comm.receive(lambda x: True)
    time.sleep(0.1)
    assert test_comm.conn.empty()
    test_comm.conn.join()











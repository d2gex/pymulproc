import multiprocessing
import sys

from pymulproc import mpq_protocol, factory


def test_local_pipe_communication():
    '''Test that communication.multiprocessing.pipe.peers library works well as follows:

    1) Child can send a message
    2) Parent can receive such message
    3) Parent can send a message
    4) Child can receive it
    '''

    pipe_factory = factory.PipeCommunication()
    parent = pipe_factory.parent()

    def call_child(p_factory):
        child = p_factory.child()
        child.send(mpq_protocol.REQ_TEST_PARENT)
        stop = False
        loops = 10000
        # Avoiding hanging for ever
        while not stop and loops:
            loops -= 1
            stop = child.receive()
        # If we have not received anything or the wrong message from parent ==> Let the parent know that the job
        # was not complete and I exited with wrong
        try:
            assert len(stop) == 4
            assert stop[mpq_protocol.S_PID_OFFSET - 1] == mpq_protocol.REQ_TEST_CHILD
        except AssertionError:
            sys.exit(1)

    child_process = multiprocessing.Process(target=call_child, args=(pipe_factory,))
    child_process.start()

    stop = False
    loops = 10000
    while not stop and loops:
        loops -= 1
        stop = parent.receive()
    assert len(stop) == 4
    assert stop[mpq_protocol.S_PID_OFFSET - 1] == mpq_protocol.REQ_TEST_PARENT
    parent.send(mpq_protocol.REQ_TEST_CHILD)
    child_process.join()
    assert child_process.exitcode == 0

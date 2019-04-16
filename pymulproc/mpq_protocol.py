
PARENT_COMM_INTERFACE = 1
CHILD_COMM_INTERFACE = 2

REQ_DO = 'DO'  # Request sent by a 'peer' to the other 'peer' to indicate that a task should be done
REQ_FINISHED = 'FINISHED'  # Request sent by a 'peer' to indicate that it's done with whatever was to be done
REQ_DIE = 'DIE'  # Request sent by a 'peer' to the other 'peer' to indicate that it should terminate
REQ_TEST_PARENT = "I'M PARENT PROCESS"  # Requests to be ignored
REQ_TEST_CHILD = "I'M CHILD PROCESS"  # Requests to be ignored


S_PID_OFFSET = 1  # offset where the PID of the sender process is located in the message
R_PID_OFFSET = S_PID_OFFSET + 1  # offset where the PID of the recipient process is located in the message

# Message structure exchanged between two peers
# +------------------------+
# +    Request             + # (String)
# +------------------------+
# +------------------------+
# +    Sender Pid          + # (Integer)
# +------------------------+
# +------------------------+
# +    Recipient Pid     + # # (Integer)
# +------------------------+
# +------------------------+
# +    Data                + # (Any Python data structured)
# +------------------------+

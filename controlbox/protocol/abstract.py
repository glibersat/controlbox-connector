class ControlboxProtocol:
    """
    A Protocol maps low-level opcodes with higher level objects and allow
    encoding/decoding of messages.
    """
    decoder = None
    command_mapping = {}

import pytest

import Communication.ReaderCommunication as reader


@pytest.fixture(autouse=True)
def restore_reader_communication_globals():
    """Restores the module-level globals in ReaderCommunication after each test.

    Autouse because Communication.ReaderCommunication keeps its entire state in
    four module globals (connection_status, should_stop, mode, selected_command)
    rather than in an object. Any test that calls restart_communication() or
    set_communication_mode() mutates them for the rest of the pytest session.

    This matters most for should_stop: restart_communication() sets it to True
    and only the scanner loop resets it, at the very end of
    communicate_with_server(). Tests never run that loop, so without this
    fixture a single call to restart_communication() would poison every later
    test that inspects the mode or status globals.
    """
    saved = {
        "connection_status": reader.connection_status,
        "should_stop": reader.should_stop,
        "mode": reader.mode,
        "selected_command": reader.selected_command,
    }
    try:
        yield
    finally:
        for name, value in saved.items():
            setattr(reader, name, value)
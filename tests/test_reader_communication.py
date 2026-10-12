import pytest

import Communication.ReaderCommunication as reader


class TestStatus:
    def test_default_status(self):
        assert reader.get_status() == "Testaus"

    def test_update_status_changes_returned_value(self):
        reader.update_status("Harava on yhdistetty")
        assert reader.get_status() == "Harava on yhdistetty"

    def test_status_round_trips(self):
        for status in ("Yritetään muodostaa yhteyttä", "Harava on yhdistetty", "OK"):
            reader.update_status(status)
            assert reader.get_status() == status


class TestCommunicationMode:
    @pytest.mark.parametrize("mode", ["scan", "AFI"])
    def test_accepts_valid_modes(self, mode):
        reader.set_communication_mode(mode)
        assert reader.mode == mode

    @pytest.mark.parametrize("mode", ["bogus", "", "SCAN", None, 1])
    def test_rejects_invalid_modes(self, mode):
        with pytest.raises(ValueError):
            reader.set_communication_mode(mode)

    def test_rejection_leaves_mode_unchanged(self):
        reader.set_communication_mode("scan")
        with pytest.raises(ValueError):
            reader.set_communication_mode("bogus")
        assert reader.mode == "scan"

    def test_is_case_sensitive(self):
        # Documented quirk: only the exact strings 'scan' and 'AFI' are valid.
        # 'afi' and 'Scan' raise ValueError.
        with pytest.raises(ValueError):
            reader.set_communication_mode("afi")


class TestSelectedCommand:
    def test_accepts_bytes(self):
        reader.set_selected_command(b"\x01\x02")
        assert reader.selected_command == b"\x01\x02"

    def test_accepts_empty_bytes(self):
        reader.set_selected_command(b"")
        assert reader.selected_command == b""

    @pytest.mark.parametrize("command", ["\x01\x02", None, 42, ["\x01"], bytearray(b"\x01")])
    def test_rejects_non_bytes(self, command):
        with pytest.raises(ValueError):
            reader.set_selected_command(command)

    def test_rejection_leaves_command_unchanged(self):
        reader.set_selected_command(b"\xaa")
        with pytest.raises(ValueError):
            reader.set_selected_command("nope")
        assert reader.selected_command == b"\xaa"


class TestRestartCommunication:
    def test_sets_should_stop(self):
        reader.restart_communication()
        assert reader.should_stop is True

    def test_repeat_calls_are_idempotent(self):
        reader.restart_communication()
        reader.restart_communication()
        assert reader.should_stop is True


class TestCommandConstants:
    def test_read_command_starts_with_read_opcode(self):
        assert reader.read_command[4] == 0x22

    def test_clear_command_starts_with_clear_opcode(self):
        assert reader.clear_command[4] == 0x32

    def test_afi_commands_differ(self):
        assert reader.enable_afi_command != reader.disable_afi_command

    def test_afi_commands_are_bytes(self):
        assert isinstance(reader.enable_afi_command, bytes)
        assert isinstance(reader.disable_afi_command, bytes)


class TestGlobalIsolation:
    def test_fixture_restores_should_stop(self, request):
        # This test mutates should_stop via restart_communication. The autouse
        # fixture in conftest restores it, so the ordering here is safe: it runs
        # while should_stop is True, then the fixture resets it for later tests.
        reader.restart_communication()
        assert reader.should_stop is True

    def test_should_stop_is_restored_between_tests(self):
        # If the fixture were missing, should_stop would still be True from the
        # previous test. This asserts the isolation works.
        assert reader.should_stop is False
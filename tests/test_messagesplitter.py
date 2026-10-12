import pytest

from DataHandling.Messagesplitter import recursive_split_hex_string, split_and_process


# Sample from the module's __main__ block: two tag notifications in one stream.
SAMPLE = (
    "0200450022000a0002001d000604d1000dd9db0f3d6c593362c18376cc3f0201a805011067"
    "02001d000604d1000dd9db0f3d6c593362c18376cc3f0201a8050110670289ed"
)

SINGLE_MESSAGE = (
    "04d1000dd9db0f3d6c593362c18376cc3f0201a80501106702001d0006"
)


class TestRecursiveSplit:
    def test_splits_on_marker_boundaries(self):
        assert recursive_split_hex_string(SAMPLE) == [
            "04d1000dd9db0f3d6c593362c18376cc3f0201a80501106702001d0006",
            "04d1000dd9db0f3d6c593362c18376cc3f0201a8050110670289ed",
        ]

    def test_markers_are_kept_at_start_of_each_message(self):
        for message in recursive_split_hex_string(SAMPLE):
            assert message.startswith("04d1")

    def test_bytes_before_first_marker_are_discarded(self):
        # The stream begins with a scanner header; only tag memory blocks are
        # kept, so the leading bytes are dropped.
        assert recursive_split_hex_string("aaaa" + SINGLE_MESSAGE) == [SINGLE_MESSAGE]

    def test_lowercases_input(self):
        assert recursive_split_hex_string(SAMPLE.upper()) == recursive_split_hex_string(SAMPLE)

    def test_input_without_markers_yields_nothing(self):
        assert recursive_split_hex_string("deadbeef" * 10) == []

    def test_input_shorter_than_minimum_yields_nothing(self):
        # 40 characters is the minimum message length.
        assert recursive_split_hex_string("0411") == []

    def test_empty_input_yields_nothing(self):
        assert recursive_split_hex_string("") == []


class TestSplitAndProcess:
    def test_returns_two_messages_for_two_tags(self):
        assert len(split_and_process(SAMPLE)) == 2

    def test_message_lengths(self):
        assert [len(m) for m in split_and_process(SAMPLE)] == [58, 54]

    def test_every_message_meets_minimum_length(self):
        assert all(len(m) >= 40 for m in split_and_process(SAMPLE))

    def test_single_tag_yields_single_message(self):
        assert split_and_process(SINGLE_MESSAGE) == [SINGLE_MESSAGE]

    def test_input_without_markers_yields_empty_list(self):
        assert split_and_process("deadbeef" * 10) == []

    def test_empty_input_yields_empty_list(self):
        assert split_and_process("") == []

    def test_uppercase_input_matches_lowercase(self):
        assert split_and_process(SAMPLE.upper()) == split_and_process(SAMPLE)

    def test_lowercases_output(self):
        for message in split_and_process(SAMPLE.upper()):
            assert message == message.lower()

    @pytest.mark.parametrize(
        "marker",
        ["0411", "04c1", "0441", "0400000000000000", "0491", "04a1", "0421", "04d1", "0451"],
    )
    def test_recognises_every_memory_block_prefix(self, marker):
        # These are the nine prefixes the app routes to different decoders in
        # main.py's fetch_data.
        assert split_and_process(marker + "ab" * 25) == [marker + "ab" * 25]
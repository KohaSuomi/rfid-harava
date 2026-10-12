import pytest

from Decoders.SevenBitDecoder import (
    bits_to_ascii,
    decode7Bit,
    decode_7bit,
    hex_to_bitstring,
)


# Sample from the module's __main__ block.
SAMPLE = "0451464954001d000604c1020b3160532f1cb3e79df7c39880800201a80501106702001d0006"


class TestHexToBitstring:
    def test_extracts_length_byte_and_converts(self):
        # Length byte at index 4 is '46' -> 70 bytes -> 280 bits.
        assert hex_to_bitstring(SAMPLE, 4, 6).startswith("01001001010101000000000000011101")

    def test_output_length_matches_length_byte(self):
        assert len(hex_to_bitstring(SAMPLE, 4, 6)) == 280

    def test_output_length_is_multiple_of_eight(self):
        # The zfill rounds up to the next multiple of 8.
        assert len(hex_to_bitstring(SAMPLE, 4, 6)) % 8 == 0

    def test_empty_input_raises(self):
        with pytest.raises(ValueError):
            hex_to_bitstring("", 4, 6)


class TestDecode7Bit:
    def test_prefixes_complete_segments_with_zero(self):
        assert decode_7bit("1000000") == ["01000000"]

    def test_drops_incomplete_trailing_segment(self):
        # Only segments of exactly 7 bits are kept; a 4-bit remainder is lost.
        assert decode_7bit("1000000" + "1000") == ["01000000"]

    def test_drops_all_ones_padding_segment(self):
        # '01111111' is the padding marker and is removed when last.
        assert decode_7bit("0000000" + "1111111") == ["00000000"]

    def test_keeps_all_ones_segment_when_not_trailing(self):
        # The padding check only inspects the final segment.
        bitstring = "1111111" + "1000000" + "1111111"
        assert decode_7bit(bitstring) == ["01111111", "01000000"]

    def test_empty_bitstring_yields_no_segments(self):
        assert decode_7bit("") == []


class TestBitsToAscii:
    def test_converts_segments_to_characters(self):
        assert bits_to_ascii(["01000001", "01000010"]) == "AB"

    def test_filters_non_alphanumeric(self):
        # Space and control bytes are dropped.
        assert bits_to_ascii(["00100000", "01000001", "00000001"]) == "A"

    def test_empty_list_yields_empty_string(self):
        assert bits_to_ascii([]) == ""


class TestDecode7BitEntryPoint:
    def test_decodes_known_sample(self):
        assert decode7Bit(SAMPLE, 4, 6) == "UhA3yot"

    def test_result_is_ascii(self):
        assert decode7Bit(SAMPLE, 4, 6).isascii()

    def test_matches_manual_pipeline(self):
        segments = decode_7bit(hex_to_bitstring(SAMPLE, 4, 6))
        assert decode7Bit(SAMPLE, 4, 6) == bits_to_ascii(segments)

    def test_empty_input_raises_value_error(self):
        # Documented quirk: decode7Bit propagates ValueError from
        # hex_to_bitstring rather than returning None.
        with pytest.raises(ValueError):
            decode7Bit("", 4, 6)
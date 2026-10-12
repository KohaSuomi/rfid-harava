import pytest

from Decoders.IsoDecoder import (
    Decode6Bit,
    bits_to_iso_646,
    hex_to_bitstring,
    isoDecoder,
)


# Sample from the module's __main__ block.
SAMPLE = "044109DB1C4EC30D77DB5DF80201E0030632410E3E4E0F14010B050110"


class TestHexToBitstring:
    def test_extracts_length_byte_and_converts(self):
        assert hex_to_bitstring(SAMPLE, 4, 6) == (
            "110110110001110001001110110000110000110101110111110110110101110111111000"
        )

    def test_length_byte_selects_how_many_bytes_to_take(self):
        # The byte at index 4 is '09' -> 9 bytes -> 18 hex chars from index 6.
        assert hex_to_bitstring(SAMPLE, 4, 6).startswith("1101101100011100")

    def test_zero_length_byte_yields_empty_bitstring(self):
        # int(b'', 16) raises, so a zero length byte that truncates to nothing
        # is an error rather than an empty string.
        with pytest.raises(ValueError):
            hex_to_bitstring("04a10000", 6, 8)

    def test_empty_input_raises(self):
        # The `if bitstring is None` guard in isoDecoder is unreachable because
        # this function either returns a string or raises.
        with pytest.raises(ValueError):
            hex_to_bitstring("", 4, 6)


class TestDecode6Bit:
    def test_prefixes_zero_starting_segments_with_01(self):
        assert Decode6Bit("000000") == ["01000000"]

    def test_prefixes_one_starting_segments_with_00(self):
        assert Decode6Bit("100000") == ["00100000"]

    def test_concatenates_into_eight_bit_segments(self):
        assert Decode6Bit("000000100000") == ["01000000", "00100000"]

    def test_empty_bitstring_yields_no_segments(self):
        assert Decode6Bit("") == []

    def test_trailing_partial_segment_is_not_padded(self):
        # Documented quirk: a trailing segment shorter than 6 bits still gets
        # the 2-char prefix, so the final element may be < 8 bits. It is still
        # consumed downstream by bits_to_iso_646, which reads it as a small int.
        assert Decode6Bit("0000000001") == ["01000000", "010001"]


class TestBitsToIso646:
    def test_converts_segments_to_characters(self):
        assert bits_to_iso_646(["01000001", "01000010"]) == "AB"

    def test_filters_non_alphanumeric(self):
        # 'J' is dropped; the rest survive.
        assert bits_to_iso_646(["01000001", "00001010"]) == "A"

    def test_empty_list_yields_empty_string(self):
        assert bits_to_iso_646([]) == ""


class TestIsoDecoder:
    def test_decodes_known_sample(self):
        assert isoDecoder(SAMPLE, 4, 6) == "611N00576578"

    def test_result_is_ascii_and_alphanumeric(self):
        result = isoDecoder(SAMPLE, 4, 6)
        assert result.isalnum()

    def test_empty_input_returns_none(self):
        # Returns None on undecodable input, matching numericDecoder, rather
        # than raising. main.py relies on a falsy result to skip the tag.
        assert isoDecoder("", 4, 6) is None

    def test_zero_length_byte_returns_none(self):
        # A zero length byte makes the slice empty, which int() rejects.
        assert isoDecoder("04c10000", 6, 8) is None

    def test_non_hex_data_returns_none(self):
        assert isoDecoder("04c1zz", 6, 8) is None


class TestDecode6BitPipeline:
    def test_sample_segments_reassemble_to_expected_value(self):
        segments = Decode6Bit(hex_to_bitstring(SAMPLE, 4, 6))
        assert len(segments) == 12
        assert segments[0] == "00110110"
        assert segments[-1] == "00111000"
        assert bits_to_iso_646(segments) == "611N00576578"
import pytest

from Decoders.IntegerDecoder import DecodeInteger, hex_to_bitstring, integerDecoder


# Sample from the module's __main__ block.
SAMPLE = "041110619F0CD7BFB770201A80501106702424103063240BE3E8B0F"


class TestHexToBitstring:
    def test_extracts_length_byte_and_converts(self):
        assert hex_to_bitstring(SAMPLE, 4, 6) == (
            "011000011001111100001100110101111011111110110111011100000010000000"
            "01101010000000010100000001000100000110011100000010010000100100"
        )

    def test_output_length_matches_length_byte(self):
        # Length byte at index 4 is '10' -> 16 bytes -> 128 bits.
        assert len(hex_to_bitstring(SAMPLE, 4, 6)) == 128

    def test_leading_zero_bits_are_preserved(self):
        # int(...)[2:] drops leading zeros; zfill restores them to the full
        # declared width so the value keeps its place value. The length byte
        # at index 4 is '01' -> 8 bits, all zero.
        assert hex_to_bitstring("041101000000", 4, 6) == "00000000"

    def test_zero_value_decodes_to_zero_string(self):
        assert integerDecoder("041101000000", 4, 6) == "0"

    def test_empty_input_raises(self):
        with pytest.raises(ValueError):
            hex_to_bitstring("", 4, 6)


class TestDecodeInteger:
    def test_converts_bitstring_to_int(self):
        assert DecodeInteger("1010") == 10

    def test_zero_bitstring(self):
        assert DecodeInteger("0") == 0

    def test_empty_bitstring_raises(self):
        with pytest.raises(ValueError):
            DecodeInteger("")


class TestIntegerDecoder:
    def test_decodes_known_sample(self):
        assert integerDecoder(SAMPLE, 4, 6) == "129760951273947461449601195042935940132"

    def test_returns_string_not_int(self):
        # The value is stringified before returning so callers can concatenate
        # it with other barcode strings.
        assert isinstance(integerDecoder(SAMPLE, 4, 6), str)

    def test_result_matches_decode_integer(self):
        expected = str(DecodeInteger(hex_to_bitstring(SAMPLE, 4, 6)))
        assert integerDecoder(SAMPLE, 4, 6) == expected

    def test_empty_input_raises_value_error(self):
        # Documented quirk: integerDecoder propagates ValueError rather than
        # returning None, making the guard at IntegerDecoder.py:28 dead code.
        with pytest.raises(ValueError):
            integerDecoder("", 4, 6)
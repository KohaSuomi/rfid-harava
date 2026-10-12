import pytest

from Decoders.NumericDecoder import hex_to_decimal, numericDecoder


# Sample from the module's __main__ block.
SAMPLE = "04A1000607800116607F0201E0030632408E05CB7F14010B050110"


class TestHexToDecimal:
    def test_converts_known_sample(self):
        assert hex_to_decimal(SAMPLE, 6, 8) == "0780011660715"

    def test_reads_four_bits_at_a_time(self):
        # The length byte at index 6 is '06' -> 6 bytes -> 48 bits -> 12
        # nibbles. The rendered string is 13 characters, not 12, because the
        # final nibble is 15 and renders as two characters.
        assert hex_to_decimal(SAMPLE, 6, 8) == "0780011660715"
        assert len(hex_to_decimal(SAMPLE, 6, 8)) == 13

    def test_digits_can_exceed_nine(self):
        # Each nibble maps to 0-15, so 'f' renders as "15" rather than being
        # split into two digits. This is why the output is longer than the
        # input nibble count.
        assert hex_to_decimal("00010fff", 2, 4) == "015"

    def test_all_nibbles_render_as_fifteen(self):
        assert hex_to_decimal("0002ffff", 2, 4) == "15151515"

    def test_zero_pads_to_declared_byte_length(self):
        # bin(0) is the single character '0'; zfill expands it to the 8 bits
        # the length byte declared. Those 8 bits yield two four-bit groups, so
        # the result is '00' rather than the '0' bin(0) would have produced.
        assert hex_to_decimal("00010000", 2, 4) == "00"


class TestNumericDecoder:
    def test_decodes_known_sample(self):
        assert numericDecoder(SAMPLE, 6, 8) == "0780011660715"

    def test_returns_only_digits(self):
        assert numericDecoder(SAMPLE, 6, 8).isdigit()

    def test_empty_input_returns_none(self):
        # Unlike the other decoders, numericDecoder catches ValueError and
        # returns None instead of propagating it.
        assert numericDecoder("", 6, 8) is None

    def test_zero_length_byte_returns_none(self):
        # A zero length byte makes the slice empty, which int() rejects.
        assert numericDecoder("04a10000", 6, 8) is None

    def test_non_hex_data_returns_none(self):
        assert numericDecoder("04a10006zzzzzzzz", 6, 8) is None
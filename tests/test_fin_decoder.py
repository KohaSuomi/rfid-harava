import pytest

from Decoders.FINDecoder import FINDecoder


# Sample from the module's __main__ block.
VALID_HEX = "1101003835334e3036323430363030000000003850464954001d0006"


class TestIsValidHex:
    @pytest.mark.parametrize(
        "hex_string",
        [
            "1101003835334e3036323430363030000000003850464954001d0006",
            "04110100",
            "00",
        ],
    )
    def test_accepts_even_length_hex(self, hex_string):
        assert FINDecoder.is_valid_hex(hex_string) is True

    @pytest.mark.parametrize("hex_string", ["110100383", "110"])
    def test_rejects_odd_length(self, hex_string):
        # Length is checked only after the character check passes; odd-length
        # input with valid hex characters is rejected by the modulo test.
        assert FINDecoder.is_valid_hex(hex_string) is False

    @pytest.mark.parametrize("hex_string", ["zz1101", "11 00", "110x00"])
    def test_rejects_non_hex_characters(self, hex_string):
        assert FINDecoder.is_valid_hex(hex_string) is False

    @pytest.mark.parametrize("hex_string", ["DEADBEEF", "abcdef"])
    def test_accepts_uppercase(self, hex_string):
        # string.hexdigits covers 0-9 a-f A-F.
        assert FINDecoder.is_valid_hex(hex_string) is True

    def test_empty_string_is_reported_valid(self):
        # Documented quirk, not the intended behaviour: all() over an empty
        # string is vacuously True and len('') % 2 == 0, so '' passes
        # validation. This means FINDecoder('') constructs successfully with
        # empty data instead of being rejected as malformed input.
        assert FINDecoder.is_valid_hex("") is True


class TestConstruction:
    def test_valid_hex_populates_data(self):
        decoder = FINDecoder(VALID_HEX)
        assert decoder.data is not None
        assert decoder.index == 0

    def test_invalid_hex_leaves_data_none(self, capsys):
        decoder = FINDecoder("zz1101")
        assert decoder.data is None
        assert capsys.readouterr().out.startswith("Skipping invalid hex string")

    def test_odd_length_hex_leaves_data_none(self):
        assert FINDecoder("110100383").data is None


class TestReadBytes:
    def test_reads_sequentially_and_advances_index(self):
        decoder = FINDecoder(VALID_HEX)
        assert decoder.read_bytes(1) == b"\x11"
        assert decoder.index == 1
        assert decoder.read_bytes(1) == b"\x01"
        assert decoder.index == 2

    def test_read_past_end_returns_short_slice(self):
        decoder = FINDecoder("00ff")
        assert decoder.read_bytes(5) == b"\x00\xff"

    def test_read_on_invalid_decoder_returns_none(self):
        decoder = FINDecoder("zz")
        assert decoder.data is None
        assert decoder.read_bytes(1) is None


class TestNumericDecoding:
    def test_decode_numeric_reads_big_endian(self):
        decoder = FINDecoder("0102")
        assert decoder.decode_numeric(2) == 0x0102

    def test_decode_crc_reads_two_bytes(self):
        decoder = FINDecoder("abcd")
        assert decoder.decode_crc() == 0xABCD

    def test_decode_crc_on_invalid_decoder_returns_zero(self):
        decoder = FINDecoder("zz")
        assert decoder.decode_crc() == 0


class TestUtf8Decoding:
    def test_decodes_ascii(self):
        assert FINDecoder(VALID_HEX).decode_utf8_string(b"853N06240600") == "853N06240600"

    def test_none_returns_empty_string(self):
        assert FINDecoder(VALID_HEX).decode_utf8_string(None) == ""

    def test_non_ascii_bytes_are_ignored(self):
        # decode('ascii', errors='ignore') drops non-ASCII bytes rather than
        # raising, so an item ID with stray high bytes decodes lossy.
        assert FINDecoder(VALID_HEX).decode_utf8_string(b"ab\xffcd") == "abcd"


class TestVariableLengthString:
    def test_stops_at_null_byte(self):
        decoder = FINDecoder("4142430044")
        assert decoder.decode_variable_length_string(16) == "ABC"
        assert decoder.index == 4

    def test_respects_max_length(self):
        decoder = FINDecoder("4142434445")
        assert decoder.decode_variable_length_string(2) == "AB"

    def test_skips_trailing_nulls(self):
        decoder = FINDecoder("41000042")
        # Reads 'A', hits the null, then skips remaining null padding so the
        # next read starts at 'B'.
        assert decoder.decode_variable_length_string(16) == "A"
        assert decoder.read_bytes(1) == b"B"

    def test_invalid_decoder_returns_empty_string(self):
        decoder = FINDecoder("zz")
        assert decoder.decode_variable_length_string(16) == ""


class TestDecodeDataBlock:
    def test_returns_readable_summary(self):
        decoder = FINDecoder("0201020a")
        summary = decoder.decode_data_block()
        assert summary == "Block Length: 2, Block ID: 258, Checksum: 10"

    def test_reads_fields_in_order(self):
        decoder = FINDecoder("0201020a")
        decoder.decode_data_block()
        # Length is 1 byte, ID is 2 bytes, checksum is 1 byte.
        assert decoder.index == 4


class TestDecode:
    def test_returns_primary_item_id_string(self):
        assert FINDecoder(VALID_HEX).decode() == "853N06240600"

    def test_ignores_hex_case(self):
        uppercase = VALID_HEX.upper()
        assert FINDecoder(uppercase).decode() == "853N06240600"

    def test_invalid_hex_returns_empty_string(self):
        # Invalid input used to return a 3-tuple here while the success path
        # returned a bare string. main.py calls .upper() on the result
        # unconditionally, so that raised AttributeError and took down the
        # scan. Every path now returns a str.
        result = FINDecoder("zz1101").decode()
        assert result == ""

    @pytest.mark.parametrize(
        "hex_string",
        [
            "1101003835334e3036323430363030000000003850464954001d0006",
            "zz1101",
            "110100383",
            "",
            "00",
            "110100",
        ],
    )
    def test_always_returns_a_string(self, hex_string):
        # Regression guard for the return-type inconsistency. Any path that
        # returns a non-str breaks the caller's .upper() call.
        assert isinstance(FINDecoder(hex_string).decode(), str)

    @pytest.mark.parametrize("hex_string", ["zz1101", "110100383", ""])
    def test_result_is_safe_to_uppercase(self, hex_string):
        # Mirrors what main.py does with the decoded barcode.
        assert FINDecoder(hex_string).decode().upper() == ""

    def test_empty_input_decodes_to_empty_string(self):
        # Follows from is_valid_hex("") being True: data is b"", so read_bytes(3)
        # returns b"" (not None) and the early return is not taken.
        assert FINDecoder("").decode() == ""


class TestSampleInputs:
    @pytest.mark.parametrize(
        "hex_string, expected",
        [
            ("1101003835334e3036323430363030000000003850464954001d0006", "853N06240600"),
        ],
    )
    def test_known_sample(self, hex_string, expected):
        assert FINDecoder(hex_string).decode() == expected
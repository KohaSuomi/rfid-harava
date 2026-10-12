"""Contract shared by all five tag decoders.

These all funnel into the same call sites in main.py's fetch_data, which
uppercase the result and append it to the batch sent to Koha. Divergence
between them is what produced AttributeError on None and empty barcodes
reaching the report API, so the shared contract is asserted here rather
than five times over.
"""

import pytest

from Decoders.IntegerDecoder import integerDecoder
from Decoders.IsoDecoder import isoDecoder
from Decoders.NumericDecoder import numericDecoder
from Decoders.SevenBitDecoder import decode7Bit
from Decoders.FINDecoder import FINDecoder


# Every decoder entry point, with the length_byte/start_index main.py uses
# for the unlocked variant of its model.
DECODERS = [
    ("FINDecoder", lambda hex_string: FINDecoder(hex_string[2:]).decode()),
    ("isoDecoder", lambda hex_string: isoDecoder(hex_string, 4, 6)),
    ("integerDecoder", lambda hex_string: integerDecoder(hex_string, 4, 6)),
    ("numericDecoder", lambda hex_string: numericDecoder(hex_string, 6, 8)),
    ("decode7Bit", lambda hex_string: decode7Bit(hex_string, 4, 6)),
]

DECODER_IDS = [name for name, _ in DECODERS]


# Payloads every decoder must reject rather than raise on.
UNREADABLE = [
    "",
    "zz",
    "00",
    "00000000",
    "zzzzzzzz",
]


@pytest.mark.parametrize("name, decode", DECODERS, ids=DECODER_IDS)
@pytest.mark.parametrize("payload", UNREADABLE)
def test_unreadable_payload_never_raises(name, decode, payload):
    """A payload the decoder cannot parse must not raise.

    An exception escaping a decoder used to reach main.py's sys.excepthook
    and exit the app. Returning a falsy value lets the caller skip the tag.
    """
    try:
        result = decode(payload)
    except Exception as exc:  # noqa: BLE001 - the point is that nothing escapes
        pytest.fail(f"{name} raised {type(exc).__name__} on {payload!r}: {exc}")


@pytest.mark.parametrize("name, decode", DECODERS, ids=DECODER_IDS)
@pytest.mark.parametrize("payload", UNREADABLE)
def test_unreadable_payload_yields_nothing_usable(name, decode, payload):
    """An unreadable payload decodes to None or an empty string.

    Either is falsy, so main.py's `if barcode:` guard skips the tag. Any
    other value would either reach Koha as a junk barcode or blow up on the
    `.upper()` call that follows.
    """
    result = decode(payload)
    assert result is None or result == "", f"{name} returned {result!r}"


@pytest.mark.parametrize("name, decode", DECODERS, ids=DECODER_IDS)
@pytest.mark.parametrize("payload", UNREADABLE)
def test_decoder_result_survives_main_pys_uppercase(name, decode, payload):
    """Replays what main.py does with a decoded barcode.

    main.py calls .upper() before appending. FINDecoder used to return a
    3-tuple, which raised AttributeError right here. A None result is
    filtered out by the `if barcode:` guard, so .upper() is not reached.
    """
    result = decode(payload)
    if result is None:
        return
    assert isinstance(result.upper(), str)
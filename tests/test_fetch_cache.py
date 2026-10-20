"""Tests for the barcode fetch cache rules used by main.fetch_data.

Stdlib only, like the rest of this suite: main.py needs PySide6, so the TTL
and criteria-invalidation logic lives in DataHandling.FetchCache instead.
"""

import DataHandling.FetchCache as FetchCache


# --- take(): TTL suppression and queue draining ---------------------------


def test_uncached_barcode_is_fresh_and_stamped():
    fetched_at = {}
    fresh, cached = FetchCache.take(['A'], fetched_at, now=100.0, ttl=60)

    assert fresh == ['A']
    assert cached == []
    assert fetched_at == {'A': 100.0}


def test_cached_barcode_is_not_fetched_and_is_reported_for_flashing():
    fetched_at = {'A': 100.0}
    fresh, cached = FetchCache.take(['A'], fetched_at, now=130.0, ttl=60)

    assert fresh == []
    assert cached == ['A']
    # A suppressed barcode keeps its original stamp.
    assert fetched_at == {'A': 100.0}


def test_ttl_expiry_makes_barcode_fresh_again():
    fetched_at = {'A': 100.0}
    fresh, cached = FetchCache.take(['A'], fetched_at, now=160.0, ttl=60)

    assert fresh == ['A']
    assert cached == []
    assert fetched_at == {'A': 160.0}


def test_zero_ttl_disables_suppression():
    fetched_at = {'A': 100.0}
    fresh, cached = FetchCache.take(['A'], fetched_at, now=100.0, ttl=0)

    assert fresh == ['A']
    assert cached == []


def test_duplicates_within_one_tick_collapse_to_one_fetch():
    fetched_at = {}
    fresh, cached = FetchCache.take(['A', 'A', 'A'], fetched_at, now=100.0, ttl=60)

    assert fresh == ['A']
    assert cached == ['A', 'A']
    assert fetched_at == {'A': 100.0}


def test_mixed_fresh_and_cached_are_split_preserving_order():
    fetched_at = {'B': 100.0}
    fresh, cached = FetchCache.take(
        ['A', 'B', 'C'], fetched_at, now=110.0, ttl=60)

    assert fresh == ['A', 'C']
    assert cached == ['B']
    assert fetched_at == {'A': 110.0, 'B': 100.0, 'C': 110.0}


def test_take_drains_the_queue_in_place():
    # Regression: leaving cached barcodes in the queue made the reader's
    # re-reports re-flash the row on every tick for the whole TTL.
    fetched_at = {'A': 100.0}
    barcodes = ['A']

    FetchCache.take(barcodes, fetched_at, now=110.0, ttl=60)

    assert barcodes == []


def test_take_drains_the_queue_even_when_everything_is_fresh():
    fetched_at = {}
    barcodes = ['A', 'B']

    FetchCache.take(barcodes, fetched_at, now=100.0, ttl=60)

    assert barcodes == []


def test_take_drains_the_queue_when_empty():
    fetched_at = {}
    barcodes = []

    fresh, cached = FetchCache.take(barcodes, fetched_at, now=100.0, ttl=60)

    assert (fresh, cached, barcodes) == ([], [], [])


# --- settings_changed(): criteria-change invalidation ---------------------


def test_settings_changed_when_mtime_differs():
    assert FetchCache.settings_changed(200.0, 100.0) is True


def test_settings_unchanged_when_mtime_is_the_same():
    assert FetchCache.settings_changed(100.0, 100.0) is False


def test_settings_change_from_missing_file_is_detected():
    assert FetchCache.settings_changed(100.0, None) is True
    assert FetchCache.settings_changed(None, 100.0) is True


def test_settings_missing_on_both_checks_is_not_a_change():
    assert FetchCache.settings_changed(None, None) is False


# --- sweep(): bounded cache growth ----------------------------------------


def test_sweep_drops_expired_entries_when_over_limit():
    fetched_at = {'A': 100.0, 'B': 190.0}

    FetchCache.sweep(fetched_at, now=200.0, ttl=60, limit=1)

    assert fetched_at == {'B': 190.0}


def test_sweep_leaves_cache_alone_under_limit():
    fetched_at = {'A': 100.0}

    FetchCache.sweep(fetched_at, now=10000.0, ttl=60, limit=5000)

    assert fetched_at == {'A': 100.0}

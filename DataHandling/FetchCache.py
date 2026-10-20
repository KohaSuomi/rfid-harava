"""Barcode fetch cache rules.

These live here rather than inline in main.fetch_data so the TTL suppression
and the search-criteria invalidation can be tested without importing PySide6.
main.py keeps the state (the barcode -> timestamp map) and calls these.
"""


def take(barcodes, fetched_at, now, ttl):
    """Split one tick's barcodes into fresh and cached, then drain the queue.

    A barcode fetched less than ``ttl`` seconds ago is returned in ``cached``
    instead of being requested again. Every other barcode is stamped with
    ``now`` and returned in ``fresh``; stamping inside the loop collapses
    duplicates the reader produced within the same tick.

    ``barcodes`` is emptied in place. That is the point of the drain: the
    reader re-reports every tag in its field several times a second, so a
    cached barcode left in the queue would be re-flashed on every later tick
    for the rest of the TTL instead of only while the tag is in the field.
    """
    fresh = []
    cached = []
    for barcode in barcodes:
        last_fetch = fetched_at.get(barcode)
        if last_fetch is not None and now - last_fetch < ttl:
            cached.append(barcode)
            continue
        fetched_at[barcode] = now
        fresh.append(barcode)
    barcodes.clear()
    return fresh, cached


def settings_changed(current_mtime, previous_mtime):
    """True when the criteria file changed since the last check.

    ``None`` means the file was missing. Missing on both checks is not a
    change; the file appearing or disappearing is.
    """
    return current_mtime != previous_mtime


def sweep(fetched_at, now, ttl, limit=5000):
    """Drop expired entries once the cache grows past ``limit``."""
    if len(fetched_at) > limit:
        for key in [k for k, t in fetched_at.items() if now - t >= ttl]:
            del fetched_at[key]

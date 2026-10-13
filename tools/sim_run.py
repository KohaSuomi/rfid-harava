"""Run the real app with NO reader at all, simulating scans directly.

The TTL dedup lives after decoding, in fetch_data's batching block. This
appends barcodes to main.barcodes on a timer - exactly what the reader loop
does by the time decoding is finished - so the dedup and flashing can be
exercised without any hardware, socket, or second machine.

Enable with SCAN_INTERVAL env var (seconds between simulated reads).
Enable batch mode with SCAN_TAGS=N (N barcodes per simulated read).
"""

import json
import os
import sys
import threading
import time

REPO = '/home/jraisa/rfid-harava'
sys.path.insert(0, REPO)

HERE = os.path.dirname(os.path.abspath(__file__))
# Written to the scratch work dir, not next to this file, so a run never
# leaves artifacts in the repo. tools/sim_run.py is launched by
# tools/ttldedup_check.py with HARAVA_WORK set.
STATS = os.path.join(os.environ.get('HARAVA_WORK', os.environ.get('TMPDIR', '/tmp')),
                     'simstats.json')
BARCODE = 'LVASK123100760'

import GUI.UI as UI

_orig_flash_barcode = UI.MainWindow.flash_barcode
stats = {'flashes': 0, 'scans': 0}
_lock = threading.Lock()


def _counting_flash_barcode(self, barcode):
    with _lock:
        stats['flashes'] += 1
        _write()
    return _orig_flash_barcode(self, barcode)


UI.MainWindow.flash_barcode = _counting_flash_barcode


def _write():
    tmp = STATS + '.tmp'
    with open(tmp, 'w') as fh:
        json.dump(stats, fh)
    os.replace(tmp, STATS)


def _simulate():
    interval = float(os.environ.get('SCAN_INTERVAL', '0.25'))
    tags = int(os.environ.get('SCAN_TAGS', '1'))
    while True:
        time.sleep(interval)
        import main
        with _lock:
            for _ in range(tags):
                main.barcodes.append(BARCODE)
            stats['scans'] += tags
            _write()


if __name__ == '__main__':
    _write()
    threading.Thread(target=_simulate, daemon=True).start()
    import main
    main.main_loop()
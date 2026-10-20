"""One-command check of the TTL dedup fix. No RFID reader, no Windows needed.

    .venv/bin/python tools/ttldedup_check.py [seconds] [python] [tags]

Starts a throwaway fake Koha API on loopback, points a copy of the app's
config at it, runs the real main.py while simulating scans by appending to
main.barcodes, and prints how many Koha requests that turned into.
"""

import configparser
import json
import os
import shutil
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))


def _detect_repo():
    """Find the repo whether this script sits at its root, in tools/, or anywhere."""
    env = os.environ.get('HARAVA_REPO')
    if env:
        return env
    here = HERE
    for _ in range(4):
        if (os.path.isfile(os.path.join(here, 'main.py'))
                and os.path.isdir(os.path.join(here, 'GUI'))):
            return here
        parent = os.path.dirname(here)
        if parent == here:
            break
        here = parent
    raise SystemExit('Could not locate the repo root. Set HARAVA_REPO=/path/to/rfid-harava')


REPO = _detect_repo()
SIM_RUN = os.path.join(HERE, 'sim_run.py')
WORK = os.path.join(os.environ.get('TMPDIR', '/tmp'), 'harava-ttldedup')
BARCODE = 'LVASK123100760'

ITEM = {"title": "Testikirja", "barcode": BARCODE, "itemnumber": "12345",
        "biblionumber": "1", "homebranch": "TESTI", "holdingbranch": "TESTI",
        "itemlost": 0, "onloan": None, "notforloan": "0",
        "itemcallnumber": "123.4", "deleted_on": "", "permanent_location": "",
        "found": "", "NiteetOsastolla": "1", "NiteetHylly": "1",
        "NiteetYht": "1", "datelastborrowed": "", "ccode": ""}

requests_seen = 0
_lock = threading.Lock()


def free_port():
    import socket
    s = socket.socket()
    s.bind(('127.0.0.1', 0))
    port = s.getsockname()[1]
    s.close()
    return port


class FakeKoha(BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'

    def log_message(self, *a):
        pass

    def _send(self, obj):
        body = json.dumps(obj).encode()
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        # Count only report fetches. Answering any other GET that might appear
        # later must not inflate the number; the token POST is separate anyway.
        global requests_seen
        if self.path.startswith('/reports'):
            with _lock:
                requests_seen += 1
        self._send([ITEM])

    def do_POST(self):
        self._send({"access_token": "fake-token", "expires_in": 3600})


def preflight(python):
    """Fail clearly if the interpreter cannot run the app."""
    proc = subprocess.run([python, '-c', 'import PySide6, requests'],
                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if proc.returncode != 0:
        raise SystemExit(
            f'{python} cannot import PySide6 and requests, which the app needs.\n'
            f'Install it for that interpreter, or pass one that already has it:\n'
            f'  {python} -m pip install "PySide6==6.8.0.2" requests\n'
            f'  .venv/bin/python tools/ttldedup_check.py [seconds] /path/to/venv/bin/python [tags]')


def tail(path, lines=15):
    try:
        with open(path, errors='replace') as fh:
            return ''.join(fh.readlines()[-lines:]).rstrip()
    except OSError:
        return '(no log written)'


def setup(api_port, fetchttl):
    for sub in ('Configs', 'GUI', 'resources'):
        os.makedirs(os.path.join(WORK, sub), exist_ok=True)
    shutil.copy(f'{REPO}/GUI/theme.css', f'{WORK}/GUI/theme.css')
    for f in os.listdir(f'{REPO}/resources'):
        shutil.copy(f'{REPO}/resources/{f}', f'{WORK}/resources/{f}')

    # Use configparser rather than string replacement: a changed default or a
    # different spacing in ConfigBase.ini would make replace() silently no-op,
    # and the run would then measure the wrong TTL while still looking valid.
    cfg = configparser.RawConfigParser()
    cfg.read(f'{REPO}/Configs/ConfigBase.ini', encoding='utf-8')
    cfg.set('API credentials', 'apitoken', 'fake-token')
    cfg.set('API credentials', 'apitokenlastupdated', '9999999999')
    cfg.set('API URLS', 'apiendpointurl',
            f'http://127.0.0.1:{api_port}/oauth/token')
    cfg.set('API URLS', 'reporterapiurl',
            f'http://127.0.0.1:{api_port}/reports')
    cfg.set('Other', 'reportid', '42')
    cfg.set('Other', 'fetchttl', str(fetchttl))
    cfg.set('API', 'client', 'testclient')
    cfg.set('API', 'secret', 'testsecret')
    with open(f'{WORK}/Configs/config.ini', 'w', encoding='utf-8') as fh:
        cfg.write(fh)

    users = configparser.RawConfigParser()
    users.read(f'{REPO}/Configs/UserSettingsBase.ini', encoding='utf-8')
    users.set('Conditions', 'collectall', 'True')
    with open(f'{WORK}/Configs/UserSettings.ini', 'w', encoding='utf-8') as fh:
        users.write(fh)


def run(python, seconds, fetchttl, tags, touch_settings=False):
    global requests_seen
    api_port = free_port()
    httpd = ThreadingHTTPServer(('127.0.0.1', api_port), FakeKoha)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    setup(api_port, fetchttl)
    requests_seen = 0

    env = dict(os.environ)
    env['PYTHONPATH'] = REPO
    env['QT_QPA_PLATFORM'] = os.environ.get('QT_QPA_PLATFORM', 'offscreen')
    env['SCAN_INTERVAL'] = '0.25'
    env['SCAN_TAGS'] = str(tags)
    env['HARAVA_WORK'] = WORK

    # Clear any stats left by an earlier run, so a crashed app cannot be
    # mistaken for a run that wrote these numbers.
    stats_path = os.path.join(WORK, 'simstats.json')
    for stale in (stats_path, stats_path + '.tmp'):
        try:
            os.remove(stale)
        except FileNotFoundError:
            pass

    stderr_path = os.path.join(WORK, 'app-stderr.log')
    with open(stderr_path, 'w') as errlog:
        proc = subprocess.Popen([python, SIM_RUN],
                                cwd=WORK, env=env,
                                stdout=subprocess.DEVNULL, stderr=errlog)
        if not touch_settings:
            time.sleep(seconds)
        else:
            # Wait for the startup fetch before touching, so the touch is a
            # change relative to the mtime the app has already recorded. A
            # fixed half-time point could land before the first tick on a slow
            # start and then simply set the baseline instead of changing it.
            deadline = time.monotonic() + seconds
            while requests_seen == 0 and time.monotonic() < deadline:
                time.sleep(0.02)
            # Bump only the mtime, exactly as the settings panel does when the
            # criteria are edited. The content is unchanged, so a second fetch
            # can only come from the cache being invalidated.
            os.utime(os.path.join(WORK, 'Configs', 'UserSettings.ini'), None)
            time.sleep(max(0.0, deadline - time.monotonic()))
        crashed_early = proc.poll() is not None
        if not crashed_early:
            proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
    httpd.shutdown()

    if crashed_early:
        raise SystemExit(
            f'The app exited before the {seconds}s run finished under {python}.\n'
            f'Last lines of {stderr_path}:\n{tail(stderr_path)}')

    if not os.path.exists(stats_path):
        raise SystemExit(
            f'The app did not run under {python}: no stats were written.\n'
            f'Last lines of {stderr_path}:\n{tail(stderr_path)}')

    with open(stats_path) as fh:
        st = json.load(fh)
    return {'requests': requests_seen, **st}


def main():
    seconds = int(sys.argv[1]) if len(sys.argv) > 1 else 20
    python = sys.argv[2] if len(sys.argv) > 2 else sys.executable
    python = python or sys.executable
    tags = int(sys.argv[3]) if len(sys.argv) > 3 else 1

    preflight(python)

    print(f'repo   : {REPO}')
    print(f'python : {python}')
    print(f'run    : {seconds}s, {tags} tag(s) scanned every 250ms\n')

    before = run(python, seconds, 0, tags)
    after = run(python, seconds, 60, tags)
    changed = run(python, seconds, 60, tags, touch_settings=True)

    hdr = f'{"":<30}{"scans":>8}{"Koha requests":>16}{"flashes":>10}'
    print(hdr)
    print('-' * len(hdr))
    for label, st in (('ttl = 0 (no dedup)', before),
                      ('ttl = 60 (dedup)', after),
                      ('ttl = 60 + criteria change', changed)):
        print(f'{label:<30}{st["scans"]:>8}'
              f'{st["requests"]:>16}{st["flashes"]:>10}')

    print()
    assert before['scans'] > 30, 'test invalid: not enough simulated scans'
    assert before['requests'] > 10, 'baseline should spam the API'
    assert before['flashes'] == 0, (
        'nothing is cached at ttl = 0, so nothing should flash')
    assert after['requests'] <= 2, f'expected ~1 request, got {after["requests"]}'
    assert after['flashes'] > 0, 'nothing flashed - locate feature lost!'
    # Every scan after the first fetch should flash once, so the upper bound
    # alone would let a partial loss through. Allow a small margin: the first
    # barcode is fetched rather than flashed, and a scan can occasionally land
    # between the queue being read and cleared.
    assert after['flashes'] >= after['scans'] - max(3, after['scans'] // 20), (
        f'only {after["flashes"]} flashes for {after["scans"]} scans: cached '
        're-reads are no longer being highlighted')
    # Each decoded report is either fetched or flashed once, so flashes cannot
    # exceed scans. More than that means the barcode queue is not drained every
    # tick and cached barcodes are re-flashed on every timer tick for the TTL.
    assert after['flashes'] <= after['scans'], (
        f'{after["flashes"]} flashes for {after["scans"]} scans: the barcode '
        'queue is not being drained each tick')
    # The two runs are wall-clock bounded, so allow a little jitter rather
    # than demanding exactly equal scan counts.
    assert abs(after['scans'] - before['scans']) <= max(3, before['scans'] // 10), \
        'both runs must simulate a comparable number of scans'

    # Touching UserSettings.ini mid-run must invalidate the cache. The tag is
    # still in the reader field, so it is re-read and must be fetched again:
    # one request at startup and one after the criteria change. Without the
    # mtime check the second read stays suppressed until the TTL expires.
    assert changed['requests'] == 2, (
        'a criteria change mid-run should cause exactly one extra request '
        f'(2 total), got {changed["requests"]}')

    print(f'{before["requests"]} requests -> {after["requests"]} request, '
          f'while still flashing {after["flashes"]} times.')
    print(f'A criteria change mid-run added one request '
          f'({changed["requests"]} total), as expected.')
    print('\nPASS: dedup works, locate-by-flashing is preserved, and changing '
          'the search criteria clears the cache.')
    print(f'(work dir: {WORK} - safe to delete)')


if __name__ == '__main__':
    main()
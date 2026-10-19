"""One-command check of the TTL dedup fix. No RFID reader, no Windows needed.

    .venv/bin/python tools/ttldedup_check.py [seconds] [python] [tags]

Starts a throwaway fake Koha API on loopback, points a copy of the app's
config at it, runs the real main.py while simulating scans by appending to
main.barcodes, and prints how many Koha requests that turned into.
"""

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
        # The report request. Only these are counted, so the startup token
        # POST below cannot throw the number off.
        global requests_seen
        with _lock:
            requests_seen += 1
        self._send([ITEM])

    def do_POST(self):
        self._send({"access_token": "fake-token", "expires_in": 3600})


def preflight(python):
    """Fail clearly if the interpreter cannot run the app."""
    proc = subprocess.run([python, '-c', 'import PySide6'],
                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if proc.returncode != 0:
        raise SystemExit(
            f'{python} cannot import PySide6, which the app needs.\n'
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

    with open(f'{REPO}/Configs/ConfigBase.ini') as fh:
        cfg = fh.read()
    cfg = cfg.replace('https://kimppa.koha-suomi.fi/api/v1/oauth/token',
                      f'http://127.0.0.1:{api_port}/oauth/token')
    cfg = cfg.replace('https://kimppa.koha-suomi.fi/api/v1/contrib/kohasuomi/reportservices/reports',
                      f'http://127.0.0.1:{api_port}/reports')
    cfg = cfg.replace('apitoken = ', 'apitoken = fake-token')
    cfg = cfg.replace('apitokenlastupdated = ', 'apitokenlastupdated = 9999999999')
    cfg = cfg.replace('reportid = ', 'reportid = 42')
    cfg = cfg.replace('client = ', 'client = testclient')
    cfg = cfg.replace('secret = ', 'secret = testsecret')
    cfg = cfg.replace('fetchttl = 60', f'fetchttl = {fetchttl}')
    with open(f'{WORK}/Configs/config.ini', 'w') as fh:
        fh.write(cfg)

    with open(f'{REPO}/Configs/UserSettingsBase.ini') as fh:
        users = fh.read().replace('collectall = False', 'collectall = True')
    with open(f'{WORK}/Configs/UserSettings.ini', 'w') as fh:
        fh.write(users)


def run(python, seconds, fetchttl, tags):
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
        time.sleep(seconds)
        crashed_early = proc.poll() is not None
        if not crashed_early:
            proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
    httpd.shutdown()

    if not os.path.exists(stats_path):
        why = 'it exited before writing any stats' if crashed_early \
            else 'no stats were written while it ran'
        raise SystemExit(
            f'The app did not run under {python}: {why}.\n'
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

    hdr = f'{"":<22}{"scans":>8}{"Koha requests":>16}{"flashes":>10}'
    print(hdr)
    print('-' * len(hdr))
    print(f'{"fetchttl = 0 (before)":<22}{before["scans"]:>8}'
          f'{before["requests"]:>16}{before["flashes"]:>10}')
    print(f'{"fetchttl = 60 (after)":<22}{after["scans"]:>8}'
          f'{after["requests"]:>16}{after["flashes"]:>10}')

    print()
    assert before['scans'] > 30, 'test invalid: not enough simulated scans'
    assert before['requests'] > 10, 'baseline should spam the API'
    assert after['requests'] <= 2, f'expected ~1 request, got {after["requests"]}'
    assert after['flashes'] > 0, 'nothing flashed - locate feature lost!'
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

    print(f'{before["requests"]} requests -> {after["requests"]} request, '
          f'while still flashing {after["flashes"]} times.')
    print('\nPASS: dedup works and locate-by-flashing is preserved.')
    print(f'(work dir: {WORK} - safe to delete)')


if __name__ == '__main__':
    main()
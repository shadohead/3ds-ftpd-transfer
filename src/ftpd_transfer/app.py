from __future__ import annotations

import cgi
import ftplib
import html
import http.server
import json
import os
import shutil
import socket
import tempfile
import threading
import time
import urllib.parse
import urllib.request
import webbrowser
from pathlib import Path
from typing import Any

HOST = "127.0.0.1"
DEFAULT_REMOTE_FOLDER = "/3ds/inbox"
CHUNK_SIZE = 64 * 1024

STATUS: dict[str, Any] = {
    "running": False,
    "ok": False,
    "message": "Ready.",
    "progress": 0,
    "log": [],
}
STATUS_LOCK = threading.Lock()


def set_status(message: str | None = None, progress: float | None = None, running: bool | None = None, ok: bool | None = None) -> None:
    with STATUS_LOCK:
        if message is not None:
            STATUS["message"] = message
            STATUS["log"].append(message)
            STATUS["log"] = STATUS["log"][-80:]
        if progress is not None:
            STATUS["progress"] = max(0, min(100, int(progress)))
        if running is not None:
            STATUS["running"] = running
        if ok is not None:
            STATUS["ok"] = ok


def status_snapshot() -> dict[str, Any]:
    with STATUS_LOCK:
        return dict(STATUS)


def sanitize_remote_folder(value: str | None) -> str:
    value = (value or DEFAULT_REMOTE_FOLDER).strip()
    return "/" + value.strip("/")


def filename_from_response(url: str, headers: Any) -> str:
    disposition = headers.get("Content-Disposition", "")
    if "filename=" in disposition:
        raw = disposition.split("filename=", 1)[1].split(";", 1)[0].strip().strip('"')
        if raw:
            return os.path.basename(urllib.parse.unquote(raw))

    parsed = urllib.parse.urlparse(url)
    name = os.path.basename(urllib.parse.unquote(parsed.path))
    return name or "download.bin"


def download_url(url: str) -> str:
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("Download URL must start with http:// or https://.")

    request = urllib.request.Request(url, headers={"User-Agent": "3ds-ftpd-transfer/0.1"})
    with urllib.request.urlopen(request, timeout=30) as response:
        status = getattr(response, "status", 200)
        if status >= 400:
            raise RuntimeError(f"download failed with HTTP {status}")

        name = filename_from_response(url, response.headers)
        target = os.path.join(tempfile.mkdtemp(prefix="3ds-ftpd-download-"), name)
        total = int(response.headers.get("Content-Length") or 0)
        done = 0
        set_status(f"Downloading {name}...", progress=1)

        with open(target, "wb") as out:
            while True:
                chunk = response.read(CHUNK_SIZE)
                if not chunk:
                    break
                out.write(chunk)
                done += len(chunk)
                if total:
                    set_status(f"Downloaded {done // 1024} KB of {total // 1024} KB.", progress=done / total * 45)
                else:
                    set_status(f"Downloaded {done // 1024} KB.", progress=15)

    if os.path.getsize(target) == 0:
        raise RuntimeError("download produced an empty file")
    return target


def ensure_remote_dir(ftp: ftplib.FTP, remote_folder: str) -> None:
    ftp.cwd("/")
    for part in [p for p in remote_folder.split("/") if p]:
        try:
            ftp.cwd(part)
        except ftplib.error_perm:
            ftp.mkd(part)
            ftp.cwd(part)


def upload_file(host: str, port: int, remote_folder: str, file_path: str) -> None:
    source = Path(file_path)
    size = source.stat().st_size
    uploaded = 0
    started = time.time()

    set_status(f"Connecting to {host}:{port}...", progress=45)
    with ftplib.FTP() as ftp:
        ftp.connect(host, port, timeout=20)
        ftp.login()
        ftp.set_pasv(True)
        ensure_remote_dir(ftp, remote_folder)
        ftp.cwd(remote_folder)

        def callback(block: bytes) -> None:
            nonlocal uploaded
            uploaded += len(block)
            elapsed = max(time.time() - started, 0.1)
            rate = uploaded / elapsed / 1024
            progress = 45 + (uploaded / size * 55 if size else 55)
            set_status(f"Uploaded {uploaded // 1024} KB of {size // 1024} KB at {rate:.0f} KB/s.", progress=progress)

        with open(source, "rb") as handle:
            ftp.storbinary(f"STOR {source.name}", handle, blocksize=CHUNK_SIZE, callback=callback)

    set_status(f"Sent {source.name} to {remote_folder}/", progress=100, ok=True)


def run_transfer(host: str, port: int, remote_folder: str, upload_path: str, url: str) -> None:
    cleanup_dir: str | None = None
    try:
        set_status("Starting transfer.", progress=0, running=True, ok=False)
        source = upload_path
        if not source:
            source = download_url(url)
            cleanup_dir = str(Path(source).parent)

        upload_file(host, port, remote_folder, source)
        set_status("Transfer complete.", progress=100, running=False, ok=True)
    except Exception as exc:
        set_status(f"Error: {exc}", running=False, ok=False)
    finally:
        if cleanup_dir:
            shutil.rmtree(cleanup_dir, ignore_errors=True)
        elif upload_path:
            shutil.rmtree(str(Path(upload_path).parent), ignore_errors=True)


class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, fmt: str, *args: object) -> None:
        return

    def do_GET(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/status":
            self.send_json(status_snapshot())
            return
        if parsed.path == "/shutdown":
            self.send_html("<!doctype html><title>Closed</title><p>3DS ftpd Transfer has closed. You can close this tab.</p>")
            threading.Thread(target=self.server.shutdown, daemon=True).start()
            return
        self.send_html(INDEX_HTML)

    def do_POST(self) -> None:
        if self.path != "/transfer":
            self.send_error(404)
            return

        if status_snapshot()["running"]:
            self.send_json({"ok": False, "error": "A transfer is already running."}, status=409)
            return

        form = cgi.FieldStorage(
            fp=self.rfile,
            headers=self.headers,
            environ={
                "REQUEST_METHOD": "POST",
                "CONTENT_TYPE": self.headers.get("Content-Type", ""),
                "CONTENT_LENGTH": self.headers.get("Content-Length", "0"),
            },
        )

        try:
            host = form.getfirst("host", "").strip()
            if not host:
                raise ValueError("Enter the IP address shown by ftpd.")
            port = int(form.getfirst("port", "5000").strip())
            if port <= 0 or port > 65535:
                raise ValueError("Port must be between 1 and 65535.")
            remote_folder = sanitize_remote_folder(form.getfirst("remote_folder", DEFAULT_REMOTE_FOLDER))
            url = form.getfirst("url", "").strip()

            upload_path = ""
            file_item = form["file"] if "file" in form else None
            if file_item is not None and getattr(file_item, "filename", ""):
                name = os.path.basename(file_item.filename)
                temp_dir = tempfile.mkdtemp(prefix="3ds-ftpd-upload-")
                upload_path = os.path.join(temp_dir, name)
                with open(upload_path, "wb") as out:
                    shutil.copyfileobj(file_item.file, out)

            if not upload_path and not url:
                raise ValueError("Choose a local file or paste a direct legal/homebrew URL.")

            thread = threading.Thread(target=run_transfer, args=(host, port, remote_folder, upload_path, url), daemon=True)
            thread.start()
            self.send_json({"ok": True})
        except Exception as exc:
            self.send_json({"ok": False, "error": str(exc)}, status=400)

    def send_json(self, payload: dict[str, Any], status: int = 200) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_html(self, payload: str) -> None:
        body = payload.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


INDEX_HTML = r"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>3DS ftpd Transfer</title>
  <style>
    :root { color-scheme: light dark; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }
    body { margin: 0; background: #f5f5f3; color: #191919; }
    main { max-width: 780px; margin: 0 auto; padding: 28px 18px 48px; }
    h1 { margin: 0 0 6px; font-size: 28px; letter-spacing: 0; }
    p { color: #555; line-height: 1.45; }
    form, section { background: #fff; border: 1px solid #ddd; border-radius: 8px; padding: 18px; margin-top: 16px; }
    label { display: block; font-weight: 650; margin: 14px 0 6px; }
    input { box-sizing: border-box; width: 100%; padding: 10px 11px; border: 1px solid #bbb; border-radius: 6px; font: inherit; }
    .row { display: grid; grid-template-columns: minmax(0, 1fr) 110px; gap: 12px; }
    .actions { display: flex; gap: 10px; align-items: center; flex-wrap: wrap; }
    button, .button-link { margin-top: 18px; padding: 11px 14px; border: 0; border-radius: 6px; background: #176b87; color: #fff; font: inherit; font-weight: 700; cursor: pointer; text-decoration: none; }
    .button-link { background: #555; display: inline-block; }
    button:disabled { opacity: .55; cursor: wait; }
    progress { width: 100%; height: 18px; }
    pre { white-space: pre-wrap; word-break: break-word; background: #101112; color: #e8e8e8; border-radius: 6px; padding: 12px; min-height: 140px; }
    .note { font-size: 13px; color: #666; }
    @media (prefers-color-scheme: dark) {
      body { background: #141414; color: #f1f1f1; }
      form, section { background: #202020; border-color: #3a3a3a; }
      p, .note { color: #c7c7c7; }
      input { background: #151515; border-color: #555; color: #f1f1f1; }
    }
  </style>
</head>
<body>
  <main>
    <h1>3DS ftpd Transfer</h1>
    <p>Open ftpd on your 3DS, enter the IP and port shown there, then send a legal homebrew file, save, patch, or your own dump.</p>

    <form id="transferForm">
      <div class="row">
        <div>
          <label for="host">3DS IP address</label>
          <input id="host" name="host" placeholder="192.168.1.123" required>
        </div>
        <div>
          <label for="port">Port</label>
          <input id="port" name="port" value="5000" inputmode="numeric" required>
        </div>
      </div>

      <label for="remote_folder">Destination folder on 3DS SD</label>
      <input id="remote_folder" name="remote_folder" value="/3ds/inbox">

      <label for="file">Local file</label>
      <input id="file" name="file" type="file">

      <label for="url">Direct download URL</label>
      <input id="url" name="url" placeholder="https://example.com/homebrew.zip">
      <p class="note">If you choose a local file and enter a URL, the local file is used. URL downloads must be direct links to legal/homebrew files.</p>

      <div class="actions">
        <button id="sendButton" type="submit">Send to 3DS</button>
        <a class="button-link" href="/shutdown">Quit</a>
      </div>
    </form>

    <section>
      <progress id="progress" value="0" max="100"></progress>
      <p id="message">Ready.</p>
      <pre id="log"></pre>
    </section>
  </main>

  <script>
    const form = document.getElementById('transferForm');
    const button = document.getElementById('sendButton');
    const progress = document.getElementById('progress');
    const message = document.getElementById('message');
    const log = document.getElementById('log');

    form.addEventListener('submit', async (event) => {
      event.preventDefault();
      button.disabled = true;
      const response = await fetch('/transfer', { method: 'POST', body: new FormData(form) });
      const payload = await response.json();
      if (!payload.ok) {
        button.disabled = false;
        alert(payload.error || 'Transfer failed to start.');
      }
    });

    async function poll() {
      try {
        const response = await fetch('/status');
        const status = await response.json();
        progress.value = status.progress || 0;
        message.textContent = status.message || '';
        log.textContent = (status.log || []).join('\n');
        button.disabled = !!status.running;
      } catch (error) {
        message.textContent = 'Could not reach local transfer helper.';
      }
      setTimeout(poll, 700);
    }
    poll();
  </script>
</body>
</html>
"""


def find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind((HOST, 0))
        return int(sock.getsockname()[1])


def main() -> None:
    port = find_free_port()
    server = http.server.ThreadingHTTPServer((HOST, port), Handler)
    url = f"http://{HOST}:{port}/"
    print(f"3DS ftpd Transfer is running at {url}", flush=True)
    print("Use the Quit button in the browser when you are done.", flush=True)
    webbrowser.open(url)
    server.serve_forever()

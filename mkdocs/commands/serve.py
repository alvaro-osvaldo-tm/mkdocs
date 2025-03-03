from __future__ import annotations

import logging
import shutil
import sys
import tempfile
from os import getpid
from os.path import isdir, isfile, join
from signal import SIGINT, SIGTERM, signal as configure_signal_handler , strsignal
from time import sleep
from typing import TYPE_CHECKING
from urllib.parse import urlsplit

from mkdocs.commands.build import build
from mkdocs.config import load_config
from mkdocs.livereload import LiveReloadServer, _serve_url

if TYPE_CHECKING:
    from mkdocs.config.defaults import MkDocsConfig

log = logging.getLogger(__name__)


def serve(
    config_file: str | None = None,
    livereload: bool = True,
    build_type: str | None = None,
    watch_theme: bool = False,
    watch: list[str] = [],
    *,
    open_in_browser: bool = False,
    **kwargs,
) -> None:
    """
    Start the MkDocs development server.

    By default it will serve the documentation on http://localhost:8000/ and
    it will rebuild the documentation and refresh the page automatically
    whenever a file is edited.
    """
    # Create a temporary build directory, and set some options to serve it
    # PY2 returns a byte string by default. The Unicode prefix ensures a Unicode
    # string is returned. And it makes MkDocs temp dirs easier to identify.
    site_dir = tempfile.mkdtemp(prefix='mkdocs_')

    def get_config():
        config = load_config(
            config_file=config_file,
            site_dir=site_dir,
            **kwargs,
        )
        config.watch.extend(watch)
        return config

    is_clean = build_type == 'clean'
    is_dirty = build_type == 'dirty'

    config = get_config()
    config.plugins.on_startup(command=('build' if is_clean else 'serve'), dirty=is_dirty)

    host, port = config.dev_addr
    mount_path = urlsplit(config.site_url or '/').path
    config.site_url = serve_url = _serve_url(host, port, mount_path)

    def builder(config: MkDocsConfig | None = None):
        log.info("Building documentation...")
        if config is None:
            config = get_config()
            config.site_url = serve_url

        build(config, serve_url=None if is_clean else serve_url, dirty=is_dirty)

    server = LiveReloadServer(
        builder=builder, host=host, port=port, root=site_dir, mount_path=mount_path
    )

    def error_handler(code) -> bytes | None:
        if code in (404, 500):
            error_page = join(site_dir, f'{code}.html')
            if isfile(error_page):
                with open(error_page, 'rb') as f:
                    return f.read()
        return None

    def handle_signal(signum, frame) -> None:

        log.info(f"Received signal ...")
        print(f"Received signal code '{signum}'")


        signal_name = strsignal(signum)
        log.info(f"Received signal '{signal_name}'")

        exit(0)

    def shutdown() -> None:
        if not server.is_active:
            return

        log.info("Shutting down...")

        try:
            server.shutdown()
        finally:
            config.plugins.on_shutdown()

        if isdir(site_dir):
            shutil.rmtree(site_dir)

    server.error_handler = error_handler

    print(f"Platform: {sys.platform}")

    import signal
    for signal_code in signal.Signals:

        #if signal_code != 21:
            #continue

        try:
            configure_signal_handler(signal_code, handle_signal)
            print(f"Configured for {strsignal(signal_code)}")
        except:
            pass


    try:
      while True:

          print(f"[{getpid()}] waiting ")
          sleep(1)
    except KeyboardInterrupt:
        print(" ========= CAPTURED =========")
        shutdown()
    finally:
        shutdown()

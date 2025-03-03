from __future__ import annotations

import subprocess
import unittest
from dataclasses import dataclass
from functools import singledispatchmethod
from pathlib import Path
from subprocess import Popen
from tempfile import TemporaryDirectory
from time import sleep

from packaging.tags import platform_tags


@dataclass
class Sample_Repository:
    handler: TemporaryDirectory
    site_dir: str
    signature: str

    def __del__(self):
        from sys import platform

        if platform == "linux":
            self.handler.cleanup()


class Shutdown_by_signal_tests(unittest.TestCase):
    SLEEPING_TIME_WAITING_FOR_START = 2
    SLEEPING_TIME_WAITING_FOR_SHUTDOWN = 12
    SLEEPING_TIME_WAITING_FOR_PROCESS = 1200
    TRIES_TO_CHECK_FOR_DIRECTORY_CLEANUP = 4
    EXECUTE_MKDOCS_SILENTLY = False

    def _create_sample_repository(self) -> Sample_Repository:
        from os import mkdir
        from uuid import uuid4

        from yaml import dump

        handler = TemporaryDirectory(prefix='mkdocs_test-')
        site_dir = handler.name

        signature = uuid4().hex

        configuration = {'site_name': 'Testing case', 'docs_dir': 'docs'}

        docs_dir = f"{site_dir}/{configuration.get('docs_dir')}"
        mkdir(docs_dir)

        Path(site_dir, "mkdocs.yml").write_text(dump(configuration))
        Path(docs_dir, "index.md").write_text("# Index File")
        Path(docs_dir, "signature.md").write_text(f"# {signature} ")

        return Sample_Repository(
            handler=handler,
            site_dir=site_dir,
            signature=signature,
        )

    def _execute_mkdocs_as_liveserver(self, site_dir: str) -> Popen:
        from os import chdir, getcwd
        from subprocess import DEVNULL
        from sys import platform

        current_working_dir = getcwd()
        chdir(site_dir)
        creation_flags = 0

        if platform == "linux":
            from errno import EADDRINUSE
            from socket import AF_INET, SOCK_STREAM, socket

            port_testing = socket(AF_INET, SOCK_STREAM)

            try:
                port_testing.bind(("127.0.0.1", 8000))
            except OSError as exception:
                if exception.errno == EADDRINUSE:
                    Popen('killall mkdocs'.split(' ')).wait(
                        timeout=self.SLEEPING_TIME_WAITING_FOR_PROCESS
                    )

            port_testing.close()

        if platform  == "win32":
            creation_flags = subprocess.CREATE_NEW_PROCESS_GROUP


        command = 'mkdocs serve'.split(' ')

        if self.EXECUTE_MKDOCS_SILENTLY:
            mkdocs = Popen(command, stdout=DEVNULL, stderr=DEVNULL, shell=False,creationflags=creation_flags)
        else:
            mkdocs = Popen(command,creationflags=creation_flags)

        sleep(self.SLEEPING_TIME_WAITING_FOR_START)

        chdir(current_working_dir)

        return mkdocs

    def _locate_mkdocs_directory(self, signature: str) -> Path | None:
        from pathlib import Path
        from tempfile import TemporaryDirectory

        temporary_directory_probe = TemporaryDirectory()
        temporary_directory = Path(f"{temporary_directory_probe.name}").parent

        for mkdocs_temporary_directory in temporary_directory.glob('mkdocs_*'):
            mkdocs_temporary_path = Path(mkdocs_temporary_directory)
            mkdocs_signature_path = Path(f"{mkdocs_temporary_path}/signature/index.html")

            if not mkdocs_temporary_path.exists():
                continue

            if not mkdocs_temporary_path.is_dir():
                continue

            if not mkdocs_signature_path.exists():
                continue

            with mkdocs_signature_path.open('r') as fp:
                signature_found = fp.read()

            if signature_found.find(signature) == -1:
                continue

            temporary_directory_probe.cleanup()

            return mkdocs_temporary_path

        return None

    def _is_active(self, mkdocs: Popen) -> bool:

        from errno import ESRCH
        from os import kill

        if mkdocs.returncode is not None:
            return False

        try:
            from signal import SIG_BLOCK
            kill(mkdocs.pid, SIG_BLOCK)
        except OSError as exception:
            if exception.errno == ESRCH:
                return True
        except ImportError:
            return False

        return False

    def _wait_for_shutdown(self, mkdocs: Popen, signal: int):
        from os import kill

        kill(mkdocs.pid, signal)

        while self._is_active(mkdocs):
            sleep(self.SLEEPING_TIME_WAITING_FOR_SHUTDOWN)

    def _was_directory_cleaned(self, path: Path) -> bool:
        for _ in range(self.TRIES_TO_CHECK_FOR_DIRECTORY_CLEANUP):
            if not path.exists():
                return True

            sleep(self.SLEEPING_TIME_WAITING_FOR_PROCESS)

        return False

    def test_shutdown_with_signal(self):

        from sys import platform

        from signal import  strsignal

        signals =[]
        import signal
        for signal_code in signal.Signals:
            try:
                strsignal(signal_code)
                signals.append(signal_code)
            except:
                pass


        repository = self._create_sample_repository()

        for signal in signals:

            print(f" ============ Testing with '{strsignal(signal)}' ============ ")

            mkdocs = self._execute_mkdocs_as_liveserver(repository.site_dir)

            self._wait_for_shutdown(mkdocs, signal)

            # This is a flaw in 'liveserver' shutdown process
            # it seems mkdocs become zombie when testing.
            while mkdocs.returncode is None:
                mkdocs.wait(timeout=self.SLEEPING_TIME_WAITING_FOR_PROCESS)

            del mkdocs

        del repository


if __name__ == '__main__':
    Shutdown_by_signal_tests()

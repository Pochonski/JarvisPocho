"""
Clap Detection Module for MARK XXXIX
Detects 2 claps in rapid succession to launch the assistant.
"""

import numpy as np
import sounddevice as sd
import threading
import time
import os
import sys
from pathlib import Path


class ClapDetector:
    def __init__(
        self,
        clap_count: int = 2,
        clap_window: float = 1.5,
        threshold: float = 0.6,
        sample_rate: int = 16000,
        warmup_time: float = 1.0,
    ):
        self.clap_count = clap_count
        self.clap_window = clap_window
        self.threshold = threshold
        self.sample_rate = sample_rate
        self.warmup_time = warmup_time

        self._claps = []
        self._running = False
        self._stream = None
        self._callback_fn = None
        self._exit_event = threading.Event()
        self._start_time = None
        self._last_clap_time = 0

    def _on_audio(self, indata, frames, time_info, status):
        if status:
            return

        # Warmup period - ignore initial audio
        if time.time() - self._start_time < self.warmup_time:
            return

        volume = np.sqrt(np.mean(indata ** 2))
        is_clap = volume > self.threshold

        # Debounce: ignore claps within 0.2 seconds of each other
        now = time.time()
        if is_clap and (now - self._last_clap_time) < 0.2:
            return

        if is_clap:
            self._last_clap_time = now
            self._claps.append(now)
            self._claps = [t for t in self._claps if now - t <= self.clap_window]

            if len(self._claps) >= self.clap_count:
                self._exit_event.set()
                if self._callback_fn:
                    try:
                        self._callback_fn()
                    except Exception:
                        pass
                self._claps = []

    def start(self, callback=None):
        self._callback_fn = callback
        self._running = True
        self._claps = []
        self._exit_event.clear()
        self._start_time = time.time()
        self._last_clap_time = 0

        self._stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=1,
            dtype="float32",
            blocksize=1024,
            callback=self._on_audio,
        )
        self._stream.start()
        print(f"[ClapDetector] 🎤 Listening for {self.clap_count} claps within {self.clap_window}s...")

    def stop(self):
        self._running = False
        if self._stream:
            self._stream.stop()
            self._stream.close()
            self._stream = None
        print("[ClapDetector] ⏹️ Stopped")

    def wait_for_clap(self, timeout=None) -> bool:
        return self._exit_event.wait(timeout=timeout)

    def is_listening(self) -> bool:
        return self._running and not self._exit_event.is_set()


def launch_on_clap():
    import subprocess

    print("\n[ClapDetector] 👏👏 Two claps detected! Launching MARK XXXIX...\n")

    base_dir = Path(__file__).resolve().parent

    env = os.environ.copy()
    env["DISPLAY"] = ":1"
    env["WAYLAND_DISPLAY"] = "wayland-1"
    env["XDG_RUNTIME_DIR"] = "/run/user/1000"
    env["QT_QPA_PLATFORM"] = "wayland"

    subprocess.Popen(
        [str(base_dir / "run.sh")],
        env=env,
        cwd=str(base_dir),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )


def wait_for_claps():
    detector = ClapDetector(
        clap_count=2,
        clap_window=1.5,
        threshold=0.6,
        sample_rate=16000,
        warmup_time=1.0,
    )

    detector.start(callback=None)

    try:
        while detector.is_listening():
            time.sleep(0.1)
    except KeyboardInterrupt:
        pass
    finally:
        detector.stop()

    if detector._exit_event.is_set():
        launch_on_clap()
        time.sleep(2)
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    wait_for_claps()
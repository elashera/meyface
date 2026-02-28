#!/usr/bin/env python3
"""Simple desktop UI for yt-dlp audio downloads."""

from __future__ import annotations

import queue
import subprocess
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk


class AudioDownloaderUI:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("yt-dlp Audio Downloader")
        self.root.geometry("760x520")

        self.url_var = tk.StringVar()
        self.output_dir_var = tk.StringVar(value=str(Path.home() / "Downloads"))
        self.format_var = tk.StringVar(value="mp3_320")

        self.proc: subprocess.Popen[str] | None = None
        self.log_queue: queue.Queue[str | None] = queue.Queue()

        self._build_ui()
        self._poll_logs()

    def _build_ui(self) -> None:
        main = ttk.Frame(self.root, padding=14)
        main.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main, text="URL (YouTube / YouTube Music):").pack(anchor=tk.W)
        ttk.Entry(main, textvariable=self.url_var).pack(fill=tk.X, pady=(4, 10))

        ttk.Label(main, text="Formato de salida:").pack(anchor=tk.W)
        choices = [
            ("MP3 320 kbps", "mp3_320"),
            ("AAC", "aac"),
            ("Opus (sin conversión)", "opus"),
        ]
        for label, value in choices:
            ttk.Radiobutton(main, text=label, value=value, variable=self.format_var).pack(anchor=tk.W)

        ttk.Label(main, text="Carpeta de salida:").pack(anchor=tk.W, pady=(10, 0))
        out_row = ttk.Frame(main)
        out_row.pack(fill=tk.X, pady=(4, 10))

        ttk.Entry(out_row, textvariable=self.output_dir_var).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(out_row, text="Elegir...", command=self._choose_output_dir).pack(side=tk.LEFT, padx=(8, 0))

        btn_row = ttk.Frame(main)
        btn_row.pack(fill=tk.X)
        self.download_btn = ttk.Button(btn_row, text="Descargar audio", command=self._start_download)
        self.download_btn.pack(side=tk.LEFT)

        self.stop_btn = ttk.Button(btn_row, text="Detener", command=self._stop_download, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=(8, 0))

        ttk.Label(main, text="Log:").pack(anchor=tk.W, pady=(10, 0))
        self.log = tk.Text(main, height=14, wrap=tk.WORD)
        self.log.pack(fill=tk.BOTH, expand=True)

    def _choose_output_dir(self) -> None:
        directory = filedialog.askdirectory(initialdir=self.output_dir_var.get() or str(Path.home()))
        if directory:
            self.output_dir_var.set(directory)

    def _build_command(self) -> list[str]:
        target_dir = Path(self.output_dir_var.get()).expanduser()
        target_dir.mkdir(parents=True, exist_ok=True)

        cmd = [
            sys.executable,
            "-m",
            "yt_dlp",
            "--newline",
            "-P",
            str(target_dir),
            "-o",
            "%(title)s [%(id)s].%(ext)s",
        ]

        mode = self.format_var.get()
        if mode == "mp3_320":
            cmd += ["-f", "ba[acodec*=opus]/ba", "-x", "--audio-format", "mp3", "--audio-quality", "320K"]
        elif mode == "aac":
            cmd += ["-f", "ba[acodec*=opus]/ba", "-x", "--audio-format", "aac", "--audio-quality", "0"]
        else:
            cmd += ["-f", "ba[acodec*=opus]/ba"]

        cmd.append(self.url_var.get().strip())
        return cmd

    def _start_download(self) -> None:
        url = self.url_var.get().strip()
        if not url:
            messagebox.showerror("Falta URL", "Introduce una URL de YouTube o YouTube Music.")
            return

        if self.proc is not None:
            messagebox.showinfo("En progreso", "Ya hay una descarga en curso.")
            return

        cmd = self._build_command()
        self._append_log("$ " + " ".join(cmd))

        self.download_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)

        worker = threading.Thread(target=self._run_download, args=(cmd,), daemon=True)
        worker.start()

    def _run_download(self, cmd: list[str]) -> None:
        try:
            self.proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )
            assert self.proc.stdout is not None
            for line in self.proc.stdout:
                self.log_queue.put(line.rstrip())
            return_code = self.proc.wait()
            status = "OK" if return_code == 0 else f"ERROR (exit {return_code})"
            self.log_queue.put(f"\nFinalizado: {status}")
        except Exception as exc:  # noqa: BLE001
            self.log_queue.put(f"Error lanzando yt-dlp: {exc}")
        finally:
            self.proc = None
            self.log_queue.put(None)

    def _stop_download(self) -> None:
        if self.proc is None:
            return
        self._append_log("\nDeteniendo descarga...")
        self.proc.terminate()

    def _poll_logs(self) -> None:
        while True:
            try:
                item = self.log_queue.get_nowait()
            except queue.Empty:
                break

            if item is None:
                self.download_btn.config(state=tk.NORMAL)
                self.stop_btn.config(state=tk.DISABLED)
            else:
                self._append_log(item)

        self.root.after(120, self._poll_logs)

    def _append_log(self, text: str) -> None:
        self.log.insert(tk.END, text + "\n")
        self.log.see(tk.END)


def main() -> int:
    root = tk.Tk()
    AudioDownloaderUI(root)
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

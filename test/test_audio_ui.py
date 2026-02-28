"""Tests for audio_ui security hardening."""

from __future__ import annotations

import os
import unittest

from audio_ui import AudioDownloaderUI

_HAS_DISPLAY = bool(os.environ.get('DISPLAY'))


class TestURLValidation(unittest.TestCase):
    """Ensure only http(s) URLs are accepted."""

    def test_valid_https(self):
        self.assertTrue(AudioDownloaderUI._is_valid_url('https://www.youtube.com/watch?v=abc'))

    def test_valid_http(self):
        self.assertTrue(AudioDownloaderUI._is_valid_url('http://youtube.com/watch?v=abc'))

    def test_valid_case_insensitive(self):
        self.assertTrue(AudioDownloaderUI._is_valid_url('HTTPS://YOUTUBE.COM'))

    def test_reject_empty(self):
        self.assertFalse(AudioDownloaderUI._is_valid_url(''))

    def test_reject_option_exec(self):
        self.assertFalse(AudioDownloaderUI._is_valid_url('--exec=rm -rf /'))

    def test_reject_option_batch_file(self):
        self.assertFalse(AudioDownloaderUI._is_valid_url('--batch-file=/etc/passwd'))

    def test_reject_option_cookies(self):
        self.assertFalse(AudioDownloaderUI._is_valid_url('--cookies-from-browser=chrome'))

    def test_reject_short_option(self):
        self.assertFalse(AudioDownloaderUI._is_valid_url('-v'))

    def test_reject_bare_path(self):
        self.assertFalse(AudioDownloaderUI._is_valid_url('/etc/passwd'))

    def test_reject_ftp(self):
        self.assertFalse(AudioDownloaderUI._is_valid_url('ftp://example.com/file'))

    def test_reject_javascript(self):
        self.assertFalse(AudioDownloaderUI._is_valid_url('javascript:alert(1)'))


@unittest.skipUnless(_HAS_DISPLAY, 'no $DISPLAY – Tkinter cannot initialise')
class TestBuildCommandSafety(unittest.TestCase):
    """Verify the command list contains '--' before the URL and '--no-exec'."""

    def _make_ui(self):
        """Create a UI instance with a hidden Tk root."""
        import tkinter as tk

        root = tk.Tk()
        root.withdraw()
        ui = AudioDownloaderUI(root)
        return ui, root

    def test_double_dash_before_url(self):
        ui, root = self._make_ui()
        try:
            ui.url_var.set('https://www.youtube.com/watch?v=test123')
            cmd = ui._build_command()
            url_index = cmd.index('https://www.youtube.com/watch?v=test123')
            self.assertEqual(cmd[url_index - 1], '--')
        finally:
            root.destroy()

    def test_no_exec_flag_present(self):
        ui, root = self._make_ui()
        try:
            ui.url_var.set('https://www.youtube.com/watch?v=test123')
            cmd = ui._build_command()
            self.assertIn('--no-exec', cmd)
        finally:
            root.destroy()

    def test_url_is_last_element(self):
        ui, root = self._make_ui()
        try:
            ui.url_var.set('https://www.youtube.com/watch?v=test123')
            cmd = ui._build_command()
            self.assertEqual(cmd[-1], 'https://www.youtube.com/watch?v=test123')
        finally:
            root.destroy()


if __name__ == '__main__':
    unittest.main()

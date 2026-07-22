"""
Entry point for the Geeta Pariwar Nepal Sadhak CRM application.

Initialises the database, seeds the default admin account, and manages
a single root window that swaps between login and dashboard views.
"""

import logging
import socket
import sys
import traceback

import ttkbootstrap as ttk
from ttkbootstrap.constants import *

from database import initialize_database
from services.auth_service import seed_admin
from views.login_window import LoginFrame
from views.dashboard import DashboardFrame

log = logging.getLogger(__name__)

_LOCK_SOCKET: socket.socket | None = None
LOCK_PORT = 48765


def _show_fatal_error(exc: BaseException) -> None:
    msg = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
    try:
        import tkinter.messagebox as mb
        mb.showerror("Fatal Error", msg)
    except Exception:
        import ctypes
        ctypes.windll.user32.MessageBoxW(0, msg, "Fatal Error", 0x10)


def _acquire_instance_lock() -> bool:
    global _LOCK_SOCKET
    try:
        _LOCK_SOCKET = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        _LOCK_SOCKET.bind(("127.0.0.1", LOCK_PORT))
        _LOCK_SOCKET.listen(1)
        return True
    except OSError:
        return False


class App(ttk.Window):
    def __init__(self) -> None:
        super().__init__(themename="darkly")
        self.title("Geeta Pariwar Nepal Sadhak CRM")
        self.geometry("1024x680")
        self.minsize(800, 520)

        self.update_idletasks()
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        x = (screen_w - self.winfo_width()) // 2
        y = (screen_h - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")

        self.protocol("WM_DELETE_WINDOW", self._on_close)

        self._current_frame: ttk.Frame | None = None
        self.show_login()

    def _clear(self) -> None:
        if self._current_frame is not None:
            self._current_frame.destroy()
            self._current_frame = None

    def _on_close(self) -> None:
        self._clear()
        self.destroy()

    def show_login(self) -> None:
        self._clear()
        self._current_frame = LoginFrame(self, on_login_success=self.show_dashboard)

    def show_dashboard(self, user) -> None:
        self._clear()
        try:
            self._current_frame = DashboardFrame(
                self, user=user, on_logout=self.show_login
            )
            self.title(
                f"Geeta Pariwar Nepal Sadhak CRM – Logged in as {user.full_name}"
            )
        except Exception as exc:
            log.exception("Failed to create dashboard")
            import tkinter.messagebox as mb
            mb.showerror("Dashboard Error", f"Failed to load dashboard:\n{exc}")
            self.show_login()


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    if not _acquire_instance_lock():
        log.error("Another instance is already running.")
        import tkinter.messagebox as mb
        mb.showerror("Error", "Geeta Pariwar CRM is already running.")
        sys.exit(1)

    try:
        initialize_database()
    except Exception as exc:
        log.critical("Database initialization failed: %s", exc)
        _show_fatal_error(RuntimeError(f"Database initialization failed:\n{exc}"))
        sys.exit(1)

    try:
        seed_admin()
    except Exception as exc:
        log.warning("Admin seeding failed: %s", exc)

    try:
        app = App()
        app.mainloop()
    except Exception as exc:
        log.critical("Application crashed: %s", exc)
        _show_fatal_error(exc)
        sys.exit(1)


if __name__ == "__main__":
    main()

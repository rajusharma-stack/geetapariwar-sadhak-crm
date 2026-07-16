"""
Entry point for the Geeta Pariwar Nepal Sadhak CRM application.

Initialises the database, seeds the default admin account, and manages
a single root window that swaps between login and dashboard views.
"""

import sys
import traceback

import ttkbootstrap as ttk
from ttkbootstrap.constants import *

from database import initialize_database
from services.auth_service import seed_admin
from views.login_window import LoginFrame
from views.dashboard import DashboardFrame


def _show_fatal_error(exc: BaseException) -> None:
    """Display a critical error in a message box (works even without Tk root)."""
    msg = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
    try:
        import tkinter.messagebox as mb
        mb.showerror("Fatal Error", msg)
    except Exception:
        import ctypes
        ctypes.windll.user32.MessageBoxW(0, msg, "Fatal Error", 0x10)


class App(ttk.Window):
    """Single-root application that switches between login and dashboard."""

    def __init__(self) -> None:
        super().__init__(themename="superhero")
        self.title("Geeta Pariwar Nepal Sadhak CRM")
        self.geometry("1024x680")
        self.minsize(800, 520)

        self.update_idletasks()
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        x = (screen_w - self.winfo_width()) // 2
        y = (screen_h - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")

        self._current_frame: ttk.Frame | None = None
        self.show_login()

    def _clear(self) -> None:
        if self._current_frame is not None:
            self._current_frame.destroy()
            self._current_frame = None

    def show_login(self) -> None:
        self._clear()
        self._current_frame = LoginFrame(self, on_login_success=self.show_dashboard)

    def show_dashboard(self, user) -> None:
        self._clear()
        self._current_frame = DashboardFrame(
            self, user=user, on_logout=self.show_login
        )
        self.title(
            f"Geeta Pariwar Nepal Sadhak CRM – Logged in as {user.full_name}"
        )


def main() -> None:
    """Application entry point."""
    try:
        initialize_database()
        seed_admin()
        app = App()
        app.mainloop()
    except Exception as exc:
        _show_fatal_error(exc)
        sys.exit(1)


if __name__ == "__main__":
    main()

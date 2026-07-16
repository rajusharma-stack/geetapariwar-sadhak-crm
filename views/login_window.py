"""
Login screen for the CRM application.

Authenticates users via auth_service and, on success, notifies the
parent controller to switch to the main dashboard.
"""

import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox
from services.auth_service import authenticate


class LoginFrame(ttk.Frame):
    """Login form – packed into the root window."""

    def __init__(self, parent: ttk.Window, on_login_success) -> None:
        super().__init__(parent)
        self._on_success = on_login_success

        inner = ttk.Frame(self, padding=30)
        inner.place(relx=0.5, rely=0.45, anchor=CENTER)

        # Title (use contrasting bootstyle for dark themes)
        ttk.Label(
            inner,
            text="Geeta Pariwar Nepal",
            font=("Segoe UI", 16, "bold"),
            bootstyle="inverse",
        ).pack(pady=(0, 2))
        ttk.Label(
            inner,
            text="Sadhak CRM",
            font=("Segoe UI", 12),
            bootstyle="inverse",
        ).pack(pady=(0, 24))

        # Username
        ttk.Label(inner, text="Username", font=("Segoe UI", 10)).pack(
            anchor=W, pady=(0, 2)
        )
        self.username_var = tk.StringVar()
        self.username_entry = ttk.Entry(
            inner, textvariable=self.username_var, width=32
        )
        self.username_entry.pack(fill=X, pady=(0, 10))

        # Password
        ttk.Label(inner, text="Password", font=("Segoe UI", 10)).pack(
            anchor=W, pady=(0, 2)
        )
        self.password_var = tk.StringVar()
        self.password_entry = ttk.Entry(
            inner, textvariable=self.password_var, width=32, show="*"
        )
        self.password_entry.pack(fill=X, pady=(0, 24))

        self.password_entry.bind("<Return>", lambda _: self._do_login())

        # Buttons
        btn_row = ttk.Frame(inner)
        btn_row.pack(fill=X)

        self.login_btn = ttk.Button(
            btn_row, text="Login", command=self._do_login, bootstyle=PRIMARY, width=12
        )
        self.login_btn.pack(side=LEFT, padx=(0, 8))

        self.exit_btn = ttk.Button(
            btn_row, text="Exit", command=parent.quit, bootstyle=SECONDARY, width=12
        )
        self.exit_btn.pack(side=LEFT)

        self.pack(fill=BOTH, expand=YES)
        self.username_entry.focus()

    def _do_login(self) -> None:
        username = self.username_var.get().strip()
        password = self.password_var.get()

        if not username or not password:
            messagebox.showwarning(
                "Validation", "Please enter both username and password."
            )
            return

        user = authenticate(username, password)
        if user is None:
            messagebox.showerror("Login Failed", "Invalid username or password.")
            return

        self._on_success(user)

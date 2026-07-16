"""
Main dashboard shown after successful login.

Displays user information, a registration form, and a list of saved
Sadhak records with full audit trail (who created / last updated).
"""

import threading
import tkinter as tk
import webbrowser
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox, Toplevel
from pathlib import Path

from database import get_connection
from services.backup_service import backup_to_drive
from services.prn_service import search_prn, search_by_prn, _select_best_prn_result
from services.group_service import (
    get_all_groups,
    get_group_with_names,
    save_group,
    delete_group,
    can_edit_sadhak,
    get_history,
)

DEFAULT_COUNTRY_CODE = "+977"

COUNTRY_CODES = [
    "+93", "+355", "+213", "+1684", "+376", "+244", "+1264", "+1268",
    "+54", "+374", "+297", "+61", "+43", "+994", "+1242", "+973",
    "+880", "+1246", "+375", "+32", "+501", "+229", "+1441", "+975",
    "+591", "+387", "+267", "+55", "+1284", "+673", "+359", "+226",
    "+257", "+855", "+237", "+1", "+238", "+1345", "+236", "+235",
    "+56", "+86", "+57", "+269", "+682", "+506", "+225",
    "+385", "+53", "+357", "+420", "+243", "+45", "+253", "+1767",
    "+1809", "+670", "+593", "+20", "+503", "+240", "+291", "+372",
    "+251", "+500", "+298", "+679", "+358", "+33", "+594", "+689",
    "+241", "+220", "+995", "+49", "+233", "+350", "+30", "+1473",
    "+590", "+1671", "+502", "+224", "+245", "+592", "+509", "+504",
    "+852", "+36", "+354", "+91", "+62", "+98", "+964", "+353",
    "+972", "+39", "+1876", "+81", "+962", "+7", "+254", "+686",
    "+383", "+965", "+996", "+856", "+371", "+961", "+266", "+231",
    "+218", "+423", "+370", "+352", "+853", "+261", "+265", "+60",
    "+960", "+223", "+356", "+692", "+222", "+230", "+262", "+52",
    "+691", "+373", "+377", "+976", "+382", "+1664", "+212", "+258",
    "+95", "+264", "+674", "+977", "+31", "+599", "+687", "+64",
    "+505", "+227", "+234", "+683", "+672", "+389", "+1670", "+47",
    "+968", "+92", "+680", "+970", "+507", "+675", "+595", "+51",
    "+63", "+48", "+351", "+1939", "+974", "+242", "+40",
    "+250", "+290", "+1869", "+1758", "+508",
    "+1784", "+685", "+378", "+239", "+966", "+221", "+381", "+248",
    "+232", "+65", "+1721", "+421", "+386", "+677", "+252", "+27",
    "+82", "+211", "+34", "+94", "+249", "+597", "+268", "+46",
    "+41", "+963", "+886", "+992", "+255", "+66", "+228", "+690",
    "+676", "+1868", "+216", "+90", "+993", "+1649", "+688", "+256",
    "+380", "+971", "+44", "+598", "+998", "+678", "+379",
    "+58", "+84", "+1340", "+681", "+967", "+260", "+263",
]

COUNTRY_NAMES = {
    "+93": "Afghanistan",
    "+355": "Albania",
    "+213": "Algeria",
    "+1684": "American Samoa",
    "+376": "Andorra",
    "+244": "Angola",
    "+1264": "Anguilla",
    "+1268": "Antigua & Barbuda",
    "+54": "Argentina",
    "+374": "Armenia",
    "+297": "Aruba",
    "+61": "Australia",
    "+43": "Austria",
    "+994": "Azerbaijan",
    "+1242": "Bahamas",
    "+973": "Bahrain",
    "+880": "Bangladesh",
    "+1246": "Barbados",
    "+375": "Belarus",
    "+32": "Belgium",
    "+501": "Belize",
    "+229": "Benin",
    "+1441": "Bermuda",
    "+975": "Bhutan",
    "+591": "Bolivia",
    "+387": "Bosnia & Herzegovina",
    "+267": "Botswana",
    "+55": "Brazil",
    "+1284": "British Virgin Islands",
    "+673": "Brunei",
    "+359": "Bulgaria",
    "+226": "Burkina Faso",
    "+257": "Burundi",
    "+855": "Cambodia",
    "+237": "Cameroon",
    "+1": "Canada / USA",
    "+238": "Cape Verde",
    "+1345": "Cayman Islands",
    "+236": "Central African Republic",
    "+235": "Chad",
    "+56": "Chile",
    "+86": "China",
    "+57": "Colombia",
    "+269": "Comoros",
    "+682": "Cook Islands",
    "+506": "Costa Rica",
    "+225": "Côte d'Ivoire",
    "+385": "Croatia",
    "+53": "Cuba",
    "+357": "Cyprus",
    "+420": "Czech Republic",
    "+243": "DR Congo",
    "+45": "Denmark",
    "+253": "Djibouti",
    "+1767": "Dominica",
    "+1809": "Dominican Republic",
    "+670": "East Timor",
    "+593": "Ecuador",
    "+20": "Egypt",
    "+503": "El Salvador",
    "+240": "Equatorial Guinea",
    "+291": "Eritrea",
    "+372": "Estonia",
    "+251": "Ethiopia",
    "+500": "Falkland Islands",
    "+298": "Faroe Islands",
    "+679": "Fiji",
    "+358": "Finland",
    "+33": "France",
    "+594": "French Guiana",
    "+689": "French Polynesia",
    "+241": "Gabon",
    "+220": "Gambia",
    "+995": "Georgia",
    "+49": "Germany",
    "+233": "Ghana",
    "+350": "Gibraltar",
    "+30": "Greece",
    "+1473": "Grenada",
    "+590": "Guadeloupe",
    "+1671": "Guam",
    "+502": "Guatemala",
    "+224": "Guinea",
    "+245": "Guinea-Bissau",
    "+592": "Guyana",
    "+509": "Haiti",
    "+504": "Honduras",
    "+852": "Hong Kong",
    "+36": "Hungary",
    "+354": "Iceland",
    "+91": "India",
    "+62": "Indonesia",
    "+98": "Iran",
    "+964": "Iraq",
    "+353": "Ireland",
    "+972": "Israel",
    "+39": "Italy",
    "+1876": "Jamaica",
    "+81": "Japan",
    "+962": "Jordan",
    "+7": "Kazakhstan / Russia",
    "+254": "Kenya",
    "+686": "Kiribati",
    "+383": "Kosovo",
    "+965": "Kuwait",
    "+996": "Kyrgyzstan",
    "+856": "Laos",
    "+371": "Latvia",
    "+961": "Lebanon",
    "+266": "Lesotho",
    "+231": "Liberia",
    "+218": "Libya",
    "+423": "Liechtenstein",
    "+370": "Lithuania",
    "+352": "Luxembourg",
    "+853": "Macau",
    "+261": "Madagascar",
    "+265": "Malawi",
    "+60": "Malaysia",
    "+960": "Maldives",
    "+223": "Mali",
    "+356": "Malta",
    "+692": "Marshall Islands",
    "+222": "Mauritania",
    "+230": "Mauritius",
    "+262": "Mayotte / Réunion",
    "+52": "Mexico",
    "+691": "Micronesia",
    "+373": "Moldova",
    "+377": "Monaco",
    "+976": "Mongolia",
    "+382": "Montenegro",
    "+1664": "Montserrat",
    "+212": "Morocco",
    "+258": "Mozambique",
    "+95": "Myanmar",
    "+264": "Namibia",
    "+674": "Nauru",
    "+977": "Nepal",
    "+31": "Netherlands",
    "+599": "Netherlands Antilles",
    "+687": "New Caledonia",
    "+64": "New Zealand",
    "+505": "Nicaragua",
    "+227": "Niger",
    "+234": "Nigeria",
    "+683": "Niue",
    "+672": "Norfolk Island",
    "+389": "North Macedonia",
    "+1670": "Northern Mariana Islands",
    "+47": "Norway",
    "+968": "Oman",
    "+92": "Pakistan",
    "+680": "Palau",
    "+970": "Palestine",
    "+507": "Panama",
    "+675": "Papua New Guinea",
    "+595": "Paraguay",
    "+51": "Peru",
    "+63": "Philippines",
    "+48": "Poland",
    "+351": "Portugal",
    "+1939": "Puerto Rico",
    "+974": "Qatar",
    "+242": "Republic of the Congo",
    "+40": "Romania",
    "+250": "Rwanda",
    "+290": "Saint Helena",
    "+1869": "Saint Kitts & Nevis",
    "+1758": "Saint Lucia",
    "+508": "Saint Pierre & Miquelon",
    "+1784": "Saint Vincent & Grenadines",
    "+685": "Samoa",
    "+378": "San Marino",
    "+239": "São Tomé & Príncipe",
    "+966": "Saudi Arabia",
    "+221": "Senegal",
    "+381": "Serbia",
    "+248": "Seychelles",
    "+232": "Sierra Leone",
    "+65": "Singapore",
    "+1721": "Sint Maarten",
    "+421": "Slovakia",
    "+386": "Slovenia",
    "+677": "Solomon Islands",
    "+252": "Somalia",
    "+27": "South Africa",
    "+82": "South Korea",
    "+211": "South Sudan",
    "+34": "Spain",
    "+94": "Sri Lanka",
    "+249": "Sudan",
    "+597": "Suriname",
    "+268": "Eswatini",
    "+46": "Sweden",
    "+41": "Switzerland",
    "+963": "Syria",
    "+886": "Taiwan",
    "+992": "Tajikistan",
    "+255": "Tanzania",
    "+66": "Thailand",
    "+228": "Togo",
    "+690": "Tokelau",
    "+676": "Tonga",
    "+1868": "Trinidad & Tobago",
    "+216": "Tunisia",
    "+90": "Turkey",
    "+993": "Turkmenistan",
    "+1649": "Turks & Caicos Islands",
    "+688": "Tuvalu",
    "+256": "Uganda",
    "+380": "Ukraine",
    "+971": "United Arab Emirates",
    "+44": "United Kingdom",
    "+598": "Uruguay",
    "+998": "Uzbekistan",
    "+678": "Vanuatu",
    "+379": "Vatican City",
    "+58": "Venezuela",
    "+84": "Vietnam",
    "+1340": "US Virgin Islands",
    "+681": "Wallis & Futuna",
    "+967": "Yemen",
    "+260": "Zambia",
    "+263": "Zimbabwe",
}

# ── Group management dialog ───────────────────────────────────────

class GroupDialog(Toplevel):
    """Dialog to add / edit a group with editable role-holder fields."""

    def __init__(self, parent, group_id=None) -> None:
        super().__init__(parent)
        self._group_id = group_id
        self._result = None
        self.title("Edit Group" if group_id else "New Group")
        self.resizable(False, False)

        conn = get_connection()
        self._users = conn.execute(
            "SELECT id, full_name FROM users WHERE active=1 ORDER BY full_name"
        ).fetchall()
        row = conn.execute("SELECT * FROM groups WHERE id=?", (group_id,)).fetchone() if group_id else None
        conn.close()

        self._build_ui(row)
        self.grab_set()
        self.wait_window()

    def _build_ui(self, row) -> None:
        pad = {"padx": 10, "pady": 4}
        frame = ttk.Frame(self, padding=16)
        frame.pack(fill=BOTH, expand=YES)

        # Name
        ttk.Label(frame, text="Level / Group Name *").grid(row=0, column=0, sticky=W, **pad)
        self.name_var = tk.StringVar(value=row[1] if row else "")
        ttk.Entry(frame, textvariable=self.name_var, width=36).grid(
            row=0, column=1, **pad
        )

        # Level
        ttk.Label(frame, text="Level").grid(row=1, column=0, sticky=W, **pad)
        self.level_var = tk.StringVar(value=row[12] if row and len(row) > 12 else "Level 1")
        level_combo = ttk.Combobox(
            frame, textvariable=self.level_var,
            values=["Level 1", "Level 2", "Level 3", "Level 4"], width=34, state="readonly"
        )
        level_combo.grid(row=1, column=1, **pad)

        # Batch
        ttk.Label(frame, text="Batch").grid(row=2, column=0, sticky=W, **pad)
        self.batch_var = tk.StringVar(value=row[13] if row and len(row) > 13 else "Regular")
        batch_combo = ttk.Combobox(
            frame, textvariable=self.batch_var,
            values=["Regular", "Kids"], width=34, state="readonly"
        )
        batch_combo.grid(row=2, column=1, **pad)

        # Role fields — editable combobox (type or pick from existing users)
        # row columns: id, name, bc_id, gc_id, ct_id, ta_id, bc_name, gc_name, ct_name, ta_name, timing, zoom_link, level, batch
        role_keys = ["bc_name", "gc_name", "ct_name", "ta_name"]
        role_labels = [
            "BC (Batch Coordinator)",
            "GC (Group Coordinator)",
            "CT (Co-Teacher)",
            "TA (Teaching Assistant)",
        ]
        self._role_vars = {}
        user_names = [u[1] for u in self._users]
        for i, (label, key) in enumerate(zip(role_labels, role_keys), start=3):
            ttk.Label(frame, text=label).grid(row=i, column=0, sticky=W, **pad)
            # Resolve initial value: prefer bc_name column, fall back to user name from bc_id
            initial = ""
            if row:
                bc_name = row[role_keys.index(key) + 6]
                bc_id = row[role_keys.index(key) + 2]
                initial = bc_name if bc_name else (
                    next((u[1] for u in self._users if u[0] == bc_id), "") if bc_id else ""
                )
            var = tk.StringVar(value=initial)
            self._role_vars[key] = var
            combo = ttk.Combobox(frame, textvariable=var, values=[""] + user_names, width=34)
            combo.grid(row=i, column=1, **pad)

        # Timing
        ttk.Label(frame, text="Class Timing").grid(row=7, column=0, sticky=W, **pad)
        self.timing_var = tk.StringVar(value=row[10] if row else "")
        ttk.Entry(frame, textvariable=self.timing_var, width=36).grid(
            row=7, column=1, **pad
        )

        # Zoom Link
        ttk.Label(frame, text="Zoom Meeting Link").grid(row=8, column=0, sticky=W, **pad)
        self.zoom_var = tk.StringVar(value=row[11] if row else "")
        ttk.Entry(frame, textvariable=self.zoom_var, width=36).grid(
            row=8, column=1, **pad
        )

        # Buttons
        btn_row = ttk.Frame(frame)
        btn_row.grid(row=9, column=0, columnspan=2, pady=(12, 0))

        ttk.Button(btn_row, text="Save", command=self._save, bootstyle=PRIMARY).pack(
            side=LEFT, padx=(0, 8)
        )
        ttk.Button(btn_row, text="Cancel", command=self.destroy, bootstyle=SECONDARY).pack(
            side=LEFT
        )

    def _save(self) -> None:
        name = self.name_var.get().strip()
        level = self.level_var.get().strip()
        batch = self.batch_var.get().strip()
        if not name:
            messagebox.showwarning("Validation", "Group name is required.")
            return
        if not level:
            level = "Level 1"
        if not batch:
            batch = "Regular"
        try:
            save_group(
                self._group_id, name,
                self._role_vars["bc_name"].get().strip(),
                self._role_vars["gc_name"].get().strip(),
                self._role_vars["ct_name"].get().strip(),
                self._role_vars["ta_name"].get().strip(),
                self.timing_var.get().strip(),
                self.zoom_var.get().strip(),
                level, batch,
            )
        except Exception as exc:
            messagebox.showerror("Error", str(exc))
            return
        self._result = "saved"
        self.destroy()


# ── Sadhak Registration ────────────────────────────────────────────

class SadhakRegistrationFrame(ttk.Frame):
    """Form to register / edit a Sadhak with automatic PRN lookup."""

    def __init__(self, parent: ttk.Window, current_user) -> None:
        super().__init__(parent, padding=20)
        self.pack(fill=BOTH, expand=NO)
        self._user = current_user
        self._editing_id: int | None = None

        # --- Name ---
        ttk.Label(self, text="Full Name *", font=("Segoe UI", 10)).grid(
            row=0, column=0, sticky=W, pady=(0, 4)
        )
        self.name_var = tk.StringVar()
        self.name_entry = ttk.Entry(self, textvariable=self.name_var, width=40)
        self.name_entry.grid(row=1, column=0, sticky=EW, pady=(0, 8))

        # --- Phone ---
        ttk.Label(self, text="Mobile Number *", font=("Segoe UI", 10)).grid(
            row=2, column=0, sticky=W, pady=(0, 4)
        )
        phone_frame = ttk.Frame(self)
        phone_frame.grid(row=3, column=0, sticky=EW, pady=(0, 8))
        _country_display = [f"{c} {COUNTRY_NAMES.get(c, '')}" for c in COUNTRY_CODES]
        self.country_code_var = tk.StringVar(
            value=f"{DEFAULT_COUNTRY_CODE} {COUNTRY_NAMES.get(DEFAULT_COUNTRY_CODE, '')}"
        )
        self.cc_combo = ttk.Combobox(
            phone_frame, textvariable=self.country_code_var,
            values=_country_display, width=18, state="readonly",
        )
        self.cc_combo.pack(side=LEFT, padx=(0, 4))
        self.phone_var = tk.StringVar()
        self.phone_var.trace_add("write", self._on_phone_changed)
        self.phone_entry = ttk.Entry(phone_frame, textvariable=self.phone_var)
        self.phone_entry.pack(side=LEFT, fill=X, expand=YES)
        phone_frame.columnconfigure(1, weight=1)

        # --- Email ---
        ttk.Label(self, text="Email", font=("Segoe UI", 10)).grid(
            row=4, column=0, sticky=W, pady=(0, 4)
        )
        self.email_var = tk.StringVar()
        self.email_var.trace_add("write", self._on_email_changed)
        self.email_entry = ttk.Entry(self, textvariable=self.email_var, width=40)
        self.email_entry.grid(row=5, column=0, sticky=EW, pady=(0, 8))

        # --- PRN ---
        ttk.Label(self, text="PRN (auto-searched)", font=("Segoe UI", 10)).grid(
            row=6, column=0, sticky=W, pady=(0, 4)
        )
        self.prn_var = tk.StringVar()
        self.prn_var.trace_add("write", self._on_prn_changed)
        self.prn_entry = ttk.Entry(
            self, textvariable=self.prn_var, width=40
        )
        self.prn_entry.grid(row=7, column=0, sticky=EW, pady=(0, 8))

        # --- Level / Group ---
        ttk.Label(self, text="Group", font=("Segoe UI", 10)).grid(
            row=8, column=0, sticky=W, pady=(0, 4)
        )
        group_row = ttk.Frame(self)
        group_row.grid(row=9, column=0, sticky=EW, pady=(0, 8))
        self.group_var = tk.StringVar()
        self.group_combo = ttk.Combobox(
            group_row, textvariable=self.group_var, width=34, state="readonly"
        )
        self.group_combo.pack(side=LEFT)
        self.group_combo.bind("<<ComboboxSelected>>", self._on_group_selected)
        self.level_display = ttk.Label(group_row, text="", font=("Segoe UI", 9, "bold"), bootstyle=INFO)
        self.level_display.pack(side=LEFT, padx=(6, 0))
        self.batch_display = ttk.Label(group_row, text="", font=("Segoe UI", 9, "bold"), bootstyle=SECONDARY)
        self.batch_display.pack(side=LEFT, padx=(2, 0))
        self.zoom_btn = ttk.Button(
            group_row, text="Zoom", command=self._open_group_zoom, bootstyle=SUCCESS, state=DISABLED
        )
        self.zoom_btn.pack(side=LEFT, padx=(6, 0))

        # --- Group role-holders ---
        self.role_vars = {
            "BC": tk.StringVar(value=""),
            "GC": tk.StringVar(value=""),
            "CT": tk.StringVar(value=""),
            "TA": tk.StringVar(value=""),
        }
        for i, (label, var) in enumerate(self.role_vars.items()):
            ttk.Label(self, text=f"{label}:", font=("Segoe UI", 9)).grid(
                row=10 + i, column=0, sticky=W, padx=(12, 0), pady=(1, 1)
            )
            ttk.Label(self, textvariable=var, font=("Segoe UI", 9, "italic")).grid(
                row=10 + i, column=0, sticky=W, padx=(80, 0), pady=(1, 1)
            )

        # --- Status ---
        self.status_var = tk.StringVar(value="Ready")
        ttk.Label(self, textvariable=self.status_var, font=("Segoe UI", 9)).grid(
            row=14, column=0, sticky=W, pady=(8, 8)
        )

        # --- Buttons row ---
        btn_row = ttk.Frame(self)
        btn_row.grid(row=15, column=0, sticky=W)

        self.save_btn = ttk.Button(
            btn_row, text="Save Sadhak", command=self._save_sadhak, bootstyle=SUCCESS
        )
        self.save_btn.pack(side=LEFT)

        self.cancel_btn = ttk.Button(
            btn_row, text="Cancel", command=self._clear_form, bootstyle=SECONDARY
        )
        self.cancel_btn.pack(side=LEFT, padx=(8, 0))

        self.columnconfigure(0, weight=1)
        self._reload_groups()

    # ── groups ──────────────────────────────────────────────────────

    def _reload_groups(self) -> None:
        groups = get_all_groups()
        self._group_map: dict[str, int] = {g[1]: g[0] for g in groups}
        self.group_combo["values"] = [""] + [f"{g[1]}" for g in groups]
        self.group_var.set("")

    def _on_group_selected(self, *_args) -> None:
        group_id = self._selected_group_id()
        if group_id is None:
            for v in self.role_vars.values():
                v.set("")
            self.zoom_btn.configure(state=DISABLED)
            self.level_display.configure(text="")
            self.batch_display.configure(text="")
            return
        info = get_group_with_names(group_id)
        if info:
            self.role_vars["BC"].set(info.bc_name)
            self.role_vars["GC"].set(info.gc_name)
            self.role_vars["CT"].set(info.ct_name)
            self.role_vars["TA"].set(info.ta_name)
            self.level_display.configure(text=f"[{info.level}]")
            self.batch_display.configure(text=f"[{info.batch}]")
            if info.zoom_link:
                self.zoom_btn.configure(state=NORMAL)
            else:
                self.zoom_btn.configure(state=DISABLED)

    def _open_group_zoom(self) -> None:
        group_id = self._selected_group_id()
        if group_id is None:
            return
        info = get_group_with_names(group_id)
        if info and info.zoom_link:
            webbrowser.open(info.zoom_link)

    def _selected_group_id(self) -> int | None:
        name = self.group_var.get()
        return self._group_map.get(name)

    # ── phone → PRN auto-lookup ──────────────────────────────────────

    def _strip_country_code(self, phone: str) -> str:
        """Remove country-code prefix, returning just the local number.

        Only strips when the number has an explicit international prefix (+ or 00),
        or when the digits match the country code selected in the dropdown.
        This avoids falsely stripping digits like ``98`` from Nepali numbers (e.g. 9846…).
        """
        raw = phone.strip()
        has_international_prefix = raw.startswith("+") or raw.startswith("00")
        digits = "".join(c for c in raw if c.isdigit())

        # Normalise 00… prefix to +… for country-code matching
        if raw.startswith("00"):
            digits = digits[2:]

        # Selected country code from the dropdown
        sel_cc = self.country_code_var.get().split()[0].replace("+", "")
        if sel_cc and digits.startswith(sel_cc) and len(digits) > len(sel_cc):
            return digits[len(sel_cc):]

        # Only try other country codes when an international prefix was typed
        if has_international_prefix:
            codes = sorted(COUNTRY_CODES, key=lambda c: len(c), reverse=True)
            for cc in codes:
                cc_d = cc.replace("+", "")
                if digits.startswith(cc_d) and len(digits) > len(cc_d):
                    return digits[len(cc_d):]

        return digits

    def _on_phone_changed(self, *_args) -> None:
        phone = self._strip_country_code(self.phone_var.get().strip())
        if len(phone) < 7 or not phone.isdigit():
            self.prn_var.set("")
            self.status_var.set("Ready")
            return
        self.status_var.set("Searching PRN…")
        threading.Thread(target=self._lookup_prn, args=(phone,), daemon=True).start()

    def _lookup_prn(self, phone: str) -> None:
        try:
            results = search_prn(phone)
        except Exception as exc:
            self.after(0, self._prn_result, "", "", f"PRN lookup failed: {exc}")
            return
        best_result = _select_best_prn_result(results, phone)
        if not best_result:
            self.after(0, self._prn_result, "", "", "No PRN found for this number")
        elif len(results) == 1:
            self.after(0, self._prn_result, best_result.prn, best_result.name, f"Found: {best_result.name}")
        else:
            self.after(
                0,
                self._prn_result,
                best_result.prn,
                best_result.name,
                f"Multiple matches ({len(results)}), showing best: {best_result.name}",
            )

    def _on_email_changed(self, *_args) -> None:
        email = self.email_var.get().strip()
        if len(email) < 5 or "@" not in email:
            return
        threading.Thread(target=self._lookup_prn_by_email, args=(email,), daemon=True).start()

    def _lookup_prn_by_email(self, email: str) -> None:
        try:
            results = search_prn(email)
        except Exception:
            return
        best_result = _select_best_prn_result(results, email)
        if best_result:
            self.after(0, self._prn_result, best_result.prn, best_result.name, f"Found via email: {best_result.name}")

    def _on_prn_changed(self, *_args) -> None:
        prn = self.prn_var.get().strip()
        if len(prn) < 2:
            return
        threading.Thread(target=self._lookup_name_by_prn, args=(prn,), daemon=True).start()

    def _lookup_name_by_prn(self, prn: str) -> None:
        try:
            results = search_by_prn(prn)
        except Exception:
            return
        best_result = _select_best_prn_result(results, prn)
        if best_result and not self.name_var.get().strip():
            self.after(0, self._prn_result, "", best_result.name, f"Found: {best_result.name}")

    def _prn_result(self, prn: str, name: str, status: str) -> None:
        if prn:
            self.prn_var.set(prn)
        if name:
            self.name_var.set(name)
        self.status_var.set(status)

    # ── save / update ────────────────────────────────────────────────

    def _save_sadhak(self) -> None:
        name = self.name_var.get().strip()
        phone = self.phone_var.get().strip()
        email = self.email_var.get().strip()
        prn = self.prn_var.get().strip()
        group_id = self._selected_group_id()

        if not name or not phone:
            messagebox.showwarning("Validation", "Name and Mobile Number are required.")
            return

        # Prepend country code if not already present
        if not phone.startswith("+"):
            phone = self.country_code_var.get().split()[0] + phone

        if self._editing_id is not None and not can_edit_sadhak(self._user.id, self._editing_id):
            messagebox.showerror(
                "Access Denied",
                "You can only edit sadhaks in groups where you are\n"
                "assigned as BC, GC, CT, or TA.",
            )
            return

        # Snapshot role-holder names from the selected group
        bc_name = gc_name = ct_name = ta_name = None
        if group_id:
            info = get_group_with_names(group_id)
            if info:
                bc_name = info.bc_name
                gc_name = info.gc_name
                ct_name = info.ct_name
                ta_name = info.ta_name

        try:
            conn = get_connection()
            group_name = self.group_var.get() or None
            if self._editing_id is not None:
                conn.execute(
                    """UPDATE sadhak
                       SET name=?, phone=?, email=?, prn=?, group_id=?,
                           bc_name=?, gc_name=?, ct_name=?, ta_name=?,
                           updated_by=?, updated_at=datetime('now','localtime')
                       WHERE id=?""",
                    (name, phone, email or None, prn or None, group_id,
                     bc_name, gc_name, ct_name, ta_name,
                     self._user.id, self._editing_id),
                )
                sadhak_id = self._editing_id
                msg = f"Updated: {name}"
            else:
                cur = conn.execute(
                    "INSERT INTO sadhak (name, phone, email, prn, group_id, "
                    "bc_name, gc_name, ct_name, ta_name, created_by, updated_by) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (name, phone, email or None, prn or None, group_id,
                     bc_name, gc_name, ct_name, ta_name,
                     self._user.id, self._user.id),
                )
                sadhak_id = cur.lastrowid
                msg = f"Saved: {name}"

            conn.execute(
                "INSERT INTO sadhak_history (sadhak_id, group_id, group_name, "
                "bc_name, gc_name, ct_name, ta_name, changed_by) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (sadhak_id, group_id, group_name,
                 bc_name, gc_name, ct_name, ta_name, self._user.id),
            )

            conn.commit()
            conn.close()
            backup_to_drive()
        except Exception as exc:
            messagebox.showerror("Database Error", str(exc))
            return

        self.status_var.set(msg)
        self._clear_form()
        app = self.master
        if hasattr(app, "refresh_sadhak_list"):
            app.refresh_sadhak_list()

    def _clear_form(self) -> None:
        self._editing_id = None
        self.name_var.set("")
        self.country_code_var.set(f"{DEFAULT_COUNTRY_CODE} {COUNTRY_NAMES.get(DEFAULT_COUNTRY_CODE, '')}")
        self.phone_var.set("")
        self.email_var.set("")
        self.prn_var.set("")
        self.group_var.set("")
        for v in self.role_vars.values():
            v.set("")
        self.save_btn.configure(text="Save Sadhak")
        self.status_var.set("Ready")
        self.name_entry.focus()

    def load_sadhak(self, record: tuple) -> None:
        """Populate the form with an existing record for editing."""
        sid, name, phone, email, prn, group_name, *_ = record
        self._editing_id = sid
        self.name_var.set(name)
        # Strip known country code for display
        display_phone = phone
        matched_code = DEFAULT_COUNTRY_CODE
        for code in COUNTRY_CODES:
            if phone.startswith(code):
                display_phone = phone[len(code):]
                matched_code = code
                break
        self.country_code_var.set(f"{matched_code} {COUNTRY_NAMES.get(matched_code, '')}")
        self.phone_var.set(display_phone)
        self.email_var.set(email or "")
        self.prn_var.set(prn or "")
        if group_name and group_name != "—":
            self.group_var.set(group_name)
            self._on_group_selected()
        self.save_btn.configure(text="Update Sadhak")
        self.status_var.set("Editing…")


# ── Sadhak List ──────────────────────────────────────────────────────

class SadhakListFrame(ttk.Frame):
    """Displays all saved Sadhak records in a table with audit info."""

    def __init__(self, parent: ttk.Window, current_user) -> None:
        super().__init__(parent, padding=(20, 0, 20, 20))
        self.pack(fill=BOTH, expand=YES)
        self._user = current_user

        # --- filter bar ---
        filter_bar = ttk.Frame(self)
        filter_bar.pack(fill=X, pady=(0, 6))

        ttk.Label(filter_bar, text="Search:", font=("Segoe UI", 9)).pack(
            side=LEFT, padx=(0, 4)
        )
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *_: self._load_sadhaks())
        ttk.Entry(filter_bar, textvariable=self.search_var, width=24).pack(
            side=LEFT, padx=(0, 12)
        )

        ttk.Label(filter_bar, text="Group:", font=("Segoe UI", 9)).pack(
            side=LEFT, padx=(0, 4)
        )
        self.filter_group_var = tk.StringVar()
        self.filter_group_combo = ttk.Combobox(
            filter_bar, textvariable=self.filter_group_var, width=20, state="readonly"
        )
        self.filter_group_combo.pack(side=LEFT, padx=(0, 12))
        self.filter_group_combo.bind("<<ComboboxSelected>>", lambda *_: self._load_sadhaks())

        self.clear_filter_btn = ttk.Button(
            filter_bar, text="Clear", command=self._clear_filters, bootstyle=SECONDARY
        )
        self.clear_filter_btn.pack(side=LEFT)

        self._load_filter_groups()

        # --- toolbar ---
        toolbar = ttk.Frame(self)
        toolbar.pack(fill=X, pady=(0, 8))

        ttk.Label(toolbar, text="Saved Sadhak Records", font=("Segoe UI", 11)).pack(
            side=LEFT
        )
        self.total_label = ttk.Label(toolbar, text="", font=("Segoe UI", 10))
        self.total_label.pack(side=LEFT, padx=(8, 0))

        self.history_btn = ttk.Button(
            toolbar, text="History", command=self._show_history, bootstyle=SECONDARY
        )
        self.history_btn.pack(side=RIGHT, padx=(4, 0))
        self.whatsapp_btn = ttk.Button(
            toolbar, text="WhatsApp", command=self._whatsapp_selected, bootstyle=SUCCESS
        )
        self.whatsapp_btn.pack(side=RIGHT, padx=(4, 0))
        self.edit_btn = ttk.Button(
            toolbar, text="Edit", command=self._edit_selected, bootstyle=INFO
        )
        self.edit_btn.pack(side=RIGHT, padx=(4, 0))
        self.delete_btn = ttk.Button(
            toolbar, text="Delete", command=self._delete_selected, bootstyle=DANGER
        )
        self.delete_btn.pack(side=RIGHT, padx=(4, 0))
        self.refresh_btn = ttk.Button(
            toolbar, text="Refresh", command=self._load_sadhaks, bootstyle=SECONDARY
        )
        self.refresh_btn.pack(side=RIGHT, padx=(4, 0))

        # --- treeview ---
        columns = (
            "name", "phone", "email", "prn", "group_name",
            "level", "batch", "bc_name", "gc_name", "ct_name", "ta_name",
            "created_at", "updated_at",
            "created_by_name", "updated_by_name",
        )
        self.tree = ttk.Treeview(
            self, columns=columns, show="headings", bootstyle=INFO, height=10
        )
        self.tree.heading("name", text="Name")
        self.tree.heading("phone", text="Phone")
        self.tree.heading("email", text="Email")
        self.tree.heading("prn", text="PRN")
        self.tree.heading("group_name", text="Group")
        self.tree.heading("level", text="Level")
        self.tree.heading("batch", text="Batch")
        self.tree.heading("bc_name", text="BC")
        self.tree.heading("gc_name", text="GC")
        self.tree.heading("ct_name", text="CT")
        self.tree.heading("ta_name", text="TA")
        self.tree.heading("created_at", text="Created At")
        self.tree.heading("updated_at", text="Updated At")
        self.tree.heading("created_by_name", text="Created By")
        self.tree.heading("updated_by_name", text="Last Updated By")

        self.tree.column("name", width=140)
        self.tree.column("phone", width=100)
        self.tree.column("email", width=140)
        self.tree.column("prn", width=70, anchor=CENTER)
        self.tree.column("group_name", width=110)
        self.tree.column("level", width=70, anchor=CENTER)
        self.tree.column("batch", width=60, anchor=CENTER)
        self.tree.column("bc_name", width=110)
        self.tree.column("gc_name", width=110)
        self.tree.column("ct_name", width=110)
        self.tree.column("ta_name", width=110)
        self.tree.column("created_at", width=140)
        self.tree.column("updated_at", width=140)
        self.tree.column("created_by_name", width=100)
        self.tree.column("updated_by_name", width=100)

        scrollbar = ttk.Scrollbar(self, orient=VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side=LEFT, fill=BOTH, expand=YES)
        scrollbar.pack(side=RIGHT, fill=Y)

        self._load_sadhaks()

    def _get_selected(self) -> tuple | None:
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("No Selection", "Please select a record first.")
            return None
        sid = int(sel[0])
        values = self.tree.item(sel[0], "values")
        return (sid, *values)

    def _edit_selected(self) -> None:
        values = self._get_selected()
        if values is None:
            return
        sid = values[0]
        if not can_edit_sadhak(self._user.id, sid):
            messagebox.showerror(
                "Access Denied",
                "You can only edit sadhaks in groups where you are\n"
                "assigned as BC, GC, CT, or TA.",
            )
            return
        app = self.master
        if hasattr(app, "reg_frame"):
            app.reg_frame.load_sadhak(values)

    def _delete_selected(self) -> None:
        if self._user.role != "Admin":
            messagebox.showerror("Access Denied", "Only Admin can delete records.")
            return
        values = self._get_selected()
        if values is None:
            return
        sid, name = values[0], values[1]
        ok = messagebox.askyesno("Confirm Delete", f"Delete Sadhak '{name}' (ID {sid})?")
        if not ok:
            return
        try:
            conn = get_connection()
            conn.execute("DELETE FROM sadhak WHERE id=?", (sid,))
            conn.commit()
            conn.close()
            backup_to_drive()
        except Exception as exc:
            messagebox.showerror("Database Error", str(exc))
            return
        self._load_sadhaks()

    def _show_history(self) -> None:
        values = self._get_selected()
        if values is None:
            return
        sid, name = values[0], values[1]
        rows = get_history(int(sid))
        if not rows:
            messagebox.showinfo("History", f"No history yet for '{name}'.")
            return

        win = Toplevel(self.master)
        win.title(f"History – {name}")
        win.geometry("750x400")
        win.transient(self.master)
        win.grab_set()

        frame = ttk.Frame(win, padding=12)
        frame.pack(fill=BOTH, expand=YES)

        cols = ("#", "Group", "Level", "Batch", "BC", "GC", "CT", "TA", "Changed By", "Date")
        tree = ttk.Treeview(frame, columns=cols, show="headings", bootstyle=INFO)
        for c in cols:
            tree.heading(c, text=c)
        tree.column("#", width=30, anchor=CENTER)
        tree.column("Group", width=100)
        tree.column("Level", width=70, anchor=CENTER)
        tree.column("Batch", width=60, anchor=CENTER)
        tree.column("BC", width=110)
        tree.column("GC", width=110)
        tree.column("CT", width=110)
        tree.column("TA", width=110)
        tree.column("Changed By", width=100)
        tree.column("Date", width=140)

        scroll = ttk.Scrollbar(frame, orient=VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scroll.set)
        tree.pack(side=LEFT, fill=BOTH, expand=YES)
        scroll.pack(side=RIGHT, fill=Y)

        for r in rows:
            tree.insert("", END, values=r)

        ttk.Button(win, text="Close", command=win.destroy).pack(pady=(8, 0))

    def _clear_filters(self) -> None:
        self.search_var.set("")
        self.filter_group_var.set("")
        self._load_sadhaks()

    def _load_filter_groups(self) -> None:
        groups = get_all_groups()
        self._filter_group_map: dict[str, int] = {g[1]: g[0] for g in groups}
        self.filter_group_combo["values"] = [""] + [g[1] for g in groups]
        self.filter_group_var.set("")

    def _whatsapp_selected(self) -> None:
        values = self._get_selected()
        if values is None:
            return
        phone = values[2]
        if not phone:
            messagebox.showinfo("No Phone", "Selected record has no phone number.")
            return
        # Ensure country code is present for WhatsApp international format
        if not phone.startswith("+"):
            phone = DEFAULT_COUNTRY_CODE + phone
        clean = "".join(c for c in phone if c.isdigit())
        if not clean:
            messagebox.showinfo("Invalid Phone", "Phone number is not valid.")
            return
        webbrowser.open(f"https://wa.me/{clean}")

    def _get_total_count(self) -> int:
        try:
            conn = get_connection()
            row = conn.execute("SELECT COUNT(*) FROM sadhak").fetchone()
            conn.close()
            return row[0] if row else 0
        except Exception:
            return 0

    def _load_sadhaks(self) -> None:
        for row in self.tree.get_children():
            self.tree.delete(row)

        keyword = self.search_var.get().strip()
        group_id = self._filter_group_map.get(self.filter_group_var.get())

        conditions = []
        params = []

        if keyword:
            conditions.append(
                "(s.name LIKE ? OR s.phone LIKE ? OR s.email LIKE ? OR s.prn LIKE ?)"
            )
            like = f"%{keyword}%"
            params.extend([like, like, like, like])

        if group_id:
            conditions.append("s.group_id = ?")
            params.append(group_id)

        where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""

        try:
            conn = get_connection()
            rows = conn.execute(f"""
                SELECT s.id, s.name, s.phone, s.email, s.prn,
                       COALESCE(g.name, '—') AS group_name,
                       COALESCE(g.level, 'Level 1') AS level,
                       COALESCE(g.batch, 'Regular') AS batch,
                       COALESCE(s.bc_name, '—') AS bc_name,
                       COALESCE(s.gc_name, '—') AS gc_name,
                       COALESCE(s.ct_name, '—') AS ct_name,
                       COALESCE(s.ta_name, '—') AS ta_name,
                       COALESCE(s.created_at, '—') AS created_at,
                       COALESCE(s.updated_at, '—') AS updated_at,
                       COALESCE(c.full_name, '—') AS created_by_name,
                       COALESCE(u.full_name, '—') AS updated_by_name
                FROM sadhak s
                LEFT JOIN groups g ON g.id = s.group_id
                LEFT JOIN users c ON c.id = s.created_by
                LEFT JOIN users u ON u.id = s.updated_by
                {where_clause}
                ORDER BY s.id DESC
            """, params).fetchall()
            conn.close()
        except Exception as exc:
            messagebox.showerror("Database Error", str(exc))
            return
        for row in rows:
            self.tree.insert("", END, iid=str(row[0]), values=row[1:])

        total = self._get_total_count()
        showing = len(rows)
        if keyword or group_id:
            self.total_label.config(text=f"({showing} of {total})")
        else:
            self.total_label.config(text=f"({total})")


# ── Dashboard ────────────────────────────────────────────────────────

class DashboardFrame(ttk.Frame):
    """Post-login dashboard – packed into the root window."""

    def __init__(self, parent: ttk.Window, user, on_logout) -> None:
        super().__init__(parent)
        self.user = user
        self._on_logout = on_logout

        # Header
        header = ttk.Frame(self, padding=(20, 12, 20, 8))
        header.pack(fill=X)

        ttk.Label(
            header,
            text=f"Welcome, {self.user.full_name}",
            font=("Segoe UI", 14, "bold"),
        ).pack(side=LEFT)

        if self.user.role == "Admin":
            self.mgmt_btn = ttk.Button(
                header,
                text="Manage Groups",
                command=self._open_group_manager,
                bootstyle=SECONDARY,
            )
            self.mgmt_btn.pack(side=RIGHT, padx=(8, 0))

            self.sync_btn = ttk.Button(
                header,
                text="Sync from Web",
                command=self._sync_from_web,
                bootstyle=INFO,
            )
            self.sync_btn.pack(side=RIGHT, padx=(8, 0))

        self.logout_btn = ttk.Button(
            header, text="Logout", command=self._do_logout, bootstyle=DANGER
        )
        self.logout_btn.pack(side=RIGHT)

        role_label = ttk.Label(
            header,
            text=f"Role: {self.user.role}",
            font=("Segoe UI", 10),
            bootstyle=INFO,
        )
        role_label.pack(side=RIGHT, padx=(0, 12))

        ttk.Separator(self, orient=HORIZONTAL).pack(fill=X, pady=(4, 0))

        # Content
        self.reg_frame = SadhakRegistrationFrame(self, current_user=user)
        self.list_frame = SadhakListFrame(self, current_user=user)

        self.pack(fill=BOTH, expand=YES)

    def refresh_sadhak_list(self) -> None:
        self.list_frame._load_filter_groups()
        self.list_frame._load_sadhaks()

    def _open_group_manager(self) -> None:
        win = Toplevel(self)
        win.title("Manage Groups / Levels")
        win.geometry("800x500")
        win.transient(self)
        win.grab_set()

        frame = ttk.Frame(win, padding=12)
        frame.pack(fill=BOTH, expand=YES)

        # Treeview of groups
        columns = ("name", "level", "batch", "timing", "bc", "gc", "ct", "ta", "zoom")
        tree = ttk.Treeview(frame, columns=columns, show="headings", bootstyle=INFO)
        tree.heading("name", text="Group")
        tree.heading("level", text="Level")
        tree.heading("batch", text="Batch")
        tree.heading("timing", text="Timing")
        tree.heading("bc", text="BC")
        tree.heading("gc", text="GC")
        tree.heading("ct", text="CT")
        tree.heading("ta", text="TA")
        tree.heading("zoom", text="Zoom Link")
        tree.column("name", width=130)
        tree.column("level", width=65, anchor=CENTER)
        tree.column("batch", width=60, anchor=CENTER)
        tree.column("timing", width=90)
        tree.column("bc", width=120)
        tree.column("gc", width=120)
        tree.column("ct", width=120)
        tree.column("ta", width=120)
        tree.column("zoom", width=180)

        scroll = ttk.Scrollbar(frame, orient=VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scroll.set)
        tree.pack(side=LEFT, fill=BOTH, expand=YES)
        scroll.pack(side=RIGHT, fill=Y)

        def load():
            for r in tree.get_children():
                tree.delete(r)
            conn = get_connection()
            rows = conn.execute("""
                SELECT g.id, g.name,
                       COALESCE(g.level, 'Level 1') AS level,
                       COALESCE(g.batch, 'Regular') AS batch,
                       COALESCE(g.timing, '') AS timing,
                       COALESCE(NULLIF(g.bc_name, ''), '—'),
                       COALESCE(NULLIF(g.gc_name, ''), '—'),
                       COALESCE(NULLIF(g.ct_name, ''), '—'),
                       COALESCE(NULLIF(g.ta_name, ''), '—'),
                       COALESCE(g.zoom_link, '') AS zoom_link
                FROM groups g
                ORDER BY g.name
            """).fetchall()
            conn.close()
            for r in rows:
                tree.insert("", END, iid=str(r[0]), values=r[1:])

        load()

        btn_row = ttk.Frame(win, padding=(12, 6))
        btn_row.pack(fill=X)

        def add():
            GroupDialog(win)
            load()
            self.reg_frame._reload_groups()

        def edit():
            sel = tree.selection()
            if not sel:
                messagebox.showinfo("No Selection", "Select a group first.")
                return
            gid = int(sel[0])
            GroupDialog(win, group_id=gid)
            load()
            self.reg_frame._reload_groups()

        def delete():
            if self.user.role != "Admin":
                messagebox.showerror("Access Denied", "Only Admin can delete.")
                return
            sel = tree.selection()
            if not sel:
                return
            gid = int(sel[0])
            gname = tree.item(sel[0], "values")[0]
            ok = messagebox.askyesno("Confirm", f"Delete group '{gname}'?")
            if not ok:
                return
            delete_group(gid)
            load()
            self.reg_frame._reload_groups()

        def open_zoom():
            sel = tree.selection()
            if not sel:
                messagebox.showinfo("No Selection", "Select a group first.")
                return
            zoom_link = tree.item(sel[0], "values")[8]  # zoom column
            if not zoom_link:
                messagebox.showinfo("No Link", "No Zoom link set for this group.")
                return
            webbrowser.open(zoom_link)

        ttk.Button(btn_row, text="Add Group", command=add, bootstyle=PRIMARY).pack(
            side=LEFT, padx=(0, 6)
        )
        ttk.Button(btn_row, text="Edit", command=edit, bootstyle=INFO).pack(
            side=LEFT, padx=(0, 6)
        )
        ttk.Button(btn_row, text="Delete", command=delete, bootstyle=DANGER).pack(
            side=LEFT, padx=(0, 6)
        )
        ttk.Button(btn_row, text="Open Zoom", command=open_zoom, bootstyle=SUCCESS).pack(
            side=LEFT, padx=(6, 0)
        )
        ttk.Button(btn_row, text="Close", command=win.destroy, bootstyle=SECONDARY).pack(
            side=RIGHT
        )

    def _sync_from_web(self) -> None:
        from tkinter.simpledialog import askstring
        url = askstring("Sync DB from Web", "Enter web app URL (e.g. https://yourname.pythonanywhere.com):", parent=self)
        if not url:
            return
        import tempfile
        import urllib.request
        import http.cookiejar
        dest = Path(__file__).resolve().parent.parent / "data" / "crm.db"
        cj = http.cookiejar.CookieJar()
        opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(cj),
        )
        opener.addheaders = [("User-Agent", "GeetaPariwarCRM")]
        try:
            username = askstring("Login", "Username:", parent=self)
            if not username:
                return
            password = askstring("Login", "Password:", parent=self, show="*")
            if not password:
                return
            import urllib.parse
            data = urllib.parse.urlencode({"username": username, "password": password}).encode()
            login_url = url.rstrip("/") + "/login"
            resp = opener.open(login_url, data=data, timeout=15)
            if resp.getcode() != 200:
                messagebox.showerror("Sync Failed", "Login failed. Check credentials.")
                return
            download_url = url.rstrip("/") + "/api/backup/download"
            db_data = opener.open(download_url, timeout=30).read()
            backup = dest.with_suffix(".db.bak")
            if dest.exists():
                import shutil
                shutil.copy2(str(dest), str(backup))
            dest.parent.mkdir(parents=True, exist_ok=True)
            with open(str(dest), "wb") as f:
                f.write(db_data)
            messagebox.showinfo("Sync Complete", f"Database downloaded from web.\nLocal backup saved as {backup.name}\n\nRestart the app for changes to take effect.")
        except Exception as exc:
            messagebox.showerror("Sync Failed", str(exc))

    def _do_logout(self) -> None:
        ok = messagebox.askyesno("Logout", "Are you sure you want to logout?")
        if not ok:
            return
        self._on_logout()

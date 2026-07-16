import functools
import json
import hashlib
import logging
import os
import sqlite3
from pathlib import Path
from typing import Optional

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)

from flask import (
    Flask, render_template, request, redirect,
    url_for, session, jsonify, abort, send_file,
)
from database import get_connection, initialize_database
from services.auth_service import authenticate, seed_admin, User
from services.backup_service import backup_to_drive
from services.group_service import (
    get_all_groups, get_group_with_names, save_group,
    delete_group, get_history, can_edit_sadhak,
)
from services.prn_service import search_prn, search_by_prn

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "geeta-pariwar-sadhak-crm-secret-key-change-in-production")

initialize_database()
seed_admin()


def login_required(f):
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return wrapper


def _session_user() -> Optional[dict]:
    if "user_id" not in session:
        return None
    return {
        "id": session["user_id"],
        "full_name": session["user_full_name"],
        "username": session["user_username"],
        "role": session["user_role"],
    }


def _get_groups_for_dropdown():
    return [{"id": g[0], "name": g[1], "level": g[2], "batch": g[3]} for g in get_all_groups()]


def _get_users_for_combo():
    conn = get_connection()
    users = conn.execute(
        "SELECT id, full_name FROM users WHERE active=1 ORDER BY full_name"
    ).fetchall()
    conn.close()
    return [u[1] for u in users]


def _get_filter_groups():
    groups = get_all_groups()
    return [{"id": g[0], "name": g[1], "level": g[2], "batch": g[3]} for g in groups]


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


# ── Auth ─────────────────────────────────────────────────────────────

@app.route("/")
def login():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return render_template("login.html")


@app.route("/login", methods=["POST"])
def do_login():
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")
    user = authenticate(username, password)
    if user is None:
        return render_template("login.html", error="Invalid username or password.")
    session["user_id"] = user.id
    session["user_full_name"] = user.full_name
    session["user_username"] = user.username
    session["user_role"] = user.role
    return redirect(url_for("dashboard"))


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ── Dashboard ────────────────────────────────────────────────────────

@app.route("/dashboard")
@login_required
def dashboard():
    user = _session_user()
    groups = _get_groups_for_dropdown()
    users_combo = _get_users_for_combo() if user["role"] == "Admin" else []
    filter_groups = _get_filter_groups()
    return render_template(
        "dashboard.html",
        user=user,
        groups=groups,
        users_combo=users_combo,
        filter_groups=filter_groups,
        country_codes=COUNTRY_CODES,
        country_names=COUNTRY_NAMES,
        default_code=DEFAULT_COUNTRY_CODE,
    )


# ── Sadhak CRUD ──────────────────────────────────────────────────────

@app.route("/api/sadhaks")
@login_required
def list_sadhaks():
    keyword = request.args.get("search", "").strip()
    group_id = request.args.get("group_id", "").strip()
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
        params.append(int(group_id))
    where = " WHERE " + " AND ".join(conditions) if conditions else ""
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
        {where}
        ORDER BY s.id DESC
    """, params).fetchall()
    total = conn.execute("SELECT COUNT(*) FROM sadhak").fetchone()[0]
    conn.close()
    records = []
    for r in rows:
        records.append({
            "id": r[0], "name": r[1], "phone": r[2], "email": r[3],
            "prn": r[4], "group_name": r[5], "level": r[6], "batch": r[7],
            "bc_name": r[8], "gc_name": r[9], "ct_name": r[10], "ta_name": r[11],
            "created_at": r[12], "updated_at": r[13],
            "created_by_name": r[14], "updated_by_name": r[15],
        })
    return jsonify({"records": records, "total": total, "showing": len(records)})


@app.route("/api/sadhak/<int:sadhak_id>")
@login_required
def get_sadhak(sadhak_id):
    conn = get_connection()
    row = conn.execute("""
        SELECT s.id, s.name, s.phone, s.email, s.prn,
               COALESCE(g.name, '') AS group_name, s.group_id
        FROM sadhak s
        LEFT JOIN groups g ON g.id = s.group_id
        WHERE s.id = ?
    """, (sadhak_id,)).fetchone()
    conn.close()
    if row is None:
        return jsonify({"error": "Not found"}), 404
    return jsonify({
        "id": row[0], "name": row[1], "phone": row[2],
        "email": row[3] or "", "prn": row[4] or "",
        "group_name": row[5], "group_id": row[6],
    })


@app.route("/api/sadhak", methods=["POST"])
@login_required
def save_sadhak():
    user = _session_user()
    data = request.get_json()
    name = data.get("name", "").strip()
    phone = data.get("phone", "").strip()
    email = data.get("email", "").strip()
    prn = data.get("prn", "").strip()
    group_id = data.get("group_id")
    editing_id = data.get("editing_id")
    if not name or not phone:
        return jsonify({"error": "Name and Mobile Number are required."}), 400
    if not phone.startswith("+"):
        phone = (data.get("country_code", DEFAULT_COUNTRY_CODE)) + phone
    if editing_id:
        if not can_edit_sadhak(user["id"], editing_id):
            return jsonify({"error": "Access denied. You can only edit sadhaks in your groups."}), 403
    bc_name = gc_name = ct_name = ta_name = None
    group_name = None
    if group_id:
        info = get_group_with_names(group_id)
        if info:
            bc_name = info.bc_name
            gc_name = info.gc_name
            ct_name = info.ct_name
            ta_name = info.ta_name
            group_name = info.name
    try:
        conn = get_connection()
        if editing_id:
            conn.execute(
                """UPDATE sadhak SET name=?, phone=?, email=?, prn=?, group_id=?,
                   bc_name=?, gc_name=?, ct_name=?, ta_name=?,
                   updated_by=?, updated_at=datetime('now','localtime')
                   WHERE id=?""",
                (name, phone, email or None, prn or None, group_id,
                 bc_name, gc_name, ct_name, ta_name,
                 user["id"], editing_id),
            )
            sadhak_id = editing_id
        else:
            cur = conn.execute(
                "INSERT INTO sadhak (name, phone, email, prn, group_id, "
                "bc_name, gc_name, ct_name, ta_name, created_by, updated_by) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (name, phone, email or None, prn or None, group_id,
                 bc_name, gc_name, ct_name, ta_name,
                 user["id"], user["id"]),
            )
            sadhak_id = cur.lastrowid
        conn.execute(
            "INSERT INTO sadhak_history (sadhak_id, group_id, group_name, "
            "bc_name, gc_name, ct_name, ta_name, changed_by) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (sadhak_id, group_id, group_name,
             bc_name, gc_name, ct_name, ta_name, user["id"]),
        )
        conn.commit()
        conn.close()
        backup_to_drive()
        return jsonify({"success": True, "id": sadhak_id, "message": f"Saved: {name}"})
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@app.route("/api/sadhak/<int:sadhak_id>", methods=["DELETE"])
@login_required
def delete_sadhak(sadhak_id):
    user = _session_user()
    if user["role"] != "Admin":
        return jsonify({"error": "Only Admin can delete records."}), 403
    try:
        conn = get_connection()
        conn.execute("DELETE FROM sadhak WHERE id=?", (sadhak_id,))
        conn.commit()
        conn.close()
        backup_to_drive()
        return jsonify({"success": True})
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@app.route("/api/sadhak/<int:sadhak_id>/history")
@login_required
def sadhak_history(sadhak_id):
    rows = get_history(sadhak_id)
    history = []
    for r in rows:
        history.append({
            "id": r[0], "group_name": r[1], "level": r[2], "batch": r[3],
            "bc_name": r[4], "gc_name": r[5], "ct_name": r[6],
            "ta_name": r[7], "changed_by": r[8], "changed_at": r[9],
        })
    return jsonify(history)


# ── PRN Lookup ───────────────────────────────────────────────────────

@app.route("/api/prn/<phone>")
@login_required
def prn_lookup(phone):
    log.debug("prn_lookup called with phone=%s args=%s", phone, request.args)
    try:
        results = search_prn(phone)
    except Exception as exc:
        log.error("prn_lookup error for phone=%s: %s", phone, exc)
        return jsonify({"error": str(exc)}), 500
    log.debug("prn_lookup results for phone=%s: %s", phone, results)
    return jsonify([{"prn": r.prn, "name": r.name, "phone": r.phone, "email": r.email} for r in results])


@app.route("/api/prn-by-prn/<prn>")
@login_required
def prn_lookup_by_prn(prn):
    log.debug("prn_lookup_by_prn called with prn=%s", prn)
    try:
        results = search_by_prn(prn)
    except Exception as exc:
        log.error("prn_lookup_by_prn error for prn=%s: %s", prn, exc)
        return jsonify({"error": str(exc)}), 500
    log.debug("prn_lookup_by_prn results for prn=%s: %s", prn, results)
    return jsonify([{"prn": r.prn, "name": r.name, "phone": r.phone, "email": r.email} for r in results])


# ── Groups CRUD ──────────────────────────────────────────────────────

@app.route("/api/groups")
@login_required
def list_groups():
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
    groups = []
    for r in rows:
        groups.append({
            "id": r[0], "name": r[1], "level": r[2], "batch": r[3], "timing": r[4],
            "bc_name": r[5], "gc_name": r[6], "ct_name": r[7],
            "ta_name": r[8], "zoom_link": r[9],
        })
    return jsonify(groups)


@app.route("/api/group/<int:group_id>")
@login_required
def get_group(group_id):
    info = get_group_with_names(group_id)
    if info is None:
        return jsonify({"error": "Not found"}), 404
    return jsonify({
        "id": info.id, "name": info.name, "level": info.level,
        "batch": info.batch,
        "bc_name": info.bc_name, "gc_name": info.gc_name,
        "ct_name": info.ct_name, "ta_name": info.ta_name,
        "timing": info.timing, "zoom_link": info.zoom_link,
    })


@app.route("/api/group", methods=["POST"])
@login_required
def create_update_group():
    user = _session_user()
    if user["role"] != "Admin":
        return jsonify({"error": "Only Admin can manage groups."}), 403
    data = request.get_json()
    group_id = data.get("id")
    name = data.get("name", "").strip()
    if not name:
        return jsonify({"error": "Group name is required."}), 400
    try:
        save_group(
            group_id, name,
            data.get("bc_name", "").strip(),
            data.get("gc_name", "").strip(),
            data.get("ct_name", "").strip(),
            data.get("ta_name", "").strip(),
            data.get("timing", "").strip(),
            data.get("zoom_link", "").strip(),
            data.get("level", "Level 1").strip(),
            data.get("batch", "Regular").strip(),
        )
        return jsonify({"success": True})
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@app.route("/api/group/<int:group_id>", methods=["DELETE"])
@login_required
def remove_group(group_id):
    user = _session_user()
    if user["role"] != "Admin":
        return jsonify({"error": "Only Admin can delete groups."}), 403
    try:
        delete_group(group_id)
        return jsonify({"success": True})
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


# ── Users (for combo) ────────────────────────────────────────────────

@app.route("/api/users")
@login_required
def list_users():
    users = _get_users_for_combo()
    return jsonify(users)


# ── Backup / Sync ───────────────────────────────────────────────────

@app.route("/api/backup/download")
@login_required
def download_backup():
    user = _session_user()
    if user["role"] != "Admin":
        abort(403)
    from config import DATABASE_PATH
    return send_file(str(DATABASE_PATH), as_attachment=True, download_name="crm.db")


@app.route("/api/backup/upload", methods=["POST"])
@login_required
def upload_backup():
    user = _session_user()
    if user["role"] != "Admin":
        return jsonify({"error": "Only Admin can restore database."}), 403
    if "file" not in request.files:
        return jsonify({"error": "No file provided."}), 400
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No file selected."}), 400
    if not file.filename.endswith(".db"):
        return jsonify({"error": "File must be a .db file."}), 400

    from config import DATABASE_PATH
    import shutil, tempfile

    tmp = Path(tempfile.mktemp(suffix=".db"))
    try:
        file.save(str(tmp))
        with sqlite3.connect(str(tmp)) as check:
            check.execute("SELECT COUNT(*) FROM sqlite_master")
    except Exception:
        tmp.unlink(missing_ok=True)
        return jsonify({"error": "Uploaded file is not a valid SQLite database."}), 400

    try:
        if DATABASE_PATH.exists():
            bak = DATABASE_PATH.with_suffix(".db.bak")
            shutil.copy2(str(DATABASE_PATH), str(bak))
        shutil.move(str(tmp), str(DATABASE_PATH))
        initialize_database()
    except Exception as exc:
        return jsonify({"error": f"Failed to restore database: {exc}"}), 500

    return jsonify({"success": True, "message": "Database restored successfully."})


@app.route("/api/db-info")
@login_required
def db_info():
    user = _session_user()
    if user["role"] != "Admin":
        abort(403)
    from config import DATA_DIR
    import os
    info = {
        "database_path": str(DATABASE_PATH),
        "data_dir": str(DATA_DIR),
        "file_exists": DATABASE_PATH.exists(),
        "file_size_bytes": DATABASE_PATH.stat().st_size if DATABASE_PATH.exists() else 0,
        "geetapariwar_data_dir_env": os.environ.get("GEETAPARIWAR_DATA_DIR", "not set"),
    }
    if DATABASE_PATH.exists():
        try:
            conn = get_connection()
            tables = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
            ).fetchall()
            info["tables"] = []
            for t in tables:
                count = conn.execute(f"SELECT COUNT(*) FROM {t[0]}").fetchone()[0]
                info["tables"].append({"name": t[0], "rows": count})
            conn.close()
        except Exception as e:
            info["error"] = str(e)
    return jsonify(info)

# ── Start ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 3201))
    app.run(host="0.0.0.0", port=port, debug=True)

"""
PRN lookup service.

Searches the local database first, then falls back to the
LearnGeeta website when no local match is found.
"""

import logging
import os
import re
import ssl
import urllib.request
import urllib.parse
from html.parser import HTMLParser
from dataclasses import dataclass
from typing import List, Optional
from database import get_connection

log = logging.getLogger(__name__)

# Known country codes (sorted longest first so longer prefixes match first)
_COUNTRY_CODES = sorted([
    "+977", "+91", "+93", "+355", "+213", "+1684", "+376", "+244",
    "+1264", "+1268", "+54", "+374", "+297", "+61", "+43", "+994",
    "+1242", "+973", "+880", "+1246", "+375", "+32", "+501", "+229",
    "+1441", "+975", "+591", "+387", "+267", "+55", "+1284", "+673",
    "+359", "+226", "+257", "+855", "+237", "+1", "+238", "+1345",
    "+236", "+235", "+56", "+86", "+57", "+269", "+682", "+506",
    "+225", "+385", "+53", "+357", "+420", "+243", "+45", "+253",
    "+1767", "+1809", "+670", "+593", "+20", "+503", "+240", "+291",
    "+372", "+251", "+500", "+298", "+679", "+358", "+33", "+594",
    "+689", "+241", "+220", "+995", "+49", "+233", "+350", "+30",
    "+1473", "+590", "+1671", "+502", "+224", "+245", "+592", "+509",
    "+504", "+852", "+36", "+354", "+62", "+98", "+964", "+353",
    "+972", "+39", "+1876", "+81", "+962", "+7", "+254", "+686",
    "+383", "+965", "+996", "+856", "+371", "+961", "+266", "+231",
    "+218", "+423", "+370", "+352", "+853", "+261", "+265", "+60",
    "+960", "+223", "+356", "+692", "+222", "+230", "+262", "+52",
    "+691", "+373", "+377", "+976", "+382", "+1664", "+212", "+258",
    "+95", "+264", "+674", "+31", "+599", "+687", "+64", "+505",
    "+227", "+234", "+683", "+672", "+389", "+1670", "+47", "+968",
    "+92", "+680", "+970", "+507", "+675", "+595", "+51", "+63",
    "+48", "+351", "+1939", "+974", "+242", "+40", "+250", "+290",
    "+1869", "+1758", "+508", "+1784", "+685", "+378", "+239", "+966",
    "+221", "+381", "+248", "+232", "+65", "+1721", "+421", "+386",
    "+677", "+252", "+27", "+82", "+211", "+34", "+94", "+249",
    "+597", "+268", "+46", "+41", "+963", "+886", "+992", "+255",
    "+66", "+228", "+690", "+676", "+1868", "+216", "+90", "+993",
    "+1649", "+688", "+256", "+380", "+971", "+44", "+598", "+998",
    "+678", "+379", "+58", "+84", "+1340", "+681", "+967", "+260",
    "+263",
], key=len, reverse=True)


def _clean_phone(raw: str) -> str:
    """Strip country code and non-digits, returning just the local number.

    Only remove a country code when the raw value begins with an explicit
    international prefix such as "+" or "00". This avoids stripping local
    numbers like 9849123377 as if they were prefixed by "+98".
    """
    value = raw.strip()
    if not (value.startswith("+") or value.startswith("00")):
        return re.sub(r"\D", "", value)

    if value.startswith("00"):
        value = "+" + value[2:]

    digits = re.sub(r"\D", "", value)
    for cc in _COUNTRY_CODES:
        code_digits = cc.replace("+", "")
        if digits.startswith(code_digits) and len(digits) > len(code_digits):
            return digits[len(code_digits):]
    return digits


@dataclass
class PrnResult:
    prn: str
    name: str
    phone: Optional[str] = None
    email: Optional[str] = None


def _normalize_phone_digits(raw: str) -> str:
    return re.sub(r"\D", "", raw or "")


def _search_prn_local(mobile_or_email: str) -> List[PrnResult]:
    """Search local sadhak table by phone or email."""
    conn = get_connection()
    term = mobile_or_email.strip()
    digits = _normalize_phone_digits(term)
    if "@" in term:
        rows = conn.execute(
            "SELECT prn, name, phone, email FROM sadhak WHERE email = ?",
            (term,),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT prn, name, phone, email FROM sadhak WHERE phone LIKE ? OR phone LIKE ? OR email = ?",
            (f"%{digits}", f"%{digits}%", term),
        ).fetchall()
    conn.close()

    exact_matches: List[PrnResult] = []
    partial_matches: List[PrnResult] = []
    for prn, name, phone, email in rows:
        if not prn:
            continue
        phone_digits = _normalize_phone_digits(phone or "")
        if digits and phone_digits.endswith(digits):
            exact_matches.append(PrnResult(prn=prn, name=name, phone=phone, email=email))
        else:
            partial_matches.append(PrnResult(prn=prn, name=name, phone=phone, email=email))

    return exact_matches or partial_matches


class _LearnGeetaParser(HTMLParser):
    """Parse the LearnGeeta participant search result table."""

    def __init__(self) -> None:
        super().__init__()
        self.results: List[PrnResult] = []
        self._in_table = False
        self._in_tbody = False
        self._row_cells: List[str] = []
        self._current_tag: Optional[str] = None

    def handle_starttag(self, tag: str, attrs) -> None:
        self._current_tag = tag
        classes = dict(attrs).get("class", "")
        if tag == "table" and "table-striped" in classes:
            self._in_table = True
        if self._in_table and tag == "tbody":
            self._in_tbody = True
        if self._in_tbody and tag == "tr":
            self._row_cells = []

    def handle_endtag(self, tag: str) -> None:
        if tag == "table":
            self._in_table = False
        if tag == "tbody":
            self._in_tbody = False
        if self._in_tbody and tag == "tr" and len(self._row_cells) >= 3:
            self.results.append(PrnResult(
                prn=self._row_cells[1].strip(),
                name=self._row_cells[2].strip(),
            ))
        self._current_tag = None

    def handle_data(self, data: str) -> None:
        if self._in_tbody and self._current_tag in ("td", "th"):
            self._row_cells.append(data.strip())


_REMOTE_TIMEOUT = 3

# Module-level cache for the HTTP session (avoids repeated GETs for cookies)
_remote_session = None


def _get_remote_session():
    global _remote_session
    if _remote_session is not None:
        return _remote_session

    url = "https://online.learngeeta.com/participant/searchparticipant.php"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:131.0) Gecko/20100101 Firefox/131.0"}

    try:
        import requests as req_lib
        sess = req_lib.Session()
        sess.verify = False
        sess.headers.update(headers)
        sess.get(url, timeout=_REMOTE_TIMEOUT)
        _remote_session = sess
        return sess
    except Exception:
        pass

    try:
        import http.cookiejar
        cj = http.cookiejar.CookieJar()
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        opener = urllib.request.build_opener(
            urllib.request.HTTPSHandler(context=ctx),
            urllib.request.HTTPCookieProcessor(cj),
        )
        get_req = urllib.request.Request(url)
        for k, v in headers.items():
            get_req.add_header(k, v)
        opener.open(get_req, timeout=_REMOTE_TIMEOUT).close()
        _remote_session = opener
        return opener
    except Exception:
        return None


def _search_prn_remote(term: str) -> List[PrnResult]:
    data = {"email": term, "Submit": "Search"}
    url = "https://online.learngeeta.com/participant/searchparticipant.php"
    html = None

    sess = _get_remote_session()
    if sess is None:
        return []

    try:
        if hasattr(sess, "post"):
            resp = sess.post(url, data=data, timeout=_REMOTE_TIMEOUT)
            if resp.status_code == 200:
                html = resp.text
        else:
            post_req = urllib.request.Request(
                url, data=urllib.parse.urlencode(data).encode(), method="POST"
            )
            post_req.add_header(
                "User-Agent",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:131.0) Gecko/20100101 Firefox/131.0",
            )
            with sess.open(post_req, timeout=_REMOTE_TIMEOUT) as resp:
                html = resp.read().decode("utf-8", errors="replace")
    except Exception as exc:
        log.warning("_search_prn_remote(%r) error: %s: %s", term, type(exc).__name__, exc)
        return []

    parser = _LearnGeetaParser()
    try:
        parser.feed(html)
    except Exception as exc:
        log.error("_search_prn_remote(%r) parse error: %s", term, exc)
        return []

    return parser.results


def search_prn(mobile_or_email: str) -> List[PrnResult]:
    """Search for participant PRN by mobile number or email.

    Checks the local database first.  When no local match is found,
    falls back to searching the LearnGeeta website.
    """
    search_terms = [mobile_or_email.strip()]
    cleaned = _clean_phone(mobile_or_email)
    if cleaned and cleaned not in search_terms:
        search_terms.append(cleaned)

    for term in search_terms:
        results = _search_prn_local(term)
        if results:
            return results

    # Fallback to remote (skip on PythonAnywhere — outbound blocked)
    if "PYTHONANYWHERE_DOMAIN" not in os.environ:
        for term in search_terms:
            results = _search_prn_remote(term)
            if results:
                return results
    return []


def _select_best_prn_result(results: List[PrnResult], term: str) -> Optional[PrnResult]:
    """Pick the best match from a list of PRN results.

    Prefers results where the phone number ends with the given term's digits,
    otherwise falls back to the first result.
    """
    if not results:
        return None
    if len(results) == 1:
        return results[0]

    digits = re.sub(r"\D", "", term or "")
    if digits:
        for r in results:
            if r.phone and _normalize_phone_digits(r.phone).endswith(digits):
                return r

    return results[0]


def search_by_prn(prn: str) -> List[PrnResult]:
    """Search for a participant by PRN number.

    Checks the local database only. The remote LearnGeeta endpoint only
    supports mobile/email search, not PRN lookup.
    """
    conn = get_connection()
    rows = conn.execute(
        "SELECT prn, name FROM sadhak WHERE prn LIKE ?",
        (f"%{prn}%",),
    ).fetchall()
    conn.close()
    return [PrnResult(prn=r[0], name=r[1]) for r in rows if r[0]]

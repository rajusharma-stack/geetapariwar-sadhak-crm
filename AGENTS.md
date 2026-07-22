# Geeta Pariwar Sadhak CRM – Agent Memory

## Project
- **Desktop app**: `main.py` (Tkinter/ttkbootstrap)
- **Web app**: `app.py` (Flask, port 3201)

## Key Fixes

### 1. ImportError: `_select_best_prn_result`
- **File**: `services/prn_service.py`
- **Symptom**: `ImportError: cannot import name '_select_best_prn_result'` when running `main.py`
- **Fix**: Re-added the `_select_best_prn_result(results, term)` function — it was accidentally deleted.
- **Used by**: `views/dashboard.py` (PRN auto-lookup) and `tests/test_prn_service.py`

### 2. PRN auto-search not populating name/PRN for local numbers
- **File**: `views/dashboard.py` — `_strip_country_code()` method
- **Symptom**: Typing a Nepali number like `9846…` would strip `98` (Iran's country code), yielding wrong search term
- **Fix**: Only attempt country-code stripping from the fallback list when the number has an explicit international prefix (`+` or `00`). Also handle `00…` → `+…` normalization.

### 3. LearnGeeta remote search not working in desktop app
- **File**: `services/prn_service.py`
- **Symptom**: `search_prn()` only queried local DB; new numbers not in DB got no results
- **Fix**: Added `_search_prn_remote()` that POSTs to `https://online.learngeeta.com/participant/searchparticipant.php` and parses the HTML response table. Falls back to remote when local search returns nothing.

### 4. LearnGeeta HTML parser skipping rows
- **File**: `services/prn_service.py` — `_LearnGeetaParser.handle_data()`
- **Symptom**: Remote search returned empty results even when LearnGeeta had data
- **Fix**: The table's first column uses `<th>` (not `<td>`), so `handle_data` was only checking `self._current_tag == "td"`. Changed to `self._current_tag in ("td", "th")` to also capture `<th>` cell values.

## Serving as web server (for others to access)
```powershell
.\serve_web.bat
```
This starts ngrok + waitress (production WSGI). It prints a public URL you can share with anyone.
- Requires ngrok (already installed)
- Others just open the link in their browser, log in with their credentials, and use the CRM

## Running the app
```powershell
.venv\Scripts\python.exe main.py
```

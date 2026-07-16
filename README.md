# Geeta Pariwar Nepal Sadhak CRM

A professional desktop CRM application built for **Geeta Pariwar Nepal** to manage *Sadhak* (devotee) records, track activities, and organise community data.

## Features *(planned)*

- Sadhak (devotee) registration and profile management
- Search, filter, and export contact data
- Activity / attendance tracking
- Backup and restore utilities
- Data export to Excel via `openpyxl` / `pandas`

## Tech Stack

| Component | Technology |
|-----------|------------|
| Language  | Python 3.13+ |
| GUI       | ttkbootstrap (modern Tkinter) |
| Database  | SQLite |
| Export    | openpyxl, pandas |

## Project Structure

```
Geetapariwarsadhak/
├── main.py          # Application entry point
├── database.py      # Database initialisation & connection helpers
├── config.py        # Centralised paths and constants
├── requirements.txt # Python dependencies
├── README.md        # This file
├── assets/          # Static assets (icons, images, etc.)
├── data/            # SQLite database storage
├── backups/         # Database backup files
└── exports/         # Exported spreadsheets / reports
```

## Getting Started

1. **Clone or copy** the project to your machine.
2. **Create a virtual environment** (recommended):
   ```bash
   python -m venv venv
   .\venv\Scripts\activate   # Windows
   ```
3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
4. **Run the application**:
   ```bash
   python main.py
   ```

> If `python main.py` fails with `ModuleNotFoundError: No module named 'ttkbootstrap'`, make sure VS Code is using the project virtual environment at `.venv`.
>
> In VS Code, select the Python interpreter from `.venv/Scripts/python.exe` and reopen the terminal.

The database will be created automatically inside the `data/` folder on first launch.

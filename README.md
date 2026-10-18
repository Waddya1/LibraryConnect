# LibraryConnect (Stage 1)

Library due-date tracker. Flask + SQLite. Uses fake/test data only.

## Setup (Windows, VS Code terminal = PowerShell)
```
python -m venv venv
venv\Scripts\Activate.ps1
pip install -r requirements.txt
flask --app app init-db
flask --app app run --debug
```
Open http://127.0.0.1:5000

## Run the tests
```
python -m unittest discover -s tests -t .
```

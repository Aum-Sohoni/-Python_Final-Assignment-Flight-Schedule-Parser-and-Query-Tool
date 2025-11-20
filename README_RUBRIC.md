# Flight Tool — Grading Rubric Coverage

This document summarizes how the repository meets the grading rubric items and how to exercise each feature.

Features and commands

- Grade 4 — Read and print CSV content
  - Use: `python3 flight_tool.py -i sample_db.csv -s`
  - Explanation: `-s/--show` prints raw CSV lines with line numbers (file I/O, loops).

- Grade 5 — Basic field splitting and minimal validation
  - Implemented in `validate_row` (checks for presence, basic string rules).

- Grade 6 — Full validation, separation of valid vs invalid rows, output to files
  - Valid flights are written to JSON via `-o` (default `db.json`).
  - Invalid rows and reasons are written to the `--errors` file.

- Grade 7 — JSON output for valid flights
  - Uses Python `json` module to serialize validated flight dicts.

- Grade 8 — CLI arguments `-i`, `-d`, `-o`
  - Implemented with `argparse` in `flight_tool.py`.

- Grade 9 — Folder parsing, combined output, robust error handling
  - Use `-d` to parse all `.csv` in a folder, combined output to `-o`.

- Grade 10 — `-j` (load JSON), `-q` (query JSON), datetime filtering
  - `-j` loads an existing JSON DB and skips CSV parsing.
  - `-q` runs queries defined in a JSON file (supports equality filters and datetime bounds).

Notes

- The main script `flight_tool.py` contains the implementation and a `--show` flag for Grade 4 demonstration.
- If you need stricter IATA validation (e.g., `XXX` rejected), I can add a `--strict-iata` flag and a small allowed-codes list.

Suggested next steps

- Run the parser on `sample_db.csv`: `python3 flight_tool.py -i sample_db.csv -o sample_db.json --errors sample_db_errors.txt -s`
- Run queries: `python3 flight_tool.py -j sample_db.json -q sample_queries.json --query-results results.json`

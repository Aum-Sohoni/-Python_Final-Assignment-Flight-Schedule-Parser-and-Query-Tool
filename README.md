# Flight Schedule Parser and Query Tool

Small CLI tool to parse flight schedule CSV files, validate rows, export a JSON database of valid flights (`db.json`) and an `errors.txt` with invalid rows. You can also load an existing JSON database and run queries defined in a JSON file.

Usage examples

- Parse CSV files and write DB + errors:

```bash
python flight_tool.py --csv flights1.csv flights2.csv --out-db db.json --errors errors.txt
```

- Load existing DB and run queries:

```bash
python flight_tool.py --load-db db.json --queries sample_queries.json --query-results results.json
```

CSV format

The CSV should contain at minimum these headers: `flight_number`, `origin`, `destination`, `departure`, `arrival`.

- `departure` and `arrival` should be ISO-8601 datetimes (e.g. `2025-11-20T15:30:00`) or common formats like `YYYY-MM-DD HH:MM`.

Queries

The queries file is a JSON list of query objects. Supported query keys:

- `name`: optional human name for the query
- `filter`: object of equality filters, e.g. `{ "origin": "JFK" }`
- `departure_between`: `["start_iso", "end_iso"]` — include flights whose `departure` is between these datetimes
- `arrival_before` / `arrival_after`: ISO datetimes

Example `sample_queries.json` is included.

Output

- `db.json`: JSON array of validated flights (fields are normalized; `departure` and `arrival` are ISO strings)
- `errors.txt`: plain text lines with errors and original row information
- `query_results.json`: object with query results when `--queries` is provided

Notes

- The script uses only Python standard library. It expects to be run with Python 3.8+.
- If you need additional filters (e.g., text contains, regex, numeric ranges), open an issue or modify `apply_filters` in `flight_tool.py`.

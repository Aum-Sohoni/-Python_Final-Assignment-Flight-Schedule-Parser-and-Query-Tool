#!/usr/bin/env python3
"""
flight_tool.py

Parse flight schedule CSV files, validate records, export `db.json` and `errors.txt`,
optionally load an existing JSON database, execute queries from a JSON file and save results.

Usage examples:
  python flight_tool.py --csv flights1.csv flights2.csv --out-db db.json --errors errors.txt
  python flight_tool.py --load-db db.json --queries sample_queries.json --query-results results.json

"""
import argparse
import csv
import json
from datetime import datetime
from typing import List, Tuple, Dict, Any
import sys


REQUIRED_FIELDS = ["flight_id", "origin", "destination", "departure_datetime", "arrival_datetime", "price"]


def parse_iso_datetime(s: str) -> datetime:
    s = s.strip()
    if not s:
        raise ValueError("empty datetime")
    # Enforce exact format YYYY-MM-DD HH:MM as required
    try:
        return datetime.strptime(s, "%Y-%m-%d %H:%M")
    except Exception:
        raise ValueError(f"invalid datetime format (expected 'YYYY-MM-DD HH:MM'): {s}")


def validate_row(row: Dict[str, str], file: str, lineno: int) -> Tuple[Dict[str, Any], str]:
    """
    Validate a CSV row. Returns (flight_dict, '') on success, (None, error_msg) on failure.
    """
    # Check required fields
    for f in REQUIRED_FIELDS:
        if f not in row or row[f] is None or str(row[f]).strip() == "":
            return None, f"missing required field '{f}'"

    # flight_id: 2-8 alphanumeric
    fid = str(row.get("flight_id", "")).strip()
    if not (2 <= len(fid) <= 8 and fid.isalnum()):
        return None, "flight_id must be 2-8 alphanumeric characters"

    # origin/destination: 3 uppercase letters
    origin = str(row.get("origin", "")).strip()
    dest = str(row.get("destination", "")).strip()
    if not (len(origin) == 3 and origin.isalpha() and origin.isupper()):
        return None, "origin must be 3 uppercase letters"
    if not (len(dest) == 3 and dest.isalpha() and dest.isupper()):
        return None, "destination must be 3 uppercase letters"

    # Parse datetimes in exact format YYYY-MM-DD HH:MM
    try:
        dep = parse_iso_datetime(row["departure_datetime"])
    except Exception as e:
        return None, f"departure_datetime parse error: {e}"
    try:
        arr = parse_iso_datetime(row["arrival_datetime"])
    except Exception as e:
        return None, f"arrival_datetime parse error: {e}"

    if arr <= dep:
        return None, "arrival_datetime must be after departure_datetime"

    # price: positive float
    try:
        price = float(str(row.get("price")).strip())
        if price <= 0:
            return None, "price must be a positive number"
    except Exception:
        return None, "price must be a positive float"

    # Build normalized flight dict (keep datetime strings in the original format)
    flight = {
        "flight_id": fid,
        "origin": origin,
        "destination": dest,
        "departure_datetime": dep.strftime("%Y-%m-%d %H:%M"),
        "arrival_datetime": arr.strftime("%Y-%m-%d %H:%M"),
        "price": price,
    }

    # Include any extra fields present
    for k, v in row.items():
        if k in flight or v is None:
            continue
        s = str(v).strip()
        if s:
            flight[k] = s

    return flight, ""


def parse_csv_files(paths: List[str]) -> Tuple[List[Dict[str, Any]], List[str]]:
    valid = []
    errors = []
    for p in paths:
        try:
            with open(p, newline="", encoding="utf-8") as fh:
                reader = csv.DictReader(fh)
                for lineno, row in enumerate(reader, start=2):
                    flight, err = validate_row(row, p, lineno)
                    if flight:
                        valid.append(flight)
                    else:
                        errors.append(f"{p}:{lineno}: {err} -- {row}")
        except FileNotFoundError:
            errors.append(f"file not found: {p}")
        except Exception as e:
            errors.append(f"{p}: error reading file: {e}")
    return valid, errors


def save_db(path: str, flights: List[Dict[str, Any]]):
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(flights, fh, indent=2, ensure_ascii=False)


def save_errors(path: str, errors: List[str]):
    with open(path, "w", encoding="utf-8") as fh:
        for e in errors:
            fh.write(e + "\n")


def load_db(path: str) -> List[Dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, list):
        raise ValueError("expected JSON database to be a list of flights")
    return data


def apply_filters(flights: List[Dict[str, Any]], q: Dict[str, Any]) -> List[Dict[str, Any]]:
    res = flights
    # Simple equality filters
    filt = q.get("filter") or {}
    for k, v in filt.items():
        res = [f for f in res if str(f.get(k, "")).lower() == str(v).lower()]

    # departure_between: [start_iso, end_iso]
    if "departure_between" in q:
        start, end = q["departure_between"]
        start_dt = parse_iso_datetime(start)
        end_dt = parse_iso_datetime(end)
        res = [f for f in res if start_dt <= parse_iso_datetime(f["departure"]) <= end_dt]

    if "arrival_before" in q:
        end_dt = parse_iso_datetime(q["arrival_before"]) 
        res = [f for f in res if parse_iso_datetime(f["arrival"]) <= end_dt]

    if "arrival_after" in q:
        start_dt = parse_iso_datetime(q["arrival_after"]) 
        res = [f for f in res if parse_iso_datetime(f["arrival"]) >= start_dt]

    return res


def run_queries(flights: List[Dict[str, Any]], queries_path: str) -> Dict[str, Any]:
    with open(queries_path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, list):
        raise ValueError("queries JSON must be a list of query objects")

    results = []
    for qi, q in enumerate(data, start=1):
        name = q.get("name") or f"q{qi}"
        matched = apply_filters(flights, q)
        results.append({"name": name, "count": len(matched), "results": matched})
    return {"queries": results}


def main(argv=None):
    parser = argparse.ArgumentParser(description="Flight schedule parser and query tool")
    parser.add_argument("-i", "--input", help="Parse a single CSV file")
    parser.add_argument("-d", "--dir", help="Parse all .csv files in a folder and combine results")
    parser.add_argument("-o", "--out", default="db.json", help="Write valid flights to this JSON file (default: db.json)")
    parser.add_argument("-j", "--db", help="Load existing JSON database instead of parsing CSVs")
    parser.add_argument("-q", "--queries", help="JSON file containing queries to run on the DB")
    parser.add_argument("--query-results", default="query_results.json", help="Where to write query results JSON")
    parser.add_argument("--errors", default="errors.txt", help="Write invalid lines to this file")
    parser.add_argument("-s", "--show", action="store_true", help="Print raw CSV content lines (useful for grade 4 demos)")
    args = parser.parse_args(argv)

    flights = []
    errors = []

    # Load DB from JSON if requested
    if args.db:
        try:
            flights = load_db(args.db)
            print(f"Loaded {len(flights)} flights from {args.db}")
        except Exception as e:
            print(f"Error loading DB: {e}", file=sys.stderr)
            sys.exit(2)
    else:
        # Determine CSV sources: single file or directory
        csv_paths = []
        if args.input:
            csv_paths.append(args.input)
        if args.dir:
            import os
            if not os.path.isdir(args.dir):
                print(f"Directory not found: {args.dir}", file=sys.stderr)
                sys.exit(2)
            for fn in sorted(os.listdir(args.dir)):
                if fn.lower().endswith('.csv'):
                    csv_paths.append(os.path.join(args.dir, fn))

        if not csv_paths:
            print("Either provide `-j path/to/db.json` or `-i file.csv` or `-d folder/`", file=sys.stderr)
            sys.exit(2)

        # Optionally print raw CSV content for demonstration (Grade 4 requirement)
        if args.show:
            for p in csv_paths:
                try:
                    with open(p, 'r', encoding='utf-8') as fh:
                        for i, line in enumerate(fh, start=1):
                            line_s = line.rstrip('\n')
                            if line_s.strip() == "":
                                continue
                            print(f"{p}: Line {i}: {line_s}")
                except Exception as e:
                    print(f"Error reading {p} for --show: {e}", file=sys.stderr)

        flights, errors = parse_csv_files(csv_paths)
        print(f"Parsed: {len(flights)} valid flights, {len(errors)} errors")

    save_db(args.out, flights)
    print(f"Saved DB to {args.out}")
    if errors:
        save_errors(args.errors, errors)
        print(f"Saved errors to {args.errors}")

    if args.queries:
        try:
            qres = run_queries(flights, args.queries)
            with open(args.query_results, "w", encoding="utf-8") as fh:
                json.dump(qres, fh, indent=2, ensure_ascii=False)
            print(f"Wrote query results to {args.query_results}")
        except Exception as e:
            print(f"Error running queries: {e}", file=sys.stderr)
            sys.exit(3)


if __name__ == "__main__":
    main()

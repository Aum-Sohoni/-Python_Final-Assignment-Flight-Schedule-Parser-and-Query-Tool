#!/usr/bin/env python3
"""Run the flight tool workflow by importing functions directly.

This avoids spawning a subprocess and exercises the parsing + saving + querying
logic programmatically.
"""
from flight_tool import parse_csv_files, save_db, save_errors, run_queries, load_db
import sys


def main():
    csv_path = "sample_db.csv"
    out_db = "sample_db.json"
    errors_file = "sample_db_errors.txt"
    queries = "sample_queries.json"
    query_results = "sample_query_results.json"

    print(f"Parsing {csv_path}...")
    flights, errors = parse_csv_files([csv_path])
    print(f"Parsed: {len(flights)} valid, {len(errors)} errors")

    print(f"Writing DB to {out_db}")
    save_db(out_db, flights)
    if errors:
        print(f"Writing errors to {errors_file}")
        save_errors(errors_file, errors)

    # Run queries if any
    try:
        print(f"Running queries from {queries}")
        qres = run_queries(flights, queries)
        with open(query_results, "w", encoding="utf-8") as fh:
            import json
            json.dump(qres, fh, indent=2, ensure_ascii=False)
        print(f"Wrote query results to {query_results}")
    except FileNotFoundError:
        print(f"Queries file not found: {queries}")
    except Exception as e:
        print(f"Error running queries: {e}", file=sys.stderr)


if __name__ == "__main__":
    main()

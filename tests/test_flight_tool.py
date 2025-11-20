import unittest
import os
import json

from flight_tool import validate_row, parse_csv_files, apply_filters, parse_iso_datetime


class FlightToolTests(unittest.TestCase):
    def setUp(self):
        self.sample_csv = os.path.join(os.path.dirname(__file__), '..', 'sample_flights.csv')

    def test_validate_row_valid(self):
        row = {
            'flight_id': 'AA100',
            'origin': 'JFK',
            'destination': 'LAX',
            'departure_datetime': '2025-11-20 08:00',
            'arrival_datetime': '2025-11-20 11:00',
            'price': '199.99'
        }
        flight, err = validate_row(row, 'sample', 1)
        self.assertEqual(err, "")
        self.assertEqual(flight['flight_id'], 'AA100')
        self.assertEqual(flight['origin'], 'JFK')

    def test_validate_row_missing(self):
        row = {
            'flight_id': 'BA200',
            'origin': '',
            'destination': 'LHR',
            'departure_datetime': '2025-11-21 09:00',
            'arrival_datetime': '2025-11-21 19:00',
            'price': '299.50'
        }
        flight, err = validate_row(row, 'sample', 2)
        self.assertIsNotNone(err)
        self.assertIsNone(flight)

    def test_validate_row_arrival_before(self):
        row = {
            'flight_id': 'DL300',
            'origin': 'ATL',
            'destination': 'MIA',
            'departure_datetime': '2025-11-22 15:00',
            'arrival_datetime': '2025-11-22 14:00',
            'price': '150.00'
        }
        flight, err = validate_row(row, 'sample', 3)
        self.assertIsNotNone(err)
        self.assertIsNone(flight)

    def test_parse_csv_files_counts(self):
        base = os.path.join(os.path.dirname(__file__), '..')
        csv_path = os.path.join(base, 'sample_flights.csv')
        valid, errors = parse_csv_files([csv_path])
        self.assertEqual(len(valid), 2)
        self.assertEqual(len(errors), 2)

    def test_apply_filters(self):
        flights = [
            {
                'flight_id': 'AA100', 'origin': 'JFK', 'destination': 'LAX',
                'departure_datetime': '2025-11-20 08:00', 'arrival_datetime': '2025-11-20 11:00'
            },
            {
                'flight_id': 'UA400', 'origin': 'SFO', 'destination': 'SEA',
                'departure_datetime': '2025-11-23 07:30', 'arrival_datetime': '2025-11-23 09:00'
            }
        ]
        q = {'filter': {'origin': 'JFK'}}
        res = apply_filters(flights, q)
        self.assertEqual(len(res), 1)

        q2 = {'departure_between': ['2025-11-01 00:00', '2025-11-30 23:59']}
        res2 = apply_filters(flights, q2)
        self.assertEqual(len(res2), 2)

    def test_parse_iso_datetime_variants(self):
        self.assertIsNotNone(parse_iso_datetime('2025-11-23 07:30'))
        with self.assertRaises(Exception):
            parse_iso_datetime('2025-11-23T07:30:00')


if __name__ == '__main__':
    unittest.main()

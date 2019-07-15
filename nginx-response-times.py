#!/usr/bin/env python3
import argparse
import sys
import requests
import time
import math


class Range:
    def __init__(self, low, high, warning=None, critical=None):
        self.low = low
        self.high = high
        self.warning = warning
        self.critical = critical

    def __str__(self):
        return f"{self.low};{self.high};{self.warning};{self.critical}"

    def __repr__(self):
        return str(self)

    @property
    def has_alerts(self):
        return self.warning is not None or self.critical is not None


def split_ranges(range_list):
    # icinga do not allow to repeat same argument, so join them all and split them again
    for data in " ".join(range_list).split(" "):
        if not data:
            continue
        array = data.split(':')

        low = float(array[0])
        high = float(array[1]) if len(array) > 1 and array[1] else None
        warn = float(array[2]) if len(array) > 2 and array[2] else None
        crit = float(array[3]) if len(array) > 3 and array[3] else None

        yield Range(low=low, high=high, warning=warn, critical=crit)

    

def query(args, range_list):
    url = f"{args.uri}/{args.index}*/_search"
    auth = (args.username, args.password)
    ranges = [{ "from": x.low, "to": x.high} for x in range_list]
    date_to = int(time.time() * 1000)
    date_from = date_to - (args.minutes * 60000)

    body = {
      "aggs": {
        "2": {
          "range": {
            "field": args.request_time_field,
            "ranges": ranges,
            "keyed": False
          }
        }
      },
      "size": 0,
      "query": {
        "bool": {
          "must": [
            {
              "range": {
                "@timestamp": {
                  "gte": date_from,
                  "lte": date_to,
                  "format": "epoch_millis"
                }
              }
            }
          ]
        }
      }
    }

    r = requests.post(url, auth=auth, json=body)
    r.raise_for_status()

    return r.json()


def print_nagios_report(range_list, result):
    OK, WARN, CRIT = 0, 1, 2
    buckets = result['aggregations']['2']['buckets']
    result = OK
    stdout = ""
    perf = ""

    def find(r):
        for b in buckets:
            if b.get('from') == r.low and b.get('to') == r.high:
                return b

    def check_status(r, value):
        if r.critical is not None and value > r.critical:
            return "CRITICAL: %s > %s" % (value, r.critical), CRIT
        if r.warning is not None and value > r.warning:
            return "WARNING: %s > %s" % (value, r.warning), WARN
        return '', OK

    for r in range_list:
        bucket = find(r)
        error, new_status = check_status(r, bucket['doc_count']) 
        perf += "'{l}'={v};{w};{c};0; ".format(
            l=bucket['key'],
            v=bucket['doc_count'],
            w='' if r.warning is None else r.warning,
            c='' if r.critical is None else r.critical,
        )
        stdout += "{l} = {v} {e}\n".format(
            l=bucket['key'],
            v=bucket['doc_count'],
            e=error,
        )
        result = max(result, new_status)
    print("%s|%s" % (stdout, perf))
    return result 
        

def parse_args():
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument(
        '--uri',
        required=True,
        help='Host to connect to.'
    )
    parser.add_argument(
        '--index', 
        required=True,
        help='Index to be used'
    )
    parser.add_argument(
        '--username',
        help='User to be used on connection'
    )
    parser.add_argument(
        '--password',
        help='Password to be used on connection'
    )
    parser.add_argument(
        '--minutes',
        type=int,
        default=5,
        help='Search for the last N minutes'
    )
    parser.add_argument(
        '--range',
        nargs='+',
        type=str,
        help='Tuples (value, min, max) to generate ranges. The first one must be 0.'
    )
    parser.add_argument(
        '--request-time-field',
        default="request_time",
        help='Field name where the request time is stored'
    )
    return parser.parse_args()


def main():
    args = parse_args()
    range_list = list(split_ranges(args.range or []))
    result = query(args, range_list)
    sys.exit(print_nagios_report(range_list, result))
    

if __name__ == "__main__":
    main()

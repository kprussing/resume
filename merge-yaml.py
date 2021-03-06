#!/usr/bin/env python
__doc__ = """Merge YAML documents into a single list.  The list can be
placed in a dictionary by passing the optional label.
"""

import argparse
import yaml

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("yaml", nargs="+", help="YAML files to merge",
                        type=argparse.FileType("r"))
    parser.add_argument("-l", "--label", help="Output label")
    parser.add_argument("-o", "--output", default="-",
                        help="Output file", type=argparse.FileType("w"))
    args = parser.parse_args()

    data = []
    for file_ in args.yaml:
        content = yaml.safe_load(file_.read())
        if isinstance(content, list):
            data.extend(content)
        else:
            data.append(content)

    if args.label:
        data = {args.label : data}

    args.output.write("---\n" + yaml.dump(data) + "...\n")


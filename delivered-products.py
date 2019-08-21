#!/usr/bin/env python3
__doc__ = """Extract the key delivered products from the YAML and format
them for the CV.  The default top level key we are looking for is
`key-delivered-products'.  This is an array 
"""

import argparse
import datetime
import sys

import yaml

_example = """---
key-delivered-products:
  - name: Title for the delivered product
    URL: https://example.com
    sponsor: Sponsor or to whom the product was delivered
    date: # The date range for work performed by the candidate
    - year: 2015
      month: 1
    - year: 2017
      month: 3
    product: >
      Description of the product (Ex: What is it for the educated person
      not in your field?  Why was this important?  What is it used for,
      how does it fit into a larger effort, how widely is it used, is it
      well vetted/well distributed, etc.?)
    contribution: >
      What did you contribute?  (Ex: Smith developed the XYZ algorithm
      that…
...
"""

formats = {
        "latex" : {
            "header" : r"\subsection{{{0}}}",
            "opener" : "\\begin{enumerate}\n",
            "name" : lambda c, url: r"\href{{{URL}}}{{{name}}}" \
                                    if url and "URL" in c else "{name}",
            "item" : r"\item ",
            "start" : "\\begin{description}\n",
            "leader" : "\\item[{label}] {text}\n",
            "end" : "\\end{description}\n",
            "closer" : "\\end{enumerate}\n",
        },
        "markdown" : {
            "header" : "## {0}",
            "opener" : "",
            "name" : lambda c, url: r"[{name}]({URL})" \
                                    if url and "URL" in c else "{name}",
            "item" : "1.  ",
            "start" : "",
            "leader" : "    {label}\n:   {text}\n\n",
            "end" : "",
            "closer" : "",
        },
    }

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=argparse.FileType("r"),
                        help="Input YAML activities file")
    parser.add_argument("-o", "--output", default="-",
                        type=argparse.FileType("w"),
                        help="Target output file")
    parser.add_argument("-t", "--to", choices=formats.keys(),
                        default="latex", help="Output format")
    parser.add_argument("--key", default="key-delivered-products",
                        help="The field containing the target data")
    parser.add_argument("--title", type=str,
                        help="Title to place in the subsection macro")
    parser.add_argument("--no-url", action="store_false", dest="url",
                        help="Disable creating hyperlinks for titles")

    class ShortCircuit(argparse.Action):
        def __call__(self, parser, namespace, values, option_string=None):
            output = namespace.output
            (open(output, "w") if output != "-"
                               else sys.stdout).write(_example)
            sys.exit(0)

    parser.add_argument("-e", "--example", nargs=0, action=ShortCircuit,
                        help="Dump an example YAML input")
    args = parser.parse_args()

    format_ = formats[args.to]
    def find(data, key):
        """Walk a YAML file and locate the given key"""
        if isinstance(data, (str, bytes)):
            return None

        if key in data:
            return data[key]

        try:
            for v in data.values() if hasattr(data, "values") else data:
                ret = find(v, key)
                if ret is not None:
                    return ret

        except TypeError:
            pass

        return None

    date = lambda x: datetime.date(year=x["year"],
                                   month=x.get("month", 1),
                                   day=x.get("day", 1))
    products = sorted(find(yaml.safe_load(args.input), args.key),
                      key=lambda p: date(p["date"][1]),
                      reverse=True)
    items = (
            ("Name/Title for Key Delivered Product",
                lambda p: format_["name"](p, args.url).format(**p),
            ),
            ("Sponsor/To Whom Delivered",
                lambda p: p.get("sponsor", "Sponsor missing!")
            ),
            ("Date range for work performed by the candidate",
                lambda p: "{0:%b %Y}--{1:%b %Y}".format(
                    date(p["date"][0]), date(p["date"][1])
                )
            ),
            ("Describe Product",
                lambda p: p.get("product", "Product missing!")
            ),
            ("Candidate's specific technical contributions",
                lambda p: p.get("contribution", "Contribution missing")
            ),
        )

    args.output.write(format_["header"].format(args.title) + "\n\n"
                      if args.title else "")
    args.output.write(format_["opener"])
    leader = format_["leader"]
    for item in products:
        args.output.write(format_["item"])
        args.output.write(format_["start"])
        for label, text in items:
            args.output.write(leader.format(label=label,
                                            text=text(item).rstrip()))

        args.output.write(format_["end"])

    args.output.write(format_["closer"])


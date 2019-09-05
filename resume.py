#!/usr/bin/env python3
__doc__ = """The main driver for processing the YAML file with my resume
details into the appropriate format.  Most of the steps require a very
simple sequence of steps.  Therefore, we can simply use a common base
and simply define minor changes in the arguments to drive what needs to
be printed.  The two basic formats are LaTeX and `Pandoc`_'s Markdown.
The LaTeX output is tailored to the formatting details of the gtpromote_
class for the CV while the Markdown attempts to replicate portions of
the formatting.  In general, this attempts to get the formatting for the
LaTeX right and hope the Markdown generates a reasonable simulation when
passed through Pandoc.

_gtpromote: https://github.gatech.edu/kprussing3/gtpromote
_Pandoc: https://pandoc.org
"""

import argparse
import datetime
import logging
import os
import re
import sys

import yaml

## Utility functions

def sanitize(struct, format="latex"):
    """Sanitize a YAML object by escaping relevant characters

    This walks down the object 
    """
    func = {
            "latex" : lambda x: re.sub(r"([$\%&_])", r"\\\1", x),
            "markdown" : lambda x: x,
        }
    if isinstance(struct, (str, bytes)):
        return func[format](struct)

    if hasattr(struct, "items"):
        for k, v in struct.items():
            struct[k] = sanitize(v)

    else:
        try:
            for i, v in enumerate(struct):
                struct[i] = sanitize(v)

        except TypeError:
            pass

    return struct


def find(data, key):
    """Walk a YAML dictionary and locate the given key"""
    if data is None and isinstance(data, (str, bytes)):
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
"""Convert the YAML date to a :class:`datetime.date`"""

## Format mappings

formats = {
        "latex" : {
            "interests" : {
                "start"     : r"\begin{fields of interest}",
                "leader"    : r"\item",
                "end"       : r"\end{fields of interest}",
            },
            "delivered-products" : {
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
        },
        "markdown" : {
            "interests" : {
                "start"     : "### Fields of Interest\n",
                "leader"    : "-  ",
                "end"       : "",
            },
            "delivered-products" : {
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
        },
    }


## Examples

_examples = {
        "delivered-products" : """---
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
""",
        "professional-activities" : """---
...
""",
    }

_subparsers = (
        ("interests", "Process interests",
         """Locate the 'interests' tag and format the subsequent list
         into an itemized list.  The LaTeX wraps the list in the
         ``fields of interest`` environment while the Markdown generates
         a level 3 header followed by a list.
         """,
         ()
         ),
        ("delivered-products", "Process delivered products",
         """Extract the key delivered products from the YAML and format
         them for the CV.  The default top level key we are looking for
         is 'key-delivered-products'.  This must be an array.
         """,
         (("--key", dict(default="key-delivered-products",
                         help="The field containing the target data")),
          ("--title", dict(type=str,
                           help="Title to place in the subsection macro"))),
         ),
        ("test", "A dummy second parser", "A do nothing parser", ()),
    )


if __name__ == "__main__":
    prog = os.path.basename(os.path.dirname(os.path.abspath(__file__)))
    parser = argparse.ArgumentParser(prog=prog, description=__doc__)

    # Define some common configuration flags
    parser.add_argument("-t", "--to", choices=formats.keys(),
                        default="latex", help="Output format")
    parser.add_argument("--iso", action="store_true",
                        help="Write dates in ISO 8601 format")
    parser.add_argument("--no-url", action="store_false", dest="url",
                        help="Disable creating hyperlinks")

    group = parser.add_mutually_exclusive_group()
    group.add_argument("-v", "--verbose", action="store_true",
                       help="Enable verbose mode")
    group.add_argument("-d", "--debug", action="store_true",
                       help="Enable debug output mode")

    class ShortCircuit(argparse.Action):
        def __call__(self, parser, namespace, values, option_string=None):
            output = namespace.output
            out = (open(output, "w") if output != "-" else sys.stdout)
            out.write(_examples[args.action])
            sys.exit(0)

    subparsers = parser.add_subparsers(dest="action",
                                       help="Action to take")
    for name, help, desc, extra in _subparsers:
        s = subparsers.add_parser(name, help=help, description=desc)
        s.add_argument("input", type=argparse.FileType("r"),
                       help="Input YAML resume data file")
        s.add_argument("-o", "--output", default="-",
                       type=argparse.FileType("w"),
                       help="Output file")
        if name in _examples:
            s.add_argument("--example", nargs=0, action=ShortCircuit,
                           help="Dump an example YAML input")

        for flag, kwargs in extra:
            s.add_argument(flag, **kwargs)

    args = parser.parse_args()

    if args.debug:
        level = logging.DEBUG
    elif args.verbose:
        level = logging.INFO
    else:
        level = logging.WARNING

    logger = logging.getLogger(prog)
    logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler()
    handler.setLevel(level)
    formatter = logging.Formatter("%(levelname)s:%(name)s:%(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    fmt = formats[args.to].get(args.action, None)
    if fmt is None:
        logger.error("%s has no format defined for %s",
                     args.to, args.action)
        sys.exit(1)

    if args.action == "interests":
        data = sanitize(find(yaml.safe_load(args.input), "interests"))
        args.output.write(fmt["start"] + "\n")
        args.output.write("\n".join(fmt["leader"] + " " + i
                                    for i in data))
        args.output.write("\n" + fmt["end"] + "\n")

    elif args.action == "delivered-products":
        data = sanitize(find(yaml.safe_load(args.input), args.key))
        products = sorted(data,
                          key=lambda p: date(p["date"][1]),
                          reverse=True)
        items = (
                ("Name/Title for Key Delivered Product",
                    lambda p: fmt["name"](p, args.url).format(**p),
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
        args.output.write(fmt["header"].format(args.title) + "\n\n"
                          if args.title else "")
        args.output.write(fmt["opener"])
        leader = fmt["leader"]
        for item in products:
            args.output.write(fmt["item"])
            args.output.write(fmt["start"])
            for label, text in items:
                args.output.write(leader.format(label=label,
                                                text=text(item).rstrip()))

            args.output.write(fmt["end"])

        args.output.write(fmt["closer"])

    elif args.action == "test":
        logger.info("Received %s action", args.action)
    else:
        logger.error("Unknown action %s", args.action)
        sys.exit(1)



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


## Format mappings

formats = {
        "latex" : {
            "interests" : {
                "start"     : r"\begin{fields of interest}",
                "leader"    : r"\item",
                "end"       : r"\end{fields of interest}",
            },
        },
        "markdown" : {
            "interests" : {
                "start"     : "### Fields of Interest\n",
                "leader"    : "-  ",
                "end"       : "",
            },
        },
    }

_subparsers = (
        ("interests", "Process interests",
         """Locate the 'interests' tag and format the subsequent list
         into an itemized list.  The LaTeX wraps the list in the
         ``fields of interest`` environment while the Markdown generates
         a level 3 header followed by a list.
         """),
        ("test", "A dummy second parser", "A do nothing parser"),
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

    subparsers = parser.add_subparsers(dest="action",
                                       help="Action to take")
    for name, help, desc in _subparsers:
        s = subparsers.add_parser(name, help=help, description=desc)
        s.add_argument("input", type=argparse.FileType("r"),
                       help="Input YAML resume data file")
        s.add_argument("-o", "--output", default="-",
                       type=argparse.FileType("w"),
                       help="Output file")

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

    elif args.action == "test":
        logger.info("Received %s action", args.action)
    else:
        logger.error("Unknown action %s", args.action)
        sys.exit(1)



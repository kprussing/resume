#!/usr/bin/env python3
__doc__ = """Process the projects in the YAML file and format them into
the appropriate tabular form.  The expected format is that output by the
`projects-import.py` script.
"""

import argparse
import collections
import datetime
import os
import re

import yaml

from .. import find, sanitize

formats = collections.OrderedDict({
        "latex" : {
            "header" : r"\begin{{program table}}{{{0}}}",
            "sep" : "&",
            "nl" : r"\newline",
            "eol" : r"\\",
            "rowsep" : "\\hiderowcolors\n&&\\\\\n\\showrowcolors",
            "end" : "\end{program table}",
        },
        "markdown" : {
            "header" : "### {0}",
            "sep" : "|",
            "nl" : " ",
            "eol" : "",
            "rowsep" : "",
            "end" : "",
        },
    })


_date = ["{{{{performance[{{0}}][{{1}}][{0}]:0{1}d}}}}".format(*x)
         for x in zip(("year", "month", "day"), (4, 2, 2))]
_format = """{num} {sep} Title: {sep} {title} {eol}
 {sep} Contract Number: {sep} {contract} {eol}
 {sep} Spnsor: {sep} {sponsor} {eol}
 {sep} P.I.: {sep} {PD[project]} {eol}
 {sep} Candidate's Role: {sep} {role} {eol}
 {sep} Budgetary Authority? {sep} {budget} {eol}
 {sep} Subtask Title? {sep} {subtask} {eol}
 {sep} Amount Funded for Task {sep} {amount-funded[task]} {eol}
 {sep} Amount Funded for Project {sep} {amount-funded[project]} {eol}
 {sep} Number and Rank of{nl} Persons Supervised: {sep} {number-supervised} {eol}
 {sep} Period of Performance{nl} (Project): {sep} """ \
         + "-".join(_date).format("project", 0) + " -- " \
         + "-".join(_date).format("project", 1) + """ {eol}
 {sep} Period of Performance{nl} (Candidate): {sep} """ \
         + "-".join(_date).format("candidate", 0) + " -- " \
         + "-".join(_date).format("candidate", 1) + """ {eol}
 {sep} Contributions: {sep} {contributions} {eol}
"""

# Define the parameters for filtering the projects.  Each table has a
# separate title, and needs a method to identify the appropriate
# projects.
_me = ("Prussing,? Keith F[.]?", "Keith F[.]? Prussing")
_leader = lambda p: any(re.match(m, e) for m in _me
                                       for e in p["PD"].values()) \
                    or any(re.match(r, p["role"])
                           for r in ("Program manager",
                                     "Project Director",
                                     "Principal Investigator",
                                     "Co-Project Director",
                                     "Co-Principal Investigator",
                                     "Task Leader")) \
                    or any(p.get(k, False) for k in ("leader",
                                                     "manager"))
_external = lambda p: (re.match("[Dd]", p["project"]) \
                       or p.get("external", False)) \
                      and not p.get("omit", False)
_internal = lambda p: (re.match("[Ii]", p["project"]) \
                       or p.get("internal", False)) \
                      and not p.get("omit", False)

_tables = collections.OrderedDict({
        "external-leader" : {
            "title" : "Externally Sponsored Programs in which Candidate"
                      " was a Supervisor (PD, PI, Task Leader)",
            "filter" : lambda p: _external(p) and _leader(p),
        },
        "external-non-leader" : {
            "title" : "Other Externally Sponsored Programs to which the"
                      " Candidate Contributed",
            "filter" :  lambda p: _external(p) and not _leader(p),
        },
        "internal-leader" : {
            "title" : "Internally Funded Programs (GT or GTRI) for"
                      " which the Candidate was a supervisor (PD, PI,"
                      " or Task Leader)",
            "filter" : lambda p: _internal(p) and _leader(p),
        },
        "internal-non-leader" : {
            "title" : "Other Internally Funded Programs to which the"
                      " the Candidate Contributed",
            "filter" : lambda p: _internal(p) and not _leader(p),
        },
    })

# A function to sort projects.  We first search by priority if set.
# Then, we sort by the dates which I worked on the project (end followed
# by start) followed by the project date.  The priority allows us to
# force a sort; larger numbers indicate a higher priority.
_key = lambda p: (-p.get("priority", 50),
                  datetime.date(**p["performance"]["candidate"][1]),
                  datetime.date(**p["performance"]["candidate"][0]),
                  datetime.date(**p["performance"]["project"][1]),
                  datetime.date(**p["performance"]["project"][0]))

if __name__ == "__main__":
    prog = ".".join(__file__.split(os.sep)[-3:-1])
    parser = argparse.ArgumentParser(prog=prog, description=__doc__)
    parser.add_argument("input", type=argparse.FileType("r"),
                        help="Input YAML project file")
    parser.add_argument("-o", "--output", default="-",
                        type=argparse.FileType("w"),
                        help="Output file")
    parser.add_argument("-t", "--to", choices=formats.keys(),
                        default="latex", help="Output format")
    parser.add_argument("--table", choices=_tables.keys(),
                        help="The specific table to generate")
    args = parser.parse_args()

    projects = sanitize(find(yaml.safe_load(args.input), "projects"))
    projects.sort(key=_key, reverse=True)
    fmt = formats[args.to]

    for table in (args.table,) if args.table else _tables.keys():
        info = _tables[table]
        args.output.write(fmt["header"].format(info["title"]) + "\n")
        for p, proj in enumerate(p for p in projects if info["filter"](p)):
            if p > 0:
                args.output.write(fmt["rowsep"] + "\n")

            args.output.write(_format.format(num=p+1, **fmt, **proj))

        args.output.write(fmt["end"] + "\n\n")


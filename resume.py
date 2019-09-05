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
passed through Pandoc.  The key search described by the subcommands is
done recursively.  Meaning keys may be nested under higher level keys if
so desired.

_gtpromote: https://github.gatech.edu/kprussing3/gtpromote
_Pandoc: https://pandoc.org
"""

import argparse
import datetime
import collections
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
    if data is None or isinstance(data, (str, bytes)):
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


def years(p):
    """Format the duration replacing a missing end year with 'present'
    and collapsing single years
    """
    if len(p["years"]) > 1:
        if p["years"][0] == p["years"][1]:
            second = ""
        else:
            second = "--{years[1]}"
    else:
        second = "--present"

    return ("{years[0]}" + second).format(**p)


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
            "professional-activities" : {
                "header" : r"\subsection{{{0}}}",
                "name" : lambda c, url: r"\href{{{URL}}}{{{name}}}" \
                                        if url and "URL" in c else "{name}",
                "start" : "\\begin{enumerate}[nosep]\n",
                "leader" : r"\item ",
                "end" : r"\end{enumerate}",
            },
            "projects" : {
                "header" : r"\begin{{program table}}{{{0}}}",
                "sep" : "&",
                "nl" : r"\newline",
                "eol" : r"\\",
                "rowsep" : "\\hiderowcolors\n&&\\\\\n\\showrowcolors",
                "end" : "\end{program table}",
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
            "professional-activities" : {
                "header" : "## {0}",
                "name" : lambda c, url: r"[{name}]({URL})" \
                                        if url and "URL" in c else "{name}",
                "start" : "",
                "leader" : "1.  ",
                "end" : "",
            },
            "projects" : {
                "header" : "### {0}",
                "sep" : "|",
                "nl" : " ",
                "eol" : "",
                "rowsep" : "",
                "end" : "",
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
outreach-and-service:
  professional-activities:
  - name: International Society for Optics and Photonics
    URL: http://spie.org/
    positions:
    - status: Member
      years:
      - 2018
      - present
  - name: American Association for the Advancement of Science
    positions:
    - status: Member
      years:
      - 1990
  - name: Atlanta Section of IEEE
    positions:
    - status: Treasurer
      years:
      - 1984
      - 1985
      notes: Elected position
    - status: Program Chairman
      years:
      - 1983
      - 1984
      notes: Appointed position.
  - name: Joint Group Chapter
    positions:
    - status: Chairman of Houston IEEE
      years:
      - 1982
      - 1982
...
""",
    }

project_tables =  collections.OrderedDict({
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
        ("professional-activities",
         "Format the professional activities",
         """Extract the professional activities from the YAML file and
         format them for the CV.  The default top level key is
         'professional-activities'; however, the format is the same for
         the 'on-campus-activities'.  Each entry in the list should
         contain a 'name' and 'positions'.  The 'positions is an array
         listing the 'status' and 'years' (start and end) for the given
         position.  If a membership or position is current, 'present'
         is allowed in the end date.  The items are sorted first based
         on 'name' and then by decreasing date with 'present' being
         newest.  If a 'URL' is present, the society name is typeset
         with a hyperlink.  The 'title', if given, is typeset as a level
         two header.
         """,
         (("--key", dict(default="professional-activities",
                         help="The field containing the target data")),
          ("--title", dict(type=str,
                           help="Title to place in the subsection macro")),
          ("--itemize", dict(action="store_true",
                             help="Generate a bulleted list"))),
        ),
        ("projects", "Format the projects into a table",
         """Process the projects in the YAML file and format them into
         the appropriate tabular form.  The expected format is that
         output by the `projects-import.py` script.
         """,
         (("--table", dict(choices=project_tables.keys(),
                           help="The specific table to generate")),)
        ),
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
            out = output if output != "-" else sys.stdout
            out.write(_examples[namespace.key])
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

    elif args.action  == "professional-activities":
        # Update the details if we want an itemized list.
        if args.itemize:
            if args.to == "latex":
                fmt["start"] = re.sub("enumerate", "itemize",
                                          fmt["start"])
                fmt["end"] = re.sub("enumerate", "itemize",
                                        fmt["end"])
            elif args.to == "markdown":
                fmt["leader"] = "-   "

        data = sanitize(find(yaml.safe_load(args.input), args.key))
        products = sorted(data,
                          key=lambda p: p["name"])
        args.output.write(fmt["header"].format(args.title) + "\n\n"
                          if args.title else "")
        args.output.write(fmt["start"])
        formatter = lambda a, p, url: (
                "{status}, {name}, " + years(p) \
                + (", {notes}" if "notes" in p else "")
            ).format(name=fmt["name"](a, url).format(**a), **p)
        lines = [fmt["leader"] + formatter(a, p, args.url)
                 for a in data
                 for p in sorted(a.get("positions", []),
                                 key=lambda p: str(p["years"][1])
                                               if len(p["years"]) > 1
                                               else "present",
                                 reverse=True)]
        args.output.write("\n".join([l + ("" if l[-1] == "." else ".")
                                     for l in lines]))
        args.output.write("\n" + fmt["end"] + "\n")

    elif args.action == "projects":
        _date = ["{{{{performance[{{0}}][{{1}}][{0}]:0{1}d}}}}".format(*x)
                 for x in zip(("year", "month", "day"), (4, 2, 2))]
        table_format = """{num} {sep} Title: {sep} {title} {eol}
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

        # Define the parameters for filtering the projects.  Each table
        # has a separate title, and needs a method to identify the
        # appropriate projects.
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

        # A function to sort projects.  We first search by priority if set.
        # Then, we sort by the dates which I worked on the project (end followed
        # by start) followed by the project date.  The priority allows us to
        # force a sort; larger numbers indicate a higher priority.
        _key = lambda p: (-p.get("priority", 50),
                          datetime.date(**p["performance"]["candidate"][1]),
                          datetime.date(**p["performance"]["candidate"][0]),
                          datetime.date(**p["performance"]["project"][1]),
                          datetime.date(**p["performance"]["project"][0]))

        # Pull and sort the data
        data = sanitize(find(yaml.safe_load(args.input), "projects"))
        projects = sorted(data, key=_key, reverse=True)

        for table in (args.table,) if args.table \
                                   else project_tables.keys():
            info = project_tables[table]
            args.output.write(fmt["header"].format(info["title"]) + "\n")
            for p, proj in enumerate(p for p in projects
                                             if info["filter"](p)):
                if p > 0:
                    args.output.write(fmt["rowsep"] + "\n")

                args.output.write(table_format.format(num=p+1, **fmt, **proj))

            args.output.write(fmt["end"] + "\n\n")

    else:
        logger.error("Unknown action %s", args.action)
        sys.exit(1)



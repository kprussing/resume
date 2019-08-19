#!/usr/bin/env python3
__doc__ = """Format my list of professional activities.  Just like
everything else, these are stored in a YAML file.  The top level key we
are looking for is `professional-activities'.  This field contains an
array with fields `name' and `positions'.  The `positions' field is an
array listing the `status' and `years' (start and end) for the given
position.  If a membership or position is current, `present' is allowed
in the end date.  The items are sorted based first by the `name' and
then by decreasing end date with `present' being the newest.  If a URL
is present, the society name is typeset as a hyperlink.  The default
output is LaTeX, but native Markdown is also supported.  The title, if
provided on the command line, is typeset as a `\subsection` for LaTeX
output and a level 2 header for Markdown.  The optional key can be used
to change the top level key for which the script searches.  The
structure of the contents and output if the new key must be the same as
the `professional-activities'.  All keys not used are simply ignored.
See the `example' flag for a reference input file.
"""

import argparse
import datetime
import sys

import yaml

_example = """---
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
"""

formats = {
        "latex" : {
            "header" : r"\subsection{{{0}}}",
            "name" : lambda c, url: r"\href{{{URL}}}{{{name}}}" \
                                    if url and "URL" in c else "{name}",
            "start" : "\\begin{itemize}[nosep]\n",
            "leader" : r"\item ",
            "end" : r"\end{itemize}",
        },
        "markdown" : {
            "header" : "## {0}",
            "name" : lambda c, url: r"[{name}]({URL})" \
                                    if url and "URL" in c else "{name}",
            "start" : "",
            "leader" : "-   ",
            "end" : "",
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
    parser.add_argument("--key", default="professional-activities",
                        help="The field containing the activities")
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
    args.output.write(format_["header"].format(args.title) + "\n\n"
                      if args.title else "")
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

    activities = sorted(find(yaml.safe_load(args.input), args.key),
                        key=lambda a: a["name"])
    args.output.write(format_["start"])
    def years(p):
        """Format the duration replacing a missing end year with
           'present' and collapsing single years
        """
        if len(p["years"]) > 1:
            if p["years"][0] == p["years"][1]:
                second = ""
            else:
                second = "--{years[1]}"
        else:
            second = "--present"

        return ("{years[0]}" + second).format(**p)

    formatter = lambda a, p, url: (
            "{status}, {name}, " + years(p) \
            + (", {notes}" if "notes" in p else "")
        ).format(name=format_["name"](a, url).format(**a), **p)
    lines = [format_["leader"] + formatter(a, p, args.url)
             for a in activities
             for p in sorted(a.get("positions", []),
                             key=lambda p: str(p["years"][1])
                                           if len(p["years"]) > 1
                                           else "present",
                             reverse=True)]
    args.output.write("\n".join([l + ("" if l[-1] == "." else ".")
                                 for l in lines]))
    args.output.write("\n" + format_["end"] + "\n")


#!/usr/bin/env python3
__doc__ = r"""Extract the short courses from the YAML and put it into a
LaTeX table.  The generated table uses the ``tabuarx`` format, and the
width of the table is set to ``\textwidth - \leftskip``.  Further, the
underlining of the headers makes use of the ``\cmidrule`` from
``booktabs``.  By default, the date is written using common
abbreviation.  The ISO 8601 format can be toggled on with the
appropriate flag.  The format of the YAML file requires a top level key
`short-courses' which contains an array for each course.  Each course
has `name' and `sessions' fields.  The sessions must have a `year',
`month', `day', and `role'.  If a URL is provided for a course, the
course will be typeset as a hyperlink.  If a session has a list of
`lectures', these can be typeset as a list in the same cell as the
course title.  All other fields will be ignored.  Use the `example' flag
to produce a minimal example for reference.
"""

import argparse
import datetime
import sys

import yaml

_example ="""---
short-courses:
  - name: Infrared/Visible Signature Suppression
    URL: https://pe.gatech.edu/courses/infraredvisible-signature-suppression
    sessions:
    - year: 2017
      month: 9
      day: 13
      role: Course administrator
  - name: Target Tracking in Sensor Systems - Infrared Search and Track
    URL: https://pe.gatech.edu/courses/target-tracking-sensor-systems
    sessions
    - year: 2018
      month: 8
      day: 28
      role: Course lecturer
      lectures:
      - Infrared Search and Track
...
"""

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=argparse.FileType("r"),
                        help="Input YAML course list")
    parser.add_argument("-o", "--output", default="-",
                        type=argparse.FileType("w"),
                        help="Target output file")
    parser.add_argument("-e", "--example", action="store_true",
                        help="Dump an example YAML input")
    parser.add_argument("--iso", action="store_true",
                        help="Write date in ISO 8601 format")
    parser.add_argument("--title", type=str,
                        help="Title to place in the subsection macro")
    parser.add_argument("--lectures", action="store_true",
                        help="Typeset the lectures with the course")
    parser.add_argument("--no-url", action="store_false", dest="url",
                        help="Disable creating hyperlinks for titles")
    parser.add_argument("-t", "--to", choices={"latex", "markdown"},
                        default="latex", help="The output format")
    args = parser.parse_args()

    if args.example:
        args.output.write(_example)
        sys.exit(0)

    courses = yaml.safe_load(args.input)
    if args.to == "latex":
        name = lambda c: r"\href{{{URL}}}{{{name}}}" \
                if args.url and "URL" in c else "{name}"
        lectures = lambda s: ["",
                r"\begin{itemize}[nosep]",
                *[r"\item {0}".format(l) for l in s["lectures"]],
                r"\end{itemize}"
                ] if args.lectures and s.get("lectures", []) \
                  else []
    elif args.to == "markdown":
        name = lambda c: "[{name}]({URL})" if args.url and "URL" in c \
            else "{name}"
        lectures = lambda s: ["", *[f"-   {_}" for _ in s["lectures"]]
                              ] if args.lectures and s.get("lectures", []) \
                             else []
    else:
        raise NotImplementedError

    info = [dict(name=name(c).format(**c) + "\n".join(lectures(s)),
                 role=s["role"],
                 date=datetime.date(s["year"], s["month"], s["day"]))
            for c in courses["short-courses"] for s in c["sessions"]]


    datefmt = "{date:%Y-%m-%d}" if args.iso \
        else "{date.day} {date:%b} {date:%Y}"
    if args.to == "latex":
        args.output.write("\\subsection{{{0}}}\n\n".format(args.title)
                          if args.title else "")
        header = "\n".join([r"\begin{{longtable}}"
                            r"{{p{{0.8in}}p{{\dimexpr\textwidth-\leftskip-1.8in}}p{{1.0in}}}}",
                            r"{0} & {1} & {2} \\",
                            r"\cmidrule(lr){{1-1}}"
                            r"\cmidrule(lr){{2-2}}"
                            r"\cmidrule(lr){{3-3}}"
                            ])
        args.output.write(header.format(r"\textbf{Date}",
                                        r"\textbf{Course}",
                                        r"\textbf{Contribution}"))
        line = datefmt + "& {name} & {role}"
        text = [line.format(**c) for c in sorted(info,
                                                 key=lambda c: c["date"],
                                                 reverse=True)]
        args.output.write("\n" + "\\\\\n".join(text) + "\n")
        args.output.write(r"\end{longtable}")
    elif args.to == "markdown":
        args.output.write(f"## {args.title}\n\n" if args.title else "")
        datelen = max(len(datefmt.format(**_)) for _ in info)
        rolelen = max(len(_["role"]) for _ in info)
        namelen = max(
            max(len(line.rstrip()) for line in _["name"].splitlines())
            for _ in info
        )
        print(datelen, rolelen, namelen)
        line = "| " + " | ".join([f"{{0:{datelen}s}}", f"{{1:{namelen}s}}",
                           f"{{2:{rolelen}s}}"])  + " |"
        args.output.write("+:" + "-" * (datelen + 1) +
                          "+:" + "-" * (namelen + 1) +
                          "+:" + "-" * (rolelen + 1) +
                          "+\n" +
                          line.format("**Date**",
                                      "**Course**",
                                      "**Contribution**") + "\n" +
                          "+" + "-" * (datelen + 2) +
                          "+" + "-" * (namelen + 2) +
                          "+" + "-" * (rolelen + 2) +
                          "+\n"
                          )

        for item in sorted(info, key=lambda _: _["date"], reverse=True):
            lines = item["name"].splitlines()
            args.output.write(line.format(datefmt.format(**item),
                                          lines[0], item["role"]) +
                              "\n" + line.format("", "", "") + "\n" +
                              "\n".join([line.format("", _, "")
                                         for _ in lines[1:]]) + "\n" +
                              "+" + "-" * (datelen + 2) +
                              "+" + "-" * (namelen + 2) +
                              "+" + "-" * (rolelen + 2) +
                              "+\n"
                              )
    else:
        raise NotImplementedError

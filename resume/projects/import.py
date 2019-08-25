#!/usr/bin/env python3
__doc__ = """Process a dump from the 'Charge Activity Report by Employee
- Project Detail Information' report from Webwise.  We only need the
table view because we simply want to extract the fields.  For this to
work, we _must_ have the table headers.  Those are used as the keys in
the YAML formatting. 
"""

import argparse
import datetime
import os
import re

import yaml

_reference_format = """  - title: {Project Title}
    project: {Project}
    contract: {Contract No}
    sponsor: {Sponsor}
    PD:
      project: {PD of Project}
      subtask: {PD of Subtask}
    role: '[Program manager, P.D./P.I., Co-P.I./P.D. Task leader]'
    budget: '[Did Candidate have budgetary authority?]'
    subtask: {Subtask Title}
    amount-funded:
      task: {Budget of Subtask}
      project: {Funded Amount includes Fee}
    number-supervised: '[15 (3 PRE, 1 SRE, 1 REII, 1 RE1, 9 students)]'
    performance:
      project:
        - year: {Contract Start Date.year}
          month: {Contract Start Date.month}
          day: {Contract Start Date.day}
        - year: {Contract End Date.year}
          month: {Contract End Date.month}
          day: {Contract End Date.day}
      candidate:
        - year: {Employee First Month Worked on Project.year}
          month: {Employee First Month Worked on Project.month}
          day: {Employee First Month Worked on Project.day}
        - year: {Employee Last Month Worked on Project.year}
          month: {Employee Last Month Worked on Project.month}
          day: {Employee Last Month Worked on Project.day}
    hours-worked: {Total Hours Worked}
    contributions: '[Briefly describe you contributions in 2--3 sentences.]'
"""

# These were part of an attempt to update a reference YAML with new
# information from the table, but I think that's going to take too much
# effort.  Maybe we'll do that, but not now.
# _empty_row = {
        # "title"                 : "",
        # "project"               : "",
        # "contract"              : "",
        # "sponsor"               : "",
        # "PD-project"            : "",
        # "PD-subtask"            : "",
        # "role"                  : "'[Program manager, P.D./P.I., Co-P.I./P.D.  Task leader]'",
        # "budget"                : "'[Did Candidate have budgetary authority?]'",
        # "subtask"               : "",
        # "amount-funded-task"    : "",
        # "amount-funded-project" : "",
        # "number-supervised"     : "'[15 (3 PRE, 1 SRE, 1 REII, 1 RE1, 9 students)]'",
        # "contract-start"        : None,
        # "contract-end"          : None,
        # "candidate-start"       : None,
        # "candidate-end"         : None,
        # "hour-worked"           : "",
        # "contributions"         : "'[Briefly describe you contributions in 2--3 sentences.]'",
    # }

# _from_to_keys = (
        # ("Project Title", "title"),
        # ("Project", "project"),
        # ("Contract No", "contract"),
        # ("Sponsor", "sponsor"),
        # ("PD of Project", "pd-project"),
        # ("PD of Subtask", "pd-subtask"),
        # ("Subtask Title", "subtask"),
        # ("Budget of Subtask", "amount-funded-task"),
        # ("Funded Amount includes Fee", "amount-funded-project"),
        # ("Contract Start Date", "contract-start"),
        # ("Contract End Date", "contract-end"),
        # ("Employee First Month Worked on Project", "candidate-start"),
        # ("Employee Last Month Worked on Project", "candidate-end"),
        # ("Total Hours Worked", "hour-worked"),
    # )

# This is the worked out regular expression for copying the vita
# view over.  All of the information is in the table and it's easier
# to parse that.  But I don't want to loose the careful work I did
# to figure this out.
# pattern = re.compile(r"\s*\d+\s*" \
        # + r"Project\s*Title\s*(?P<title>[-&\w\s]+)" \
        # + r"Contract\s*No(?:[.]|umber)\s*(?P<contract>[\w-]*)\s*" \
        # + r"Sponsor\s*(?P<sponsor>[-&\w/\s]+)\s*" \
        # + r"P[.]\s*I[.]\s*(?P<pi>[\w,\s]+)" \
        # + r"Candidate['’]s\s+Role\s*(?P<role>[\w\s-]*)" \
        # + r"Budgetary\s*Authority[?]\s*(?P<budget>\w*)\s*" \
        # + r"Subtask\s*Title[?]?\s*(?P<subtask>[-&\w\s]*)" \
        # + r"Amount\s*Funded\s*for\s*Task:?\s*(?P<task_amount>\$[\d,.]+)?\s*" \
        # + r"Amount\s*Funded\s*for\s*Project:?\s*(?P<project_amount>\$[\d,.]+)?\s*" \
        # + r"Number\s*and\s*Rank\s*of\s*Persons\s*Supervised:?\s*(?P<supervised>[\w\s]*)" \
        # + r"Period\s*of\s*Performance\s*\(Project\):?\s*(?P<project_performance>[-/\d\s]*)" \
        # + r"Period\s*of\s*Performance\s*\(Candidate\):?\s*(?P<candidate_performance>[-/\d\s]*)" \
        # + r"Contributions:?\s*(?P<contributions>\w|\s)*"
        # )

# We define two entries as the same if they have the same entries
# same_entry = lambda l, r: all(l[k] == r[k] for k in ("title",
                                                     # "subtask",
                                                     # "contract"))

if __name__ == "__main__":
    prog, _ = os.path.splitext(".".join(__file__.split(os.sep)[-3:]))
    parser = argparse.ArgumentParser(prog=prog, description=__doc__)
    parser.add_argument("-o", "--output", default="-",
                        type=argparse.FileType("w"),
                        help="Output file")
    parser.add_argument("table", type=argparse.FileType("r"),
                        help="Input table view")
    args = parser.parse_args()

    keys = [k.strip() for k in args.table.readline().split("\t")]
    func = lambda k, x: datetime.datetime.strptime(x, "%m/%d/%Y") \
            if k in keys[-4:] else x
    args.output.write("projects:\n")
    for line in args.table:
        row = {k:func(k, e.strip())
               for k, e in zip(keys, line.split("\t"))}
        args.output.write(_reference_format.format(**row))


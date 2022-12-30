#!/usr/bin/env python3
__doc__ = """Import new publications from a bibliography exported from
Zotero.  This runs ``pandoc-citeproc`` on the given BibLaTeX file and
the separates each key into a file based on the ``id``.  This will
overwrite any file with the same name by default.  This will inspect the
environment variable ``PANDOC_CITEPROC`` for the user specified path to
``pandoc-citeproc``.  Otherwise, it uses the default search path.  Note,
this assumes the output format of ``pandoc-citeproc`` places the entries
under 'references' map and each reference is a list that has a first
element of 'id'.  This does not actually parse the YAML in so that the
``pandoc-citeproc`` ordering is preserved.
"""

import argparse
import os
import re
import subprocess
import sys

import yaml

_default = os.path.join(os.environ["HOME"],
                        "Downloads",
                        "Exported Items.bib")
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("bibliography", nargs="?", default=_default,
                    help="Input BibLaTeX file: %(default)s")
parser.add_argument("-d", "--dir", default=os.curdir,
                    help="Output directory: %(default)s")
parser.add_argument("-i", "--interactive", action="store_true",
                    help="Ask before overwriting existing files")

args = parser.parse_args()

if not os.path.exists(args.bibliography):
    sys.exit(f"BibLaTeX file '{args.bibliography}' does not exist")

cmd = ["pandoc", "--from=biblatex", "--to=markdown", "--standalone",
        args.bibliography]
proc = subprocess.run(cmd, capture_output=True, text=True, check=True)
if proc.returncode != 0:
    sys.exit(f"Error running '{cmd}'\n" + proc.stderr)

inputs = yaml.safe_load(re.sub("---\n+$", "...",
                               re.sub("{(.+)}", r"\1", proc.stdout),
                               re.MULTILINE))

for item in inputs["references"]:
    fname = os.path.join(args.dir, item["id"] + ".yaml")
    overwrite = True
    if args.interactive and os.path.exists(fname):
        while True:
            inp = input(f"File '{fname}' exists. Overwrite? [Y/n] ")
            if inp == "" or inp.lower() == "y":
                break
            elif inp.lower() == "n":
                overwrite = False
                break

    if overwrite:
        with open(fname, "w") as fid:
            yaml.safe_dump(item, fid, explicit_start=True, explicit_end=True)

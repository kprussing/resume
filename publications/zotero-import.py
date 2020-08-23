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

cmd = [os.environ.get("PANDOC_CITEPROC", "pandoc-citeproc"),
       "--bib2yaml", args.bibliography]
proc = subprocess.run(cmd, universal_newlines=True,
                      stdout=subprocess.PIPE,
                      stderr=subprocess.PIPE)
if proc.returncode != 0:
    sys.exit(f"Error running '{cmd}'\n" + proc.stderr)

output = None
start = 0
for line in proc.stdout.split("\n"):
    if line.strip() == "":
        continue

    if re.match("^[.]{3}$", line):
        break

    match = re.match(r"(.*)id:\s*([\w-]+)", line)
    if match:
        if output:
            output.write("...")
            output.close()

        start = len(match.group(1))
        fname = os.path.join(args.dir, match.group(2) + ".yaml")

        overwrite = True
        if args.interactive and os.path.exists(fname):
            while True:
                inp = input(f"File '{fname}' exists. Overwrite? [Y/n] ")
                if inp == "" or inp.lower() == "y":
                    overwrite = True
                    break
                if inp.lower() == "n":
                    overwrite = False
                    break

        if overwrite:
            output = open(fname, "w")
            output.write("---\n")
        else:
            output = None

    if output:
        output.write(line[start:] + "\n")

if output:
    output.write("...")
    output.close()


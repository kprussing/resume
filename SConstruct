#!/usr/bin/env python 
"""The script to build my resumes."""

import os
import re

try:
    Import("env")
except:
    env = Environment(ENV=os.environ, tools=["default", "pandoc"])

Export("env")
pubs = SConscript(os.path.join("publications", "SConscript"))

# Define how to generate the table of short courses
data = "kprussing.yaml"
short_courses = env.Command("short-courses.tex",
                            ["short-courses.py", data],
                            action="python3 ${SOURCES[0]} $FLAGS "
                                   "-o ${TARGET} ${SOURCES[1]}",
                            FLAGS="--lectures "
                                  "--title 'Continuing Education Courses Taught'")

def short_courses_tex2md(target, source, env):
    """Screen out the rule lines from the table

    This will write an optional subsection title before the table if the
    'section' keyword in found in `env`.
    """
    import re, subprocess
    with open(str(source[0]), "r") as src:
        lines = [l for l in src.readlines()
                 if not re.search("cmidrule", l)]

    with open(str(target[0]), "w") as tgt:
        tgt.write(subprocess.run([env["PANDOC"], "-f", "latex",
                                                 "-t", "markdown"],
                                 universal_newlines=True,
                                 input="".join(lines),
                                 check=True,
                                 stdout=subprocess.PIPE).stdout)

short_courses.extend(env.Command("short-courses.md", short_courses,
                                 action=short_courses_tex2md))

activities = {
        "professional-activities" : {
            "title"  : "'Professional Activities'",
            "files"  : [],
            "script" : "professional-activities.py",
        },
        "on-campus-committees" : {
            "title" : "'On Campus Committees'",
            "files" : [],
            "script" : "professional-activities.py",
        },
        "key-delivered-products" : {
            "title" : "'Key Delivered Products'",
            "files" : [],
            "script" : "delivered-products.py",
        },
    }
for key, vals in activities.items():
    for ext, fmt in ((".md", "markdown"), (".tex", "latex")):
        pa = env.Command(key + ext, [vals["script"], data],
                         action="python3 ${SOURCES[0]} $FLAGS "
                                "-o ${TARGET} ${SOURCES[1]}",
                         FLAGS="--to " + fmt + " --key " + key
                              + " --title " + vals["title"])
        vals["files"].extend(pa)

srcs = ["index.md", "experience.md", "awards.md"] \
    + pubs \
    + [dp for dp in activities["key-delivered-products"]["files"]
          if re.search("[.]md$", str(dp))] \
    + ["projects.md"] \
    + [sc for sc in short_courses if re.search("[.]md$", str(sc))] \
    + [x + ".md" for x in ("skills", "education",)] \
    + [pa for pa in activities["professional-activities"]["files"]
          if re.search("[.]md$", str(pa))] \
    + [pa for pa in activities["on-campus-committees"]["files"]
          if re.search("[.]md$", str(pa))] \
    + [x + ".md" for x in ("old-work", "footer")]

css = " ".join(["--css={0}.css".format(File(x).path)
                for x in ("website-colors", "style")])

env.Pandoc(os.path.join("doc", "full.html"), srcs,
           PANDOCFLAGS="--self-contained " + css)
env.Pandoc(os.path.join("doc", "short.html"), "short.text",
           PANDOCFLAGS="--self-contained --css=short.css")

try:
    Export("pubs tex")
except:
    pass

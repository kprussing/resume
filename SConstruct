#!/usr/bin/env python
"""The script to build my resumes."""

import os
import re

try:
    Import("env")
except:
    env = Environment(ENV=os.environ, tools=["default", "pandoc"])

merge_yaml = File("merge-yaml.py")
Export("env merge_yaml")
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
        "interests" : {
            "files" : [],
        },
        "professional-activities" : {
            "title"  : "'Professional Activities'",
            "files"  : [],
        },
        "on-campus-committees" : {
            "title" : "'On Campus Committees'",
            "files" : [],
            "action" : "professional-activities",
            "key" : "on-campus-committees",
        },
        "key-delivered-products" : {
            "title" : "'Key Delivered Products'",
            "files" : [],
            "action" : "delivered-products"
        },
        "irad-efforts" : {
            "title" : "'Independent Research and Development Efforts/Other Significant Technical Innovation'",
            "files" : [],
            "action" : "delivered-products",
            "key" : "irad-efforts",
        },
        "professional-development" : {
            "files" : [],
            "action" : "name-date",
            "key" : "professional-development",
        },
        "proposals-external" : {
            "files" : [],
            "action" : "proposals",
        },
        "proposals-internal" : {
            "files" : [],
            "action" : "proposals",
            "flags" : "--internal",
        },
    }

action = "python3 ${SOURCES[0]} --to $fmt $OPTS $key $FLAGS " \
         "--output ${TARGET} ${SOURCES[1]}"
for key, vals in activities.items():
    for ext, fmt in ((".md", "markdown"), (".tex", "latex")):
        FLAGS = ("--title " + vals["title"] if "title" in vals else "") \
              + ((" --key " + key if vals.get("key", "") else "")
                                  if "action" in vals else"") \
              + " " + vals.get("flags", "")
        pa = env.Command(key + ext, [File("resume.py"), data],
                         action=action, fmt=fmt, FLAGS=FLAGS,
                         key=vals["action"] if "action" in vals else key,
                         )
        vals["files"].extend(pa)

yaml = []
action = "python3 ${SOURCES[0]} -o $TARGET --label $label ${SOURCES[1:]}"
for root in ("proposals",):
    _ = SConscript(os.path.join(root, "SConscript"))
    yaml.extend( env.Command(root + ".yaml", [merge_yaml] + _,
                             action=action, label=root) )

srcs = ["index.md"] \
    + [fi for fi in activities["interests"]["files"]
          if re.search("[.]md$", str(fi))] \
    + ["experience.md", "awards.md"] \
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

index = env.Pandoc(os.path.join("docs", "index.html"), srcs,
                   PANDOCFLAGS="--self-contained " + css)
env.Pandoc(os.path.join("docs", "short.html"), "short.text",
           PANDOCFLAGS=["--self-contained", "--css", File("short.css")])

try:
    Export("pubs tex")
except:
   Default(index)


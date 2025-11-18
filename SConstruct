#!/usr/bin/env python
"""The script to build my resumes."""

import os
import re

env = Environment(ENV=os.environ,
                  )
index = env.Command(os.path.join("docs", "index.html"),
                    ["style.css", "website-colors.css",
                     "metadata.yml", "bio.md", "fields-of-interest.md",
                     "education.md", "experience.md", "short-courses.md",
                     "publications.md", "projects.md", "outreach.md",
                     "skills.md"],
                    action="pandoc -F pandoc-acro --embed-resources --standalone -o $TARGET -c ${SOURCES[0]} -c ${SOURCES[1]} ${SOURCES[2:]}"
                    )
env.Command("prussing-resume-body.tex",
            ["metadata.yml", "bio.md", "fields-of-interest.md",
             "education.md", "experience.md", "short-courses.md",
             "publications.md", "projects.md", "outreach.md",
             "skills.md"],
            action="pandoc -F pandoc-acro -F latex-filter.py -o $TARGET ${SOURCES}"
            )
pdf = env.PDF("prussing-resume.tex")

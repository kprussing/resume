#!/usr/bin/env python3
__doc__ = """A filter for generating a paper list under a section.  This
filter processes the 'references' field in the metadata block to remove
all bibliography items that do not match the key(s) given in the
'paper-keys' metadata field.

"""

#
# Copyright (c) 2019, Keith F. Prussing
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
#
#     1. Redistributions of source code must retain the above copyright
#     notice, this list of conditions and the following disclaimer.
#
#     2. Redistributions in binary form must reproduce the above
#     copyright notice, this list of conditions and the following
#     disclaimer in the documentation and/or other materials provided
#     with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#

import datetime
import panflute

_DEBUG = False

def start(item):
    """Extract the start date from the 'issued' field

    If 'issued' is not a key in the bibliography file, return ``None``.
    If the month or day is not specified in the field, we set the value
    to the first month or day as appropriate.

    """
    # Grab the issued field.
    issued = item.get("issued", None)
    if not issued:
        return issued

    # Now we need to figure out if we have a 'date-parts' or a list
    # of :class:`panflute.MetaMap`s`.  In either case, we only worry
    # about the first element which is the start date.
    if isinstance(issued, list):
        field = lambda x: issued[0].get(x, 1)
        y, m, d = [int(field(x)) for x in ("year", "month", "day")]
    else:
        panflute.debug("start: In the 'date-parts' section!")
        panflute.debug("start: This will probably break...")
        parts = issued["date-parts"][0]
        y = parts[0]
        m = parts[1] if len(parts) > 1 else 1
        d = parts[2] if len(parts) > 2 else 1

    return datetime.date(y, m, d)


def finalize(doc):
    """Filter the references"""
    if "references" not in doc.metadata:
        return

    keys = doc.get_metadata("publication-keys", [])
    if not keys:
        doc.metadata["references"] = []

    bib = doc.get_metadata("references")
    if _DEBUG:
        panflute.debug("keys {0}".format(keys))

    for item in reversed(bib):
        if _DEBUG:
            panflute.debug("id: {id}, type: {type}".format(**item))

        if not all([item.get(k, "") == v
                    for x in keys
                    for k, v in x.items()]):
            if _DEBUG:
                panflute.debug("dropping {0}".format(item["id"]))

            bib.remove(item)

    # panflute.debug("{0}".format(sorted(bib, key=start, reverse=True)))
    doc.metadata["references"] = sorted(bib, key=start, reverse=True)


# Boiler plate
def main(doc=None):
    """The main routine"""
    return panflute.run_filters([], finalize=finalize, doc=doc)

if __name__ == "__main__":
    main()

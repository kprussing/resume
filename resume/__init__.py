__doc__ = """Utilities to process my resume into a useable format.
"""

import re

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
    if data is None and isinstance(data, (str, bytes)):
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


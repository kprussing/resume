import sys
import panflute


def action(elem, doc):
    if isinstance(elem, panflute.Span):
        if len(elem.classes) > 1:
            return

        text = f"\\my{elem.classes[0]}{{{panflute.stringify(elem)}}}"
        return panflute.RawInline(text, "tex")


def main(doc=None):
    return panflute.run_filter(action, doc=doc)


if __name__ == "__main__":
    main()

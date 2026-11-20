"""Run functions copied out of the root page in node, so the page's own code is what gets tested."""
import json
import os
import re
import subprocess

HTML = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "index.html")


def page_source():
    with open(HTML, encoding="utf-8") as fh:
        return fh.read()


def run_page_js(functions, body, variables=()):
    """Run the named page functions and `var NAME = ...;` lines in node; return what the snippet logs as JSON."""
    src = page_source()
    parts = [re.search(r"\nfunction %s\([^\n]*\}\n|\nfunction %s\([\s\S]*?\n}\n" % (n, n), src).group(0) for n in functions]
    lines = [re.search(r"\nvar [^\n]*\b%s = [^\n]*\n" % v, src).group(0) for v in variables]
    out = subprocess.run(["node", "-e", "".join(parts + list(dict.fromkeys(lines))) + body], capture_output=True, text=True, timeout=30)
    return json.loads(out.stdout), out.stderr

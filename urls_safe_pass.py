#!/usr/bin/env python3
"""
urls.py safe normalization pass: whitespace + comment spacing + collapse the
one provably-dead duplicate path, with an AST semantic-equality guard.

Usage:  python urls_safe_pass.py <path-to-urls.py>

Writes ONLY if the resolved urlpatterns after the cosmetic transform are
equivalent to the original EXCEPT for collapsing exact duplicate
`path('help/', views.help_page, name='help_page')` registrations to the
first occurrence -- no reorder/rename/route/view change, nothing outside
the urlpatterns assignment altered. Any deviation aborts, no write.
Idempotent. CRLF and no-BOM preserved.
"""
import ast, difflib, re, sys

HELP_STRIPPED = "path('help/', views.help_page, name='help_page'),"
START_RE = re.compile(r'^(\s*)(path\(|re_path\(|#)')


def transform(raw_bytes):
    raw = raw_bytes.decode("utf-8")
    use_crlf = "\r\n" in raw
    norm = raw.replace("\r\n", "\n").replace("\r", "\n")
    src = norm.split("\n")
    start = next(i for i, l in enumerate(src)
                 if l.lstrip().startswith("urlpatterns") and "[" in l)
    end = next(i for i in range(start + 1, len(src)) if src[i].strip() == "]")
    out, seen_help = [], False
    for idx, line in enumerate(src):
        line = line.rstrip(" \t")
        if start < idx < end:
            m = START_RE.match(line)
            if m:
                body = line[len(m.group(1)):]
                line = "    " + body
                if body.startswith("#") and len(body) > 1 and body[1] not in (" ", "#", "!"):
                    line = "    # " + body[1:]
            if line.strip() == HELP_STRIPPED:
                if seen_help:
                    continue
                seen_help = True
        out.append(line)
    res = "\n".join(out)
    if use_crlf:
        res = res.replace("\n", "\r\n")
    return res.encode("utf-8")


def url_model(src):
    tree = ast.parse(src)
    up = None
    entries = []
    for node in tree.body:
        if (isinstance(node, ast.Assign) and len(node.targets) == 1
                and isinstance(node.targets[0], ast.Name)
                and node.targets[0].id == "urlpatterns"):
            up = node
            assert isinstance(node.value, ast.List), "urlpatterns is not a list literal"
            for el in node.value.elts:
                assert isinstance(el, ast.Call), f"non-call element: {ast.dump(el)}"
                fn = el.func.id if isinstance(el.func, ast.Name) else ast.dump(el.func)
                a0 = el.args[0] if el.args else None
                route = a0.value if isinstance(a0, ast.Constant) else (ast.dump(a0) if a0 else None)
                view = ast.dump(el.args[1]) if len(el.args) > 1 else None
                name = next((kw.value.value for kw in el.keywords
                             if kw.arg == "name" and isinstance(kw.value, ast.Constant)), None)
                entries.append((fn, route, view, name))
    assert up is not None, "no urlpatterns assignment found"
    up.value = ast.List(elts=[], ctx=ast.Load())
    return entries, ast.dump(tree)


def guard(old_b, new_b):
    eo, ro = url_model(old_b.decode("utf-8"))
    en, rn = url_model(new_b.decode("utf-8"))
    if ro != rn:
        raise AssertionError("GUARD FAIL: module structure outside urlpatterns changed")
    help_entry = next((e for e in eo if e[1] == "help/" and e[3] == "help_page"), None)
    expected, seen = [], False
    for e in eo:
        if help_entry is not None and e == help_entry:
            if seen:
                continue
            seen = True
        expected.append(e)
    if en != expected:
        raise AssertionError("GUARD FAIL: urlpatterns delta is NOT 'collapse help dup only' "
                             "(reorder / rename / route / view change detected)")
    return len(eo), len(en)


def main():
    path = sys.argv[1]
    with open(path, "rb") as f:
        old = f.read()
    new = transform(old)
    if new == old:
        print("Already normalized - no changes, no write.")
        return 0
    o, n = guard(old, new)                       # raises -> no write
    with open(path + ".bak", "wb") as f:
        f.write(old)
    with open(path, "wb") as f:
        f.write(new)
    od = old.decode().replace("\r\n", "\n").split("\n")
    nd = new.decode().replace("\r\n", "\n").split("\n")
    print("\n".join(difflib.unified_diff(od, nd, path + ".bak", path, lineterm="")))
    print(f"\nGUARD PASS - elements {o} -> {n} (removed {o-n}: only the proven help/ dead dup)")
    print(f"backup: {path}.bak | CRLF preserved: {b'\r\n' in new} | BOM: {new[:3] == b'\xef\xbb\xbf'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
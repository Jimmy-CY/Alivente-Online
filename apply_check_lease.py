import io, sys, ast, collections

target = r"pages\management\commands\check_lease_renewal_and_invoices.py"
prebak = target + ".prebak"
EXPECT_LINES = 1623

raw = io.open(target, "rb").read()
if raw[:3] == b"\xef\xbb\xbf":
    raw = raw[3:]
text = raw.decode("utf-8").replace("\r\n", "\n").replace("\r", "\n")
text = text.rstrip("\n") + "\n"            # exactly one trailing newline
out = text.replace("\n", "\r\n")
io.open(target, "wb").write(out.encode("utf-8"))

chk = io.open(target, "rb").read()
bom  = chk[:3] == b"\xef\xbb\xbf"
s    = chk.decode("utf-8")
nl   = s.count("\r\n")
tabs = s.count("\t")

prebak_txt = io.open(prebak, "rb").read().decode("utf-8")
pre_na = collections.Counter(c for c in prebak_txt if ord(c) > 127)
new_na = collections.Counter(c for c in s if ord(c) > 127)

print("BOM present      :", bom, "(want False)")
print("CRLF line count  :", nl, "(want %d)" % EXPECT_LINES)
print("tab count        :", tabs, "(want 0)")
print("non-ASCII total  : prebak=%d  written=%d" % (sum(pre_na.values()), sum(new_na.values())))

ok = True
try:
    ast.parse(s); print("AST parse        : OK")
except SyntaxError as e:
    ok = False; print("AST parse        : FAIL ->", e)

if pre_na == new_na:
    print("non-ASCII multiset: IDENTICAL to original (byte-faithful)")
else:
    ok = False
    print("non-ASCII multiset: *** MISMATCH ***")
    for ch in sorted(set(pre_na) | set(new_na), key=ord):
        a, b = pre_na.get(ch, 0), new_na.get(ch, 0)
        if a != b:
            print("   U+%04X  prebak=%d  written=%d" % (ord(ch), a, b))

if bom or nl != EXPECT_LINES or tabs != 0 or not ok:
    print("\nRESULT: FAIL  -> run the restore command")
    sys.exit(1)
print("\nRESULT: PASS  -> run manage.py check next")
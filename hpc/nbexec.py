"""Run selected code cells of a notebook in one namespace (skips ! and % lines)."""
import json, os
os.environ.setdefault("MPLBACKEND", "Agg")
def run_cells(path, cells, ns):
    nb = json.load(open(path, encoding="utf-8"))
    for i in cells:
        src = "".join(nb["cells"][i]["source"])
        src = "\n".join(l for l in src.splitlines() if not l.lstrip().startswith(("!", "%")))
        src = src.replace("DATA_DIR = None", f"DATA_DIR = {os.environ['DATA_DIR']!r}")
        print(f"######## cell {i}", flush=True)
        exec(compile(src, f"cell{i}", "exec"), ns)
    return ns

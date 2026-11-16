"""Graph ablation behind docs/RESULTS_AND_INTERPRETATION.md, Section 5: train GCN and GraphSAGE (seeds 0-4,
Role 3 settings) and score the test graph with and without its edges. Reuses the data and GCN cells of
role4_explainability.ipynb. Run from the repository root: python notebooks/role4_graph_ablation.py (~1 h on CPU)."""
import json, os, random, sys
os.chdir(os.path.dirname(os.path.abspath(__file__)))
nb = json.load(open("role4_explainability.ipynb", encoding="utf-8"))
ns = {"display": print}
for i in (2, 9):  # data cell, GCN definition+training cell (training repeated below per seed)
    src = "\n".join(l for l in "".join(nb["cells"][i]["source"]).splitlines() if not l.lstrip().startswith("%"))
    if i == 9: src = src.split("random.seed(0)")[0]
    exec(src, ns)
exec(r'''
import torch.nn.functional as F
from torch_geometric.nn import SAGEConv
from sklearn.metrics import average_precision_score

class SAGE(torch.nn.Module):
    def __init__(self, d, hid=64):
        super().__init__()
        self.c1, self.c2, self.out = SAGEConv(d, hid), SAGEConv(hid, hid), torch.nn.Linear(hid, 2)
    def forward(self, x, edge_index):
        for conv in (self.c1, self.c2):
            x = F.dropout(F.relu(conv(x, edge_index)), 0.3, self.training)
        return self.out(x)
counts = torch.bincount(train_g.y[train_g.labeled], minlength=2).float(); w = counts.sum() / (2 * counts)
none = torch.empty(2, 0, dtype=torch.long)
for cls in (GCN, SAGE):
    for seed in range(5):
        random.seed(seed); np.random.seed(seed); torch.manual_seed(seed)
        m = cls(165); opt = torch.optim.Adam(m.parameters(), lr=5e-3, weight_decay=5e-4)
        def sc(g, ei):
            m.eval()
            with torch.no_grad(): return torch.softmax(m(g.x, ei), 1)[:, 1][g.labeled].numpy()
        best, bad = -1, 0
        for ep in range(500):
            m.train(); opt.zero_grad()
            F.cross_entropy(m(train_g.x, train_g.edge_index)[train_g.labeled], train_g.y[train_g.labeled], weight=w).backward(); opt.step()
            ap = average_precision_score(val_g.y[val_g.labeled], sc(val_g, val_g.edge_index))
            if ap > best: best, bad, st = ap, 0, {k: v.clone() for k, v in m.state_dict().items()}
            else:
                bad += 1
                if bad >= 50: break
        m.load_state_dict(st); yt = test_g.y[test_g.labeled].numpy()
        print(cls.__name__, seed, "AP with edges %.3f  without %.3f" % (average_precision_score(yt, sc(test_g, test_g.edge_index)), average_precision_score(yt, sc(test_g, none))), flush=True)
''', ns)

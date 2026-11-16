"""Re-run the Role 3 notebook (sections 1-7) on a GPU node and export Role 4 prediction files."""
import os, sys; SP = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, SP)
from nbexec import run_cells
from pathlib import Path
import torch; print("cuda:", torch.cuda.is_available(), flush=True)
ns = run_cells(os.path.join(SP, "..", "notebooks", "role3_gnn_elliptic.ipynb"), [4, 7, 10, 12, 14, 20], {})
exec(r'''
out = Path(SP) / "r3out"
test_ids = df.loc[df["time_step"] >= TEST_START, "txId"].astype(str).values[test_g.labeled.cpu().numpy()]
for (kind, s), m in trained.items():
    p, _, _ = predict(m, test_g)
    pd.DataFrame({"txId": test_ids, "score_illicit": p}).to_csv(out / f"{kind}_seed{s}_predictions.csv", index=False)
res_df.to_csv(out / "role3_gnn_results.csv", index=False)
pd.DataFrame(per_step).to_csv(out / "role3_gnn_per_timestep.csv", index=False)
pd.DataFrame(rf_rows).to_csv(out / "role3_rf_embeddings_results.csv", index=False)
for s in SEEDS:   # same RF as Section 7, kept as score files
    rf = RandomForestClassifier(n_estimators=100, max_features=50, n_jobs=-1, random_state=s).fit(Xtr, ytr)
    pd.DataFrame({"txId": test_ids, "score_illicit": rf.predict_proba(Xte)[:, 1]}).to_csv(out / f"rf_raw_seed{s}_predictions.csv", index=False)
torch.save(trained[("gcn", 0)].state_dict(), out / "gcn_seed0.pt")
print(summary); print(pd.DataFrame(rf_rows).groupby("model")[["illicit_f1","pr_auc"]].agg(["mean","std"]).round(3)); print("DONE")
''', {**ns, "SP": SP, "Path": Path})

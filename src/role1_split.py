"""Rebuild the team's chronological split, tests/elliptic_split.csv, from raw Elliptic files.

Command line, from the repository root:
    python -m src.role1_split --data-dir <folder with elliptic_txs_*.csv> --out tests/elliptic_split.csv

Train = time steps 1-34, test = 35-49 (Weber et al., 2019). Class codes 1/2 become
"illicit"/"licit"; unlabelled transactions stay "unknown" and are kept, not dropped.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

TRAIN_END = 34
CLASS_NAMES = {"1": "illicit", "2": "licit", "unknown": "unknown"}


def build_split(features: pd.DataFrame, classes: pd.DataFrame) -> pd.DataFrame:
    """One row per transaction, in the raw features-file order."""
    split = features.iloc[:, :2].copy()
    split.columns = ["txId", "time_step"]
    labels = classes.set_index(classes["txId"].astype(str))["class"].astype(str).map(CLASS_NAMES)
    split["class"] = split["txId"].astype(str).map(labels)
    if split["class"].isna().any():
        raise ValueError("Some transactions have no class row or an unexpected class code.")
    split["split"] = split["time_step"].le(TRAIN_END).map({True: "train", False: "test"})
    return split


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    find = lambda name: next(args.data_dir.rglob(name))
    split = build_split(
        pd.read_csv(find("elliptic_txs_features.csv"), header=None, usecols=[0, 1]),
        pd.read_csv(find("elliptic_txs_classes.csv")),
    )
    split.to_csv(args.out, index=False)
    print(split.groupby(["split", "class"]).size().unstack(fill_value=0).to_string())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
RAW_FILE = REPO_ROOT / "data" / "raw" / "inspections_raw.csv.gz"
OUT_DIR = REPO_ROOT / "data" / "processed"
OUT_FILE = OUT_DIR / "inspections_model.csv"

INITIAL_CYCLE = "Cycle Inspection / Initial Inspection"
FAIL_THRESHOLD = 14   #0-13 points are passed (a grade)
CHAIN_MIN_LOCATIONS = 5
FIRST_MODEL_DATE = "2023-01-01"


def load_raw():
    df = pd.read_csv(RAW_FILE, dtype=str)
    df["inspection_date"] = pd.to_datetime(df["inspection_date"])
    df["score"] = pd.to_numeric(df["score"])

    df = df[df["inspection_date"].dt.year > 1900]
    df["boro"] = df["boro"].replace("0", np.nan) # lots of 0 treat as nans
    for col in ["latitude", "longitude"]:
        df[col] = pd.to_numeric(df[col]).replace(0, np.nan) # long, lat = 0 are invalid (location not tracked); treat as missing
    return df


def restaurant_info(df):
    info = (df.sort_values("inspection_date")
              .groupby("camis")
              .last()[["dba", "boro", "zipcode", "cuisine_description", "latitude", "longitude"]])

    locations_per_name = df.groupby("dba")["camis"].nunique()
    info["is_chain"] = (info["dba"].map(locations_per_name) >= CHAIN_MIN_LOCATIONS).astype(int)
    return info


def inspection_table(df):
    df = df.assign(
        is_violation=df["violation_code"].notna(),
        is_critical=df["critical_flag"].eq("Critical"),
        is_closure=df["action"].str.contains("Closed by DOHMH|re-closed", na=False),
    )
    insp = (df.groupby(["camis", "inspection_date", "inspection_type"], dropna=False)
              .agg(score=("score", "first"),
                   n_violations=("is_violation", "sum"),
                   n_critical=("is_critical", "sum"),
                   closed=("is_closure", "any"))
              .reset_index())
    return insp


def history_features(insp):
    daily = (insp.groupby(["camis", "inspection_date"])
                 .agg(n_insp=("score", "size"),
                      n_critical=("n_critical", "sum"),
                      closed=("closed", "any"))
                 .reset_index()
                 .sort_values(["camis", "inspection_date"]))
    g = daily.groupby("camis")
    daily["n_prior_inspections"] = g["n_insp"].cumsum() - daily["n_insp"]
    daily["n_prior_critical_violations"] = g["n_critical"].cumsum() - daily["n_critical"]
    daily["n_prior_closures"] = g["closed"].cumsum() - daily["closed"]
    daily["days_since_prev_inspection"] = (daily["inspection_date"] - g["inspection_date"].shift()).dt.days

    initial = (insp[insp["inspection_type"] == INITIAL_CYCLE]
               .sort_values(["camis", "inspection_date"])
               .copy())
    g = initial.groupby("camis")
    initial["n_prior_initial_inspections"] = g.cumcount()
    initial["prev_initial_score"] = g["score"].shift()
    initial["mean_prior_initial_score"] = g["score"].transform(lambda s: s.shift().expanding().mean())
    initial["max_prior_initial_score"] = g["score"].transform(lambda s: s.shift().cummax())
    initial["days_since_prev_initial"] = (initial["inspection_date"] - g["inspection_date"].shift()).dt.days

    history_cols = ["n_prior_inspections", "n_prior_critical_violations",
                    "n_prior_closures", "days_since_prev_inspection"]
    initial = initial.merge(daily[["camis", "inspection_date"] + history_cols],
                            on=["camis", "inspection_date"], how="left")
    return initial


def main():
    raw = load_raw()
    info = restaurant_info(raw)
    insp = inspection_table(raw)
    model = history_features(insp)

    model = model.merge(info, left_on="camis", right_index=True, how="left")
    model["inspection_year"] = model["inspection_date"].dt.year
    model["inspection_month"] = model["inspection_date"].dt.month
    model["inspection_dayofweek"] = model["inspection_date"].dt.dayofweek
    model["prev_initial_failed"] = (model["prev_initial_score"] >= FAIL_THRESHOLD).astype("Int64")
    model.loc[model["prev_initial_score"].isna(), "prev_initial_failed"] = pd.NA
    model["n_prior_closures"] = model["n_prior_closures"].astype(int)
    model["fail"] = (model["score"] >= FAIL_THRESHOLD).astype(int)

    columns = [
        # atributes (identifiers) not features 
        "camis", "dba", "inspection_date",
        # restaurant facts
        "boro", "zipcode", "cuisine_description", "latitude", "longitude", "is_chain",
        # timing
        "inspection_year", "inspection_month", "inspection_dayofweek",
        # history
        "n_prior_inspections", "n_prior_initial_inspections", "prev_initial_score",
        "prev_initial_failed", "mean_prior_initial_score", "max_prior_initial_score",
        "n_prior_critical_violations", "n_prior_closures",
        "days_since_prev_inspection", "days_since_prev_initial",
        # targets (y)
        "score", "fail",
    ]
    model = model[model["inspection_date"] >= FIRST_MODEL_DATE]
    model = model[columns].sort_values(["inspection_date", "camis"]).reset_index(drop=True)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    model.to_csv(OUT_FILE, index=False)

    print(f"raw violation rows:      {len(raw):,}")
    print(f"inspections (all types): {len(insp):,}")
    print(f"modeling rows:           {len(model):,} x {model.shape[1]} columns")
    print(f"restaurants:             {model['camis'].nunique():,}")
    print(f"fail rate:               {model['fail'].mean():.3f}")
    print(f"saved to {OUT_FILE}")


if __name__ == "__main__":
    main()

# Data shape

## Source
1. **Dataset:** DOHMH New York City Restaurant Inspection Results (NYC Department of Health and Mental Hygiene)
2. **Dataset id:** `43nn-pn8j`
3. **API:** https://data.cityofnewyork.us/resource/43nn-pn8j.json


Note: The API keeps a rolling window of ~ 3 years plus a few hundred older records. It only lists restaurants that are currently active. Restaurants that closed for good are dropped from the dataset, so it is biased toward restaurants that survived.

### Scores meaning: 
inspector adds penalty points for every violation found.
**Score of 0–13:** the restaurant gets an A on the spot.
**Score of 14 or more:** no grade is given at the first (initial) inspection. The restaurant is re-inspected, and the re-inspection decides its B or C.

## Files
| File | Rows | Description |
|---|---|---|
| `raw/inspections_raw.csv.gz` | 295,422 | raw api pull |
| `raw/inspections_raw_metadata.json` | – | source url, pull time and row count, used for version control|
| `processed/inspections_model.csv` | 44,890 | output of `src/build_dataset.py`. one row per inspection from 2023 onward. |


## Raw data: `raw/inspections_raw.csv.gz`
one row per violation.

| column | type | description |
|---|---|---|
| camis | id | unique restaurant id |
| dba | text | restaurant name |
| boro | categorical | Manhattan, Brooklyn, Queens, Bronx, Staten Island (`0` = missing) |
| building, street, zipcode | text | address |
| phone | text | phone number |
| cuisine_description | categorical | cuisine type, 90 categories (e.g. American, Chinese, Pizza) |
| inspection_date | date | date of inspection (`1900-01-01` = not inspected yet) |
| action | categorical | violations cited / no violations / closed / re-opened / re-closed |
| violation_code | categorical | violation code (e.g. `04L` = mice) |
| violation_description | text | violation description |
| critical_flag | categorical | Critical (can cause illness) / Not Critical / Not Applicable (no violation) |
| score | continuous (points) | total penalty points for the inspection, higher = worse |
| grade | ordinal | A (0–13) > B (14–27) > C (28+); N = not yet graded, Z / P = grade pending, empty = no grade issued |
| grade_date | date | date grade was issued |
| record_date | date | date record was last updated |
| inspection_type | categorical | `program / step`. programs: cycle (routine), pre-permit, administrative, task force, single-rule checks. steps: initial, re-inspection, compliance, reopening |
| latitude, longitude | continuous (degrees) | location (`0` = missing) |
| community_board, council_district, census_tract, bin, bbl, nta | categorical | nyc geography codes |

## Processed data: `processed/inspections_model.csv`
one row per initial cycle inspection.

note: features only use info from before the inspection date. history columns are empty when there's no earlier inspection in the data window. restaurants appear more than once, so rows aren't independent.

| column | type | description |
|---|---|---|
| camis | id | restaurant id |
| dba | text | restaurant name |
| inspection_date | date | date of inspection |
| boro | categorical | borough (same as raw) |
| zipcode | categorical | zip code |
| cuisine_description | categorical | cuisine type, 90 categories |
| latitude, longitude | continuous (degrees) | location |
| is_chain | binary | 1 = name appears at 5+ locations |
| inspection_year | ordinal | 2023–2026 |
| inspection_month | ordinal | 1 = Jan … 12 = Dec |
| inspection_dayofweek | ordinal | 0 = Mon … 6 = Sun |
| n_prior_inspections | continuous (count) | earlier inspections of any type |
| n_prior_initial_inspections | continuous (count) | earlier initial cycle inspections |
| prev_initial_score | continuous (points) | score at previous initial inspection |
| prev_initial_failed | binary | 1 = previous initial score ≥ 14 |
| mean_prior_initial_score | continuous (points) | mean of earlier initial scores |
| max_prior_initial_score | continuous (points) | worst earlier initial score |
| n_prior_critical_violations | continuous (count) | critical violations across earlier inspections |
| n_prior_closures | continuous (count) | earlier closures by DOHMH |
| days_since_prev_inspection | continuous (days) | days since previous inspection of any type |
| days_since_prev_initial | continuous (days) | days since previous initial inspection |
| score | target, continuous (points) | penalty points at this inspection (alt target) |
| fail | **target**, binary | 1 = score ≥ 14, no A (40% of rows). main target |

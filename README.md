# DATA1030 Project

> Can we predict which restaurant will fail its health inspection before the inspector walks in?

## Team
- Ahmed Hanzala
- Luke Sidwell
- Yuan Ying

## Repository structure
```
├── data/      raw and preprocessed data
├── figures/   generated figures
├── results/   predictions, saved models, metrics
├── report/    PDF of the midterm report
├── src/       notebooks and Python source
├── environment.yml
├── LICENSE
└── README.md
```

## Setup
Python version: 3.12
```bash
conda env create -f environment.yml
conda activate data1030
```

Package versions: in `environment.yml`

## Data
NYC restaurant inspections, pulled from the NYC Open Data API. code is in `src/build_dataset.py` and `collect.py`. More information about data and each of its feature is located in `data/README.md`

## License
MIT. See [LICENSE](LICENSE).

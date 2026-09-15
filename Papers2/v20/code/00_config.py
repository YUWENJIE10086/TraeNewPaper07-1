from pathlib import Path

# v20 uses repository-relative paths only. No D:/ or /home/... paths are allowed.
HERE = Path(__file__).resolve().parent
V20_ROOT = HERE.parent
REPO_ROOT = V20_ROOT.parent.parent

SOURCE_ROOT = (
    REPO_ROOT
    / "Papers2"
    / "v18"
    / "v18-3"
    / "v18-3-3"
    / "v18-3-3-2"
    / "xg-3"
)
SOURCE_DATA = SOURCE_ROOT / "data"

RESULTS = V20_ROOT / "results"
TABLES = V20_ROOT / "tables"
FIGURES = V20_ROOT / "figures"
INTERMEDIATE = V20_ROOT / "intermediate"

for directory in (RESULTS, TABLES, FIGURES, INTERMEDIATE):
    directory.mkdir(parents=True, exist_ok=True)

ANALYSIS_PANEL = SOURCE_DATA / "analysis_panel.csv"
SOURCE_METRICS = SOURCE_DATA / "metrics.json"
SOURCE_DATA_QUALITY = SOURCE_DATA / "data_quality.json"
SOURCE_OUTCOME_WEIGHTS = SOURCE_DATA / "clean_outcome_weights.csv"
SOURCE_PSM_BALANCE = SOURCE_DATA / "psm_balance.csv"

RANDOM_SEED = 20260915
PERMUTATION_REPS = 1000
PSM_CALIPER = 0.02


def assert_source_files() -> None:
    required = [
        ANALYSIS_PANEL,
        SOURCE_METRICS,
        SOURCE_DATA_QUALITY,
        SOURCE_OUTCOME_WEIGHTS,
        SOURCE_PSM_BALANCE,
    ]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError("Missing registered upstream files:\n" + "\n".join(missing))

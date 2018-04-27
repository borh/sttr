# sttr

Calculate STTR on tokenized text with metadata using Python

# Requirements

Tested using Python 3.6.

-   Pandas

```bash
pip install pandas
```

Or using Pipenv:

```bash
pipenv install
pipenv shell
```

# Usage

Run the `run_sttr.py` script, specifying the `datadir` and `output` parameters.

## Single-corpus mode

```bash
python run_sttr.py /path/to/corpus/dir
```

Results filename uses the specified corpus directory name as the prefix.

## Multiple-corpus mode

```bash
python run_sttr.py /path/to/corpus/dirs/* /path/to/other/corpus
```

Final results will be merged into `merged_results.tsv` in the current directory.

## Full example

```bash
python run_sttr.py --meta 'author,genre,brow,narrative_perspective' ~/Dropbox/Complexity/Corpora/*
```

This will calculate STTR for every corpus directory under `~/Dropbox/Complexity/Corpora`. The `author,genre,brow,narrative_perspective` will be extracted from the `groups.csv` file as well and merged into the `merged_results.tsv` file at the end. Missing metadata is output as NA.

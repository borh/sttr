# sttr

Calculate STTR on tokenized text with metadata using Python

# Requirements

Tested using Python 3.7.

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

You may also use the pre-defined `sttr` run command when using pipenv (i.e. replace all `python run_sttr.py` incantations with `pipenv run sttr`).

## Example

```bash
python run_sttr.py /path/to/corpus/dir
```

The above command will look under `/path/to/corpus/dir` for all directories that have a `groups.csv` or `metadata.csv` file and try to extract the specified filenames from the `Tokenized`, `Lemmatized`, `POS`, `POS_Tri`, `UniversalPOS`, and `UniversalPOS_Tri` directories (if present).
For each corpus and folder (Tokenized/Lemmatized/...) combination, a `results_CORPUSNAME_TYPE.tsv` will be generated containing calculated measures.

Finally, a `merged_results_CORPUSNAME1+CORPUSNAME2+...tsv` file wile be generated containing the merged results from all corpora.

An example run on the whole project, with extended metadata:

```bash
python run_sttr.py --meta 'author,genre,brow,narrative_perspective,year' ~/Dropbox/Complexity/Corpora/*
```

This will calculate Yule's K, STTR, and associated length measures, for every corpus directory under `~/Dropbox/Complexity/Corpora`. The `author,genre,brow,narrative_perspective` metadata will be extracted from the `groups.csv` file as well and merged into the `merged_results_....tsv` file at the end. Missing metadata is output as NA.

## Advanced usage

See the usage:

    usage: run_sttr.py [-h] [--check-only] [--meta META_FIELDS] [-t TYPES] [-p]
                       [-f FIELD]
                       datadirs [datadirs ...]

    calculates sttr

    positional arguments:
      datadirs            directory with data in csv files

    optional arguments:
      -h, --help          show this help message and exit
      --check-only        do a pass through all specified corpus directories to
                          make sure they conform to project standards
      --meta META_FIELDS  specify metadata fields in CSV to use as categorical
                          features, optional, (default='Brow'); Format: specify as
                          CSV string
      -t TYPES            specify folders to use (Tokenized or POS etc.),
                          optional, (default='Tokenized,Lemmatized,POS,POS_Tri,Uni
                          versalPOS,UniversalPOS_Tri')
      -p                  remove punctuation, optional, (default='False')
      -f FIELD            use delimited field number to extract chosen unit
                          (token/POS/lemma/...), optional, (default='0' (the first
                          field))

Note that you may specify multiple corpora on the command line like below:

```bash
python run_sttr.py /path/to/corpus/dirs/* /path/to/other/corpus
```

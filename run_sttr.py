#!/usr/bin/env python
import math
import statistics
import os
import pandas as pd
import re
import argparse
import glob


def ttr(words):
    '''
    calcute type-token ratio
    :param words: list of words
    :return: float with type-token ratio
    '''
    return len(set(words)) / len(words)


def sttr_ci(results):
    '''
    calculate confidence interval for standardized type-token ratio (see Evert et al. 2017)
    :param results: standardized type token ratio for a list of words
    :return:  float with confidence interval
    '''
    return 1.96 * statistics.stdev(results) / math.sqrt(len(results))


def sttr(wordlist, winsize, ci=True):
    '''
    calculate standardized type-token ratio
    originally Kubat&Milicka 2013. Much better explained
    in Evert et al. 2017.
    ci: additionally calculate and return the confidence interval
    '''
    results = []
    for i in range(int(len(wordlist)/winsize)):
        results.append(ttr(wordlist[i*winsize:(i*winsize)+winsize]))
    if not ci:
        return statistics.mean(results)
    else:
        r = statistics.mean(results)
        ci = sttr_ci(results)
        sd = statistics.stdev(results)
        return r, ci, sd


def remove_punct(text):
    '''
    removes punctuation and non-textual metadata from text
    :param text: input str
    :return: str
    '''
    if re.match(r'<(EOS|PGB)>', text):
        return ''
    else:
        return re.sub(r'[^\w]', '', text)


def read_txt(file, remove_punctuation):
    text = []
    with open(file, encoding='utf-8') as f:
        for line in f:
            token = line.rstrip()
            if token == '<EOS>' or token == '<PGB>':
                continue

            if remove_punctuation:
                normalized_token = remove_punct(token)
                if normalized_token != '':
                    text.append(normalized_token)
            else:
                text.append(token)
    return text, len(text)


def write_results(out_file, df_sttr, df_groups):
    '''
    write results to csv file
    :param out_file: filename
    :param df_sttr: pandas df with all results
    :param df_groups: metadata about text type
    '''
    if not out_file.endswith('tsv'):
        out_file = out_file + '.tsv'

    df_groups.reset_index(inplace=True, drop=True)
    df_sttr.reset_index(inplace=True, drop=True)
    df_result = df_sttr.merge(df_groups, on=['filename', 'window'], how='inner',
                              left_index=True, right_index=True, sort=True)
    df_result.set_index('filename', inplace=True)
    df_result.to_csv(out_file, sep='\t', encoding='utf-8', index=True)


def calc_sttrs(filenames, winsize, remove_punctuation):
    '''
    calculate sttr for all files in filenames
    :param filenames: list of filenames
    :param winsize: int winsize for sttr calculation
    :return: pandas df with results
    '''
    sttr_results = []
    textlengths = []
    for file in filenames:
        text, text_len = read_txt(file, remove_punctuation)
        sttr_results.append((os.path.split(file)[1],) + sttr(text, winsize=winsize))
        textlengths.append(text_len)
    df_sttr = pd.DataFrame(sttr_results)
    df_sttr.columns = ['filename', 'sttr', 'ci', 'sd']
    df_sttr.insert(loc=1, column='window', value=[winsize]*len(filenames))
    df_sttr.insert(loc=2, column='text_length', value=textlengths)
    return df_sttr


def start_msg(args):
    print('Processing files in {}'.format(args.datadirs))
    print('using {} files'.format('tokenized' if args.tokenized else 'plain'))


def corpus_sttr(basedir, corpus_path, meta_fields, remove_punctuation):
    filenames = sorted(glob.glob(os.path.join(basedir, corpus_path, '*.txt')))
    columns = ['filename'] + meta_fields

    # read metadata about text type
    df_groups = pd.read_table(os.path.join(basedir, 'groups.csv'),
                              sep=None, engine='python')
    df_groups.rename(columns={'idno': 'filename', 'textid': 'filename'},
                     inplace=True)
    df_groups.rename(columns=lambda s: s.lower().replace('-', '_'),
                     inplace=True)
    selected_columns = set(df_groups.columns.tolist()) & set(columns)
    df_groups = df_groups[list(selected_columns)]

    # Sanity checks:
    filenames_set = {os.path.basename(filename) for filename in filenames}
    groups_filenames_set = set(df_groups['filename'])
    if len(df_groups['filename']) != len(groups_filenames_set):
        from collections import Counter
        c = Counter(df_groups['filename'])
        raise ValueError('Error: Duplicate filename(s) detected in groups.csv: "{}". Aborting.'.format({filename for filename, freq in c.items() if freq >= 2}))
    if filenames_set != groups_filenames_set or len(df_groups) != len(filenames_set):
        raise ValueError("Warning: groups.csv and filesystem contain differing information: {}\nOnly in groups.csv: {}\nOnly on filesystem: {}".format(
            filenames_set ^ groups_filenames_set,
            groups_filenames_set.difference(filenames_set),
            filenames_set.difference(groups_filenames_set)
        ))

    # calculate sttr for window size 10
    df_results = calc_sttrs(filenames, 10, remove_punctuation)
    ngroups = df_groups.copy()
    ngroups.insert(loc=1, column='window', value=10)

    # repeat for 100...1000 winsize
    for i in range(100, 1001, 100):  # i: window size
        r = calc_sttrs(filenames, i, remove_punctuation)
        df_results = df_results.append(r)
        g = df_groups.copy()  # insert window size for merging
        g.insert(loc=1, column='window', value=i)
        ngroups = ngroups.append(g)
    return df_results, ngroups


def corpora_merge(corpora_paths, corpus_type, output, meta_fields, remove_punctuation):
    results, ngroups = pd.DataFrame(), pd.DataFrame(columns=['filename'] + meta_fields)
    for path in corpora_paths:
        r, g = corpus_sttr(path, corpus_type, meta_fields, remove_punctuation)
        corpus_name = os.path.basename(path)
        out_fn = 'sttr_' + corpus_name
        write_results(out_fn, r.copy(), g.copy())
        print('Results for corpus \'{}\' written to \'{}.tsv\'.'.format(corpus_name, out_fn))
        g.insert(loc=1, column='corpus_name', value=corpus_name)
        results = results.append(r)
        ngroups = ngroups.append(g)

    results.reset_index(inplace=True, drop=True)
    ngroups.reset_index(inplace=True, drop=True)

    write_results('merged_results', results, ngroups)


def main(args):
    start_msg(args)

    corpora_paths = args.datadirs
    corpus_type = 'Tokenized' if args.tokenized else 'Plain'
    meta_fields = args.meta_fields.split(',')
    corpora_merge(corpora_paths, corpus_type, args.output, meta_fields, args.remove_punctuation)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='calculates sttr')
    parser.add_argument('output', type=str, help='name of file to write results to')
    parser.add_argument('datadirs', type=str, help='directory with data in csv files', nargs='+')
    parser.add_argument('--meta', default='brow', dest='meta_fields',
                        help='specify metadata fields in CSV to use as categorical features, optional, (default=\'brow\'); Format: specify as CSV string')
    parser.add_argument('-t', default=True, action='store_true', dest='tokenized',
                        help='use tokenized (instead of plain files), optional, (default=\'tokenized\')')
    parser.add_argument('-p', default=False, action='store_true', dest='remove_punctuation',
                        help='remove punctuation, optional, (default=\'False\')')
    main(parser.parse_args())

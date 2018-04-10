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
                pass

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
    df_result = df_groups.merge(df_sttr, on=['filename'], how='inner',
                                left_index=True, right_index=True, sort=True)
    df_result.to_csv(out_file, sep='\t', encoding='utf-8', index=False)


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
    df_sttr.insert(loc=0, column='window', value=[winsize]*len(filenames))
    df_sttr.insert(loc=0, column='text_length', value=textlengths)
    return df_sttr


def start_msg(args):
    print('Processing files in {}'.format(args.datadir))
    if args.tokenized:
        t = 'tokenized'
    else:
        t = 'plain'
    print('using {} files'.format(t))


def get_dirs(args):
    # choose tokenized text or plain text
    if args.tokenized:
        corpus_path = 'Tokenized'
    else:
        corpus_path = 'Plain'
    return args.datadir, corpus_path


def main(args):
    start_msg(args)
    basedir, corpus_path = get_dirs(args)
    filenames = sorted(glob.glob(os.path.join(basedir, corpus_path, '*.txt')))
    columns = ['filename'] + args.meta_fields.split(',')

    # read metadata about text type
    file_columns = set(pd.read_table(os.path.join(args.datadir, 'groups.csv'),
                                     sep=None, engine='python',
                                     nrows=0).columns.tolist())
    common_columns = file_columns.intersection(set(columns))
    if 'filename' not in common_columns:
        if 'idno' in file_columns:
            common_columns.add('idno')
        elif 'textid' in file_columns:
            common_columns.add('textid')

    dtypes = {colname: 'category' for colname in common_columns}

    df_groups = pd.read_table(os.path.join(args.datadir, 'groups.csv'),
                              sep=None, engine='python',
                              usecols=common_columns, dtype=dtypes)
    df_groups.rename(columns={'idno': 'filename', 'textid': 'filename'}, inplace=True)
    df_groups.rename(columns=lambda s: s.lower().replace('-', '_'),
                     inplace=True)

    # calculate sttr for 10, 100...1000 winsize
    df_results = calc_sttrs(filenames, 10, args.remove_punctuation)
    ngroups = df_groups
    for i in range(100, 1001, 100):  # i: window size
        df_results = df_results.append(calc_sttrs(filenames, i, args.remove_punctuation))
        ngroups = ngroups.append(df_groups)

    write_results(args.output, df_results, ngroups)
    print('Done. Results written to {}'.format(args.output))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='calculates sttr')
    parser.add_argument('datadir', type=str, help='directory with data in csv files')
    parser.add_argument('output', type=str, help='name of file to write results to')
    parser.add_argument('--meta', default='brow', dest='meta_fields',
                        help='specify metadata fields in CSV to use as categorical features, optional, (default=\'brow\'); Format: specify as CSV string')
    parser.add_argument('-t', default=True, action='store_true', dest='tokenized',
                        help='use tokenized (instead of plain files), optional, (default=\'tokenized\')')
    parser.add_argument('-p', default=False, action='store_true', dest='remove_punctuation',
                        help='remove punctuation, optional, (default=\'False\')')
    main(parser.parse_args())

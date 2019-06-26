#!/usr/bin/env python
import pandas as pd
import math
from statistics import mean, stdev, StatisticsError
from unicodedata import normalize
import os
import glob
from pathlib import Path
import re
import argparse
import pprint
from collections import Counter
from itertools import chain
import platform


PLATFORM_MACOS = True if platform.system() == 'Darwin' else False


def compact_format_files(files):
    if not files:
        return None
    basedir = Path(list(files)[0]).parent
    return (basedir, [Path(file).name for file in files])


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
    return 1.96 * stdev(results) / math.sqrt(len(results))


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
        return mean(results)
    elif len(results) > 1:
        r = mean(results)
        ci = sttr_ci(results)
        sd = stdev(results)
        return r, ci, sd
    else:
        return results[0], 0, 0


def yule_k_(text_length, frequency_spectrum):
    '''Yule (1944)'''
    return 10000 * (sum((freq_size * (freq / text_length) ** 2 for freq, freq_size in frequency_spectrum.items())) - (1 / text_length))


def yule_k(wordlist):
    counter = Counter(wordlist)
    freq_spect = Counter(counter.values())
    return yule_k_(len(wordlist), freq_spect)


def remove_punct(text):
    '''
    removes punctuation and non-textual metadata from text
    :param text: input str
    :return: str
    '''
    return re.sub(r'[^\w]', '', text)


def sentence_iter(xs, remove_punctuation, field):
    sentence = []
    for line in xs:
        token = line.rstrip()
        if token == '<EOS>' or token == '<PGB>':
            # Discard empty sentences (i.e. <EOS> followed by <PGB>)
            if sentence:
                yield sentence
            sentence = []
            continue

        # Set correct field to extract (surface, POS, or lemma).
        token = token.split('\t')[field]

        if remove_punctuation:
            normalized_token = remove_punct(token)
            if normalized_token != '':
                sentence.append(normalized_token)
        else:
            sentence.append(token)
    if sentence:
        yield sentence


def read_txt(file, remove_punctuation, field=0, is_tokens=True):
    text = []
    sentence_lengths = []
    with open(file, encoding='utf-8') as f:
        for sentence in sentence_iter(f, remove_punctuation, field):
            sentence_lengths.append(len(sentence))
            text.extend(sentence)

    if not is_tokens:
        sentence_mean = None
        sentence_sd = None
    else:
        try:
            sentence_mean = mean(sentence_lengths)
            sentence_sd = stdev(sentence_lengths)
        except StatisticsError:
            print('Warning: Cannot calculate mean and stdev of sentence length since EOS annotations are not present in \'{}\''.format(file))
            sentence_mean = None
            sentence_sd = None

    return text, len(text), sentence_mean, sentence_sd


def write_results(out_file, path, df_sttr, df_groups):
    '''
    write results to csv file
    :param out_file: filename
    :param df_sttr: pandas df with all results
    :param df_groups: metadata about text type
    '''
    Path(path).mkdir(parents=True, exist_ok=True)

    if not out_file.endswith('tsv'):
        out_file = out_file + '.tsv'

    out_path = Path(path).joinpath(out_file)

    df_groups.reset_index(inplace=True, drop=True)
    df_sttr.reset_index(inplace=True, drop=True)
    df_result = df_sttr.merge(df_groups, on=['Corpus_name', 'Filename', 'Window', 'Type'],
                              how='inner', left_index=True, right_index=True,
                              sort=False)
    df_result.set_index('Filename', inplace=True)
    df_result.to_csv(out_path, sep='\t', encoding='utf-8', index=True)


def calculate_measures(filenames, winsize, remove_punctuation, field, is_tokens=True):
    '''
    calculate sttr for all files in filenames
    :param filenames: list of filenames
    :param winsize: int winsize for sttr calculation
    :return: pandas df with results
    '''
    sttr_results = []
    text_lengths = []
    sentence_means = []
    sentence_sds = []
    yules_ks = []
    for file in filenames:
        text, text_len, sentence_length_mean, sentence_length_sd = read_txt(
            file, remove_punctuation, field, is_tokens
        )
        yules_ks.append(yule_k(text))
        if text_len < winsize:
            print('Skipping sttr calculation for \'{}\' as text length ({}) is less than window size ({})'.format(
                file,
                text_len,
                winsize
            ))
            sttr_results.append((os.path.split(file)[1],) + (0.0, 0.0, 0.0))
        else:
            sttr_results.append((os.path.split(file)[1],) + sttr(text, winsize=winsize))
        text_lengths.append(text_len)
        sentence_means.append(sentence_length_mean)
        sentence_sds.append(sentence_length_sd)
    df_sttr = pd.DataFrame(sttr_results)
    df_sttr.columns = ['Filename', 'STTR', 'STTR_CI', 'STTR_SD']
    df_sttr.insert(loc=1, column='Yules_K', value=yules_ks)

    if is_tokens:
        # These would make no sense for trigrams:
        df_sttr.insert(loc=3, column='Text_length', value=text_lengths)
        df_sttr.insert(loc=4, column='Sent_len_mean', value=sentence_means)
        df_sttr.insert(loc=5, column='Sent_len_sd', value=sentence_sds)
        df_sttr.insert(loc=6, column='Window', value=[winsize]*len(filenames))
    else:
        df_sttr.insert(loc=2, column='Window', value=[winsize]*len(filenames))
    return df_sttr


def start_msg(args):
    print('Processing folder types\n{}\nfor corpora under\n{}\nusing windows sizes: {}.'.format(
        pprint.pformat(args.types),
        pprint.pformat(args.datadirs),
        list(range(args.min_window, args.max_window+1, 100))
    ))


def find_metadata(dir):
    metadata_file = os.path.join(dir, 'groups.csv')
    if not os.path.exists(metadata_file):
        metadata_file = os.path.join(dir, 'metadata.csv')
        if not os.path.exists(metadata_file):
            # print('No "groups.csv" or "metadata.csv" file found at path "{}"'.format(dir))
            return None
    return metadata_file


def find_corpora(basedir):
    for root, dirs, files in os.walk(basedir, followlinks=True):
        for dir in [root] + dirs:
            maybe_dir = os.path.join(root, dir)
            metadata_file = find_metadata(maybe_dir)
            if metadata_file:
                yield maybe_dir, metadata_file


def get_data(corpus_path, meta_fields, metadata_file):
    filenames = sorted([normalize('NFC', fname) if PLATFORM_MACOS else fname
                        for fname in glob.glob(os.path.join(corpus_path, '*.txt'))])
    columns = ['Filename'] + meta_fields

    df_groups = pd.read_csv(metadata_file, sep=None, engine='python')
    df_groups.rename(
        columns={
            'idno': 'Filename',
            'textid': 'Filename',
            'pubyear-orig': 'Year',
            'supergenre': 'Genre',
            'group': 'Brow',
        }, inplace=True)
    df_groups.columns = df_groups.columns.str.capitalize().str.replace('-', '_')
    selected_columns = set(df_groups.columns.tolist()) & set(columns)
    df_groups = df_groups[list(selected_columns)]

    if 'genre' in selected_columns:
        def normalize_columns(s):
            if not isinstance(s, str):
                return None
            s = s.lower()
            if s == 'novel':
                return 'fiction'
            else:
                return s
        df_groups['Genre'] = df_groups['Genre'].map(normalize_columns)

    df_groups['Filename'] = df_groups['Filename'].map(lambda x: normalize('NFC', x) if PLATFORM_MACOS else x).map(lambda x: x if x.endswith('.txt') else x + '.txt')

    # Sanity checks:
    filenames_set = set(filenames)
    groups_filenames = [os.path.join(corpus_path, filename)
                        for filename in df_groups['Filename']]
    groups_filenames_set = set(groups_filenames)

    if not filenames_set:
        print('No files for folder type {}, skipping...'.format(Path(corpus_path).name))
        return None

    if len(df_groups['Filename']) != len(groups_filenames_set):
        from collections import Counter
        c = Counter(df_groups['Filename'])
        raise ValueError('Error: Duplicate filename(s) detected in groups.csv: "{}". Aborting.'.format({filename for filename, freq in c.items() if freq >= 2}))

    if filenames_set != groups_filenames_set or len(df_groups) != len(filenames_set):
        print('Warning: "{}" and filesystem contain differing information, skipping...'.format(metadata_file))
        print('Only in "{}":'.format(metadata_file))
        pprint.pprint(compact_format_files(groups_filenames_set.difference(filenames_set)))
        print('Only on filesystem:')
        pprint.pprint(compact_format_files(filenames_set.difference(groups_filenames_set)))
        return None

    print('Processing folder type {}.'.format(Path(corpus_path).name))
    return groups_filenames, df_groups


def corpus_measures(groups_filenames, df_groups, remove_punctuation, field,
                    min_window, max_window, check_only, is_tokens):
    if check_only:
        return None

    # calculate sttr for window size 500
    df_results = calculate_measures(groups_filenames, min_window, remove_punctuation, field, is_tokens)
    ngroups = df_groups.copy()
    ngroups.insert(loc=1, column='Window', value=500)

    # repeat for 600...1000 winsize
    for i in range(min_window+100, max_window+1, 100):  # i: window size
        r = calculate_measures(groups_filenames, i, remove_punctuation, field, is_tokens)
        df_results = df_results.append(r)
        g = df_groups.copy()  # insert window size for merging
        g.insert(loc=1, column='Window', value=i)
        ngroups = ngroups.append(g, sort=True)
    return df_results, ngroups


def corpora_merge(corpora_paths, corpus_types, out, meta_fields, remove_punctuation, field,
                  min_window, max_window, check_only):
    results, ngroups = pd.DataFrame(), pd.DataFrame(columns=['Filename', 'Corpus_name', 'Type'] + meta_fields)

    corpora = set(chain.from_iterable(map(find_corpora, corpora_paths)))
    for path, metadata_file in corpora:
        print('{}\nUsing metadata file {}'.format('='*80, metadata_file))

        for corpus_type in corpus_types:
            tokens_path = os.path.join(path, corpus_type)

            data = get_data(tokens_path, meta_fields, metadata_file)

            if data:
                groups_filenames, df_groups = data
            else:
                continue

            punc = False if re.search(r'japanese', path, re.I) else remove_punctuation
            is_tokens = False if corpus_type.endswith('Tri') else True

            measures_data = corpus_measures(groups_filenames, df_groups, punc, field,
                                            min_window, max_window, check_only,
                                            is_tokens=is_tokens)
            if check_only:
                continue
            else:
                r, g = measures_data

            corpus_name = os.path.basename(path)
            g.insert(loc=1, column='Corpus_name', value=corpus_name)
            g.insert(loc=2, column='Type', value=corpus_type)
            r.insert(loc=1, column='Corpus_name', value=corpus_name)
            r.insert(loc=2, column='Type', value=corpus_type)
            out_fn = 'results_' + corpus_name + '_' + corpus_type
            if not check_only:
                write_results(out_fn, out, r.copy(), g.copy())
            print('Corpus \'{}\', folder type \'{}\' (remove_punc={}, cols={}) => \'{}/{}.tsv\'.'.format(
                corpus_name,
                corpus_type,
                punc,
                ','.join(g.columns.tolist()),
                out,
                out_fn
            ))

            # TODO
            # if not is_tokens:
            #     results.insert(loc=3, column='Text_length', value=)
            #     results.insert(loc=4, column='Sent_len_mean', value=)
            #     results.insert(loc=5, column='Sent_len_sd', value=)
            results = results.append(r, sort=True)
            ngroups = ngroups.append(g, sort=True)

    results.reset_index(inplace=True, drop=True)
    ngroups.reset_index(inplace=True, drop=True)

    if not check_only:
        write_results('merged_results_' + '+'.join(ngroups['Corpus_name'].unique()), out, results, ngroups)


def main(args):
    args.types = args.types.split(',')
    start_msg(args)

    corpora_paths = args.datadirs
    corpus_types = args.types
    meta_fields = list(map(lambda s: s.capitalize(), args.meta_fields.split(',')))
    corpora_merge(corpora_paths, corpus_types, args.out, meta_fields,
                  args.remove_punctuation, args.field,
                  args.min_window, args.max_window, args.check_only)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='calculates sttr')
    parser.add_argument('datadirs', type=str, help='directory with data in csv files', nargs='+')
    parser.add_argument('-o', '--out', default='./', dest='out',
                        help='specify output directory for results files, optional, (default=\'./\'--teh current directory)')
    parser.add_argument('-c', '--check-only', default=False, action='store_true', dest='check_only',
                        help='do a pass through all specified corpus directories to make sure they conform to project standards')
    parser.add_argument('-m', '--meta', default='Brow', dest='meta_fields',
                        help='specify metadata fields in CSV to use as categorical features, optional, (default=\'Brow\'); Format: specify as CSV string')
    parser.add_argument('-t', '--types', default='Tokenized,Lemmatized,POS,POS_Tri,UniversalPOS,UniversalPOS_Tri,ds,narr',
                        dest='types',
                        help='specify folders to use (Tokenized or POS etc.), optional, (default=\'Tokenized,Lemmatized,POS,POS_Tri,UniversalPOS,UniversalPOS_Tri,ds,narr\')')
    parser.add_argument('-p', '--remove-punctuation', default=False, action='store_true', dest='remove_punctuation',
                        help='remove punctuation, optional, (default=\'False\')')
    parser.add_argument('-f', '--field', default=0, action='store', type=int, dest='field',
                        help='use delimited field number to extract chosen unit (token/POS/lemma/...), optional, (default=\'0\' (the first field))')
    parser.add_argument('--maxwin', default=1000, action='store', type=int, dest='max_window',
                        help='maximum window size, optional, (default=\'1000\')')
    parser.add_argument('--minwin', default=500, action='store', type=int, dest='min_window',
                        help='minimum window size, optional, (default=\'500\')')
    main(parser.parse_args())

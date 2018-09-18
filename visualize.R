## Packages
library(readr)
library(dplyr)
library(ggplot2)

library(Kendall)
library(reshape2)

## Data
corpora <- read_tsv('merged_results.tsv')

## TODO: add t-score?
## A simple yet robust approach could be to compute the difference between medians and then compute 95% confidence interval of such statistic with bootstrap (percentile). Such confidence interval would be adequate for inference. (https://stats.stackexchange.com/a/201710)
##corpora$brow.t.score <- group_by(corpus + brow)


## Plots
cairo_pdf('sttr-plots.pdf', onefile = TRUE, width = 16, heigh = 12)

ggplot(corpora %>% filter(window>=500), aes(corpus_name, sttr, color = brow)) +
    geom_boxplot() +
    facet_grid(window ~ corpus_name, scales = 'free') +
    ggtitle('STTR faceted by windows size and corpus')

ggplot(filter(corpora, window==500), aes(text_length, sttr, color = brow)) +
    geom_text(aes(label=filename)) +
    facet_wrap(~ corpus_name, scales = 'free') +
    ggtitle('STTR per filename for window=500 (brow)')

ggplot(corpora %>% filter(!is.na(genre)) %>% filter(window==500),
       aes(text_length, sttr, color = genre)) +
    geom_text(aes(label=filename)) +
    facet_wrap(~ corpus_name, scales = 'free') +
    ggtitle('STTR per filename for window=500 (genre)')

ggplot(corpora %>% filter(!is.na(narrative_perspective)) %>% filter(window==500),
       aes(text_length, sttr, color = narrative_perspective)) +
    geom_text(aes(label=filename)) +
    facet_wrap(~ corpus_name, scales = 'free') +
    ggtitle('STTR per filename for window=500 (narrative perspective)')

ggplot(corpora %>% filter(!is.na(year)) %>% filter(window==500),
       aes(year, sttr, color = author)) +
    geom_text(aes(label=filename)) +
    facet_wrap(~ corpus_name, scales = 'free') +
    ggtitle('STTR per filename by year for window=500 (color by author)')

ggplot(corpora, aes(filename, sttr, color = brow)) +
    geom_pointrange(aes(ymax = sttr + ci, ymin = sttr - ci),
                    size = .1, fatten = .1, shape = 16) +
    facet_grid(window ~ corpus_name, scales = 'free') +
    theme(axis.text.x = element_text(angle = 90, hjust = 0, vjust = .5, size = 2)) +
    ggtitle('STTR with CI per filename')

ggplot(corpora, aes(filename, sttr, color = brow)) +
    geom_pointrange(aes(ymax = sttr + ci, ymin = sttr - ci),
                    size = .1, fatten = .1, shape = 16) +
    coord_flip() +
    facet_grid(corpus_name ~ window, scales = 'free') +
    ## theme(axis.text.y = element_text(angle = 90, hjust = 0, vjust = .5, size = 2)) +
    ggtitle('STTR with CI per filename (inverted)')

dev.off()

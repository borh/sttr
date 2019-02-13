## Packages
library(readr)
library(dplyr)
library(ggplot2)

library(Kendall)
library(reshape2)

## Data
corpora <- read_tsv('merged_results.tsv', col_types = 'cfddddddfidffffi') %>% filter(Corpus_name!="grouptest")

corpora.melt <- melt(corpora %>% filter(Window==500) %>% select(-Window, -STTR_CI, -STTR_SD))

## Plots
cairo_pdf('sttr-plots.pdf', onefile = TRUE, width = 16, heigh = 12)

date <- as.POSIXct(Sys.time())

for (measure in c('STTR', 'Yules_K')) {
    g <- ggplot(corpora.melt %>% filter(variable==measure), aes(variable, value, color = Brow)) +
        geom_boxplot() +
        facet_grid(Type ~ Corpus_name, scales = 'free', space = 'fixed') +
        ggtitle(paste('Results matrix:', measure, date))
    print(g)
}

ggplot(corpora.melt %>% filter(variable=='Sent_len_mean') %>% filter(Type=='Tokenized'), aes(variable, value, color = Brow)) +
    geom_boxplot() +
    facet_grid(Type ~ Corpus_name, scales = 'free') +
    ggtitle(paste('Results matrix: Mean sentence length (Tokenized)', date))

for (measure in c('STTR', 'Yules_K')) {
    for (corpus in unique(corpora.melt$Corpus_name)) {
        d.authors <- corpora.melt %>%
            filter(variable==measure) %>%
            filter(Corpus_name==corpus) %>%
            filter(!is.na(Author))
        if (nrow(d.authors) > 1) {
            g <- ggplot(d.authors, aes(Author, value, color = Brow)) +
                geom_boxplot() +
                facet_wrap(~ Type, scales = 'free') +
                theme(axis.text.x = element_text(angle = 40, hjust = 1, vjust = 1)) +
                ggtitle(paste('By author:', measure, corpus, date))
            print(g)
        }
    }
}

dev.off()

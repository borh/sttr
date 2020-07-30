## Packages
library(readr)
library(dplyr)
library(ggplot2)

library(Kendall)
library(reshape2)

## Data
corpora <- read_csv('merged_results.tsv') %>% filter(Corpus_name!="grouptest")

corpora.melt <- melt(corpora 
		     # %>% filter(Window==10000) 
		     %>% select(-Window))

## Plots
get_os <- function(){
    sysinf <- Sys.info()
    if (!is.null(sysinf)){
        os <- sysinf['sysname']
    if (os == 'Darwin')
        os <- "osx"
    } else { ## mystery machine
        os <- .Platform$OS.type
        if (grepl("^darwin", R.version$os))
            os <- "osx"
        if (grepl("linux-gnu", R.version$os))
            os <- "linux"
    }
    tolower(os)
}
os <- get_os()

if (os == 'linux') {
    cairo_pdf('sttr-plots.pdf', onefile = TRUE, width = 16, heigh = 12)
} else if (os == 'osx') {
    pdf('sttr-plots.pdf', onefile = TRUE, width = 16, heigh = 12)
}

date <- as.POSIXct(Sys.time())

for (measure in c('STTR', 'Yules_K')) {
    g <- ggplot(corpora.melt %>% filter(variable==measure), aes(variable, value, color = Brow)) +
        geom_boxplot() + geom_jitter(position=position_jitterdodge(), size=0.3) +
        facet_grid(Type ~ Corpus_name, scales = 'free', space = 'fixed') +
        ggtitle(paste('Results matrix:', measure, date))
    print(g)
}

ggplot(corpora.melt %>% filter(variable=='Sent_len_mean') %>% filter(Type=='Tokenized'), aes(variable, value, color = Brow)) +
    geom_boxplot() + geom_jitter(position=position_jitterdodge(), size=0.3) +
    facet_grid(Type ~ Corpus_name, scales = 'free') +
    ggtitle(paste('Results matrix: Mean sentence length (Tokenized)', date))

ggplot(corpora.melt %>% filter(Type=='Tokenized'), aes(variable, value, group = Corpus_name, color = Corpus_name)) +
    geom_boxplot() + geom_jitter(position=position_jitterdodge(), size=0.3) +
    facet_wrap(vars(variable), scales = 'free') +
    ggtitle(paste('Results matrix: All (Tokenized)', date))


for (measure in c('STTR', 'Yules_K', 'Sent_len_mean')) {
    for (corpus in unique(corpora.melt$Corpus_name)) {
        d.authors <- corpora.melt %>%
            filter(variable==measure) %>%
            filter(Corpus_name==corpus) %>%
            filter(!is.na(Author)) %>%
            filter(!is.na(Brow))
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

import numpy as np
from ngslib import BigWigFile

from oncotator.datasources.Datasource import Datasource

class BigWigDatasource(Datasource):
    """
    A datasource derived from a BigWig file.  For variants spanning a genomic range (i.e. non SNVs),
    the median of values from the BigWig are returned.
    """
    def __init__(self, src_file, title='', version=None):
        super(BigWigDatasource, self).__init__(src_file, title=title, version=version)

        self.output_headers = [title + '_score']
        self.bigwig_fh = BigWigFile(src_file)
        self.has_chr = True if self.bigwig_fh.chroms[0].startswith('chr') else False

    def annotate_mutation(self, mutation):
        if self.has_chr and not mutation.chr.startswith('chr'):
            chrn = 'chr' + mutation.chr
        else:
            chrn = mutation.chr

        scores = [r.score for r in self.bigwig_fh.fetch(chrom=chrn, start=mutation.start - 1, stop=mutation.end)] #start - 1 because bigwig format is zero-based coords

        if not scores:
            final_score = None
        elif len(scores) == 1:
            final_score = scores[0]
        else:
            final_score = np.median(scores)

        mutation.createAnnotation(self.output_headers[0], final_score, annotationSource=self.title)
        return mutation

    def close(self):
        self.bigwig_fh.close()
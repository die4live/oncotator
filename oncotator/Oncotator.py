#!/usr/local/bin/python2.7
# encoding: utf-8
'''
Oncotator -- An annotation engine for Cancer

Oncotator is a description

It defines classes_and_methods

@author:     aramos, mgupta, and lichtens
        
@copyright:  2012 Broad Institute. All rights reserved.
        
@license:    TODO: license

@contact:    oncotator@broadinstitute.org
@deffield    updated: Updated
'''
import sys
if not (sys.version_info[0] == 2  and sys.version_info[1] in [ 7]):
    raise "Oncotator requires Python 2.7.x : " + str(sys.version_info)

import sys
import os

from argparse import ArgumentParser
from argparse import RawDescriptionHelpFormatter
import logging
from oncotator.utils.version import VERSION 
from oncotator.utils.OncotatorCLIUtils import OncotatorCLIUtils
from oncotator.Annotator import Annotator

__version__ = VERSION
__all__ = []

__date__ = '2012-12-29'
__updated__ = '2012-12-29'

DEBUG = 1
TESTRUN = 0
PROFILE = 1

#TODO: This needs to be dynamic from a config file.
# TODO: This needs to be changed.
DEFAULT_DB_DIR = '/xchip/cga1/lichtens/oncotator_ds_tmp'

class CLIError(Exception):
    '''Generic exception to raise and log different fatal errors.'''
    def __init__(self, msg):
        super(CLIError).__init__(type(self))
        self.msg = "E: %s" % msg
    def __str__(self):
        return self.msg
    def __unicode__(self):
        return self.msg

def parseOptions(program_license, program_version_message):
    # Setup argument parser
    epilog= '''
    
    Example usage :
    python Oncotator.py -v --input_format=MAFLITE --output_format=TCGAMAF myInputFile.maflite myOutputFile.maf.annotated hg19
    
    IMPORTANT NOTE:  hg19 is only supported genome build for now.

    Default values specified by -d or --default_annotation_values are used when an annotation does not exist or is populated with an empty string ("")

    Both default and override config files and command line specifications stack.
    '''
    parser = ArgumentParser(description=program_license, formatter_class=RawDescriptionHelpFormatter, epilog=epilog)
    parser.add_argument("-v", "--verbose", dest="verbose", action="count", help="set verbosity level [default: 0]", default=0)
    parser.add_argument('-V', '--version', action='version', version=program_version_message)
    parser.add_argument('-i', '--input_format', type=str, default="MAFLITE", choices=OncotatorCLIUtils.getSupportedInputFormats(),help='Input format.  Note that MAFLITE will work for any tsv file with appropriate headers, so long as all of the required headers (or an alias -- see maflite.config) are present.  [default: %s]' % "MAFLITE")
    parser.add_argument('--db-dir', dest='dbDir', default=DEFAULT_DB_DIR, 
        help='Main annotation database directory. [default: %s]' % DEFAULT_DB_DIR)
    parser.add_argument('-o' ,'--output_format', type=str, default="TCGAMAF",choices=OncotatorCLIUtils.getSupportedOutputFormats(),help='Output format. [default: %s]' % "TCGAMAF")
    parser.add_argument('--override_config', type=str, 
                        help="File path to manual annotations in a config file format (section is 'manual_annotations' and annotation:value pairs).")
    parser.add_argument('--default_config', type=str,
                        help="File path to default annotation values in a config file format (section is 'manual_annotations' and annotation:value pairs).")
    parser.add_argument('--no-multicore', dest="noMulticore", action='store_true', default=False, help="Disables all multicore functionality.")
    parser.add_argument('input_file', type=str,
                   help='Input file to be annotated.  Type is specified through options.')
    parser.add_argument('output_file', type=str, 
                    help='Output file name of annotated file.')
    parser.add_argument('genome_build', metavar='build', type=str, help="Genome build.  For example: hg19", choices=["hg19"])
    parser.add_argument('-a', '--annotate-manual', dest="override_cli",type=str, action='append', default=[], help="Specify annotations to override.  Can be specified multiple times.  E.g. -a 'name1:value1' -a 'name2:value2' ")
    parser.add_argument('-d', '--annotate-default', dest="default_cli",type=str, action='append', default=[], help="Specify default values for annotations.  Can be specified multiple times.  E.g. -d 'name1:value1' -a 'name2:value2' ")
    # Process arguments
    args = parser.parse_args()
    
    return args





def main(argv=None): # IGNORE:C0111
    '''Command line options.'''
    
    if argv is None:
        argv = sys.argv
    else:
        sys.argv.extend(argv)

    program_name = os.path.basename(sys.argv[0])
    program_version = "%s" % __version__
    program_build_date = str(__updated__)
    program_version_message = '%%(prog)s %s (%s)' % (program_version, program_build_date)
    program_shortdesc = program_version_message
    program_license = '''%s

    %s

  Copyright 2012 Broad Institute. All rights reserved.
  
  #TODO: License Here
  
  Distributed on an "AS IS" basis without warranties
  or conditions of any kind, either express or implied.

USAGE
''' % (program_shortdesc, str(__date__))

    try:
        args = parseOptions(program_license, program_version_message)
        verbose = args.verbose
        if verbose > 0:
            print("Verbose mode on")
        
        logFilename = 'oncotator.log'
        
        
        # Create a basic logger to a file
        loggingFormat = '%(asctime)s %(levelname)s [%(name)s:%(lineno)d] %(message)s'
        logging.basicConfig(filename=logFilename, level=logging.INFO, format=loggingFormat)
        
        
        # Add a console logger to the root logger, which means that all loggers generated will have the console dump.  
        #    Output on the console will be the same as what is in the log file. 
        ch = logging.StreamHandler()
        ch.setLevel(logging.WARN)
        formatter = logging.Formatter(loggingFormat)
        ch.setFormatter(formatter)
        
        if verbose:
            ch.setLevel(logging.INFO)
            print("Path:")
            print(sys.path)
            print(" ")
        
        logging.getLogger('').addHandler(ch)
        
        logger = logging.getLogger(__name__)
        logger.info("Args: " + str(args))
        logger.info('Log file: ' + os.path.abspath(logFilename))
        
        if DEBUG:
            logger.setLevel(logging.DEBUG)
        
        # Initiate an Oncotator session.
        inputFilename = args.input_file
        outputFilename = args.output_file
        inputFormat = args.input_format.upper()
        outputFormat = args.output_format.upper()
        datasourceDir = args.dbDir

        # Parse annotation overrides
        commandLineManualOverrides = args.override_cli
        overrideConfigFile = args.override_config
        manualOverrides = OncotatorCLIUtils.determineAllAnnotationValues(commandLineManualOverrides, overrideConfigFile)

        # Parse default overrides
        commandLineDefaultValues = args.default_cli
        defaultConfigFile = args.default_config
        defaultValues = OncotatorCLIUtils.determineAllAnnotationValues(commandLineDefaultValues, defaultConfigFile)

        # Create a run configuration to pass to the Annotator class.
        runConfig = OncotatorCLIUtils.createRunConfig(inputFormat, outputFormat, inputFilename, outputFilename, globalAnnotations=manualOverrides, datasourceDir=datasourceDir, isMulticore=(not args.noMulticore), defaultAnnotations=defaultValues)
           
        annotator = Annotator()
        annotator.initialize(runConfig)
        annotator.annotate()
        
        return 0
    except KeyboardInterrupt:
        ### handle keyboard interrupt ###
        return 0


def main_profile():
    import cProfile
    import pstats
    
    print("Profiling enabled...")
    profile_filename = 'Oncotator_profile.bin'
    cProfile.run('main()', profile_filename)
    statsfile = open("profile_stats.txt", "wb")
    p = pstats.Stats(profile_filename, stream=statsfile)
    stats = p.strip_dirs().sort_stats('cumulative')
    stats.print_stats()
    statsfile.close()
    sys.exit(0)    

if __name__ == "__main__":
    if DEBUG:
        sys.argv.append("-v")
        
    if TESTRUN:
        import doctest
        doctest.testmod()
    if PROFILE:
        main_profile()
    #sys.exit(main())
    main()
    
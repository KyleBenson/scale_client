#!/usr/bin/python

# @author: Kyle Benson
# (c) Kyle Benson 2018

STATISTICS_DESCRIPTION = """
A (very) basic script for parsing a bunch of statistical outputs and calculating some basic statistics from them.
You'll likely need to subclass the main class to handle your experimental setup and generate meaningful results.
"""

import logging
log = logging.getLogger(__name__)
import argparse
import sys
import os

import pandas as pd

from parsed_sensed_events import ParsedSensedEvents


class ScaleStatistics(object):
    """Parse results and visualize statistics e.g. reachability rate, latency (mininet exps only)."""

    def __init__(self, config):
        super(ScaleStatistics, self).__init__()

        if config.dirs is not None:
            self.files = self.gather_files_from_dirs(config.dirs)
        else:
            self.files = config.files
        self.config = config

        log_level = logging.getLevelName(config.debug.upper())
        log.setLevel(log_level)

        # the actual parsed stats
        self.stats = None  # type: pd.DataFrame

    @classmethod
    def get_arg_parser(cls, add_help=True):
        """Returns the argparse object for this class for use as a parent in your derived class,
        in which case set add_help=False to avoid arg conflicts."""
        ##################################################################################
        #################      ARGUMENTS       ###########################################
        # ArgumentParser.add_argument(name or flags...[, action][, nargs][, const][, default][, type][, choices][, required][, help][, metavar][, dest])
        # action is one of: store[_const,_true,_false], append[_const], count
        # nargs is one of: N, ?(defaults to const when no args), *, +, argparse.REMAINDER
        # help supports %(var)s: help='default value is %(default)s'
        ##################################################################################

        parser = argparse.ArgumentParser(description=STATISTICS_DESCRIPTION, add_help=add_help,
                                         # formatter_class=argparse.RawTextHelpFormatter,
                                         # epilog='Text to display at the end of the help print',
                                         )

        group = parser.add_mutually_exclusive_group()
        group.add_argument('--dirs', '-d', type=str, nargs="+",
                           help='''directories containing files from which to read outputs
                            (default=%(default)s)''')
        group.add_argument('--files', '-f', type=str, nargs="+", default=['results.json'],
                           help='''files from which to read output results
                            (default=%(default)s)''')

        parser.add_argument('--output-file', '-o', metavar='output_file', type=str, default=False,
                            help='''if specified, output the resulting DataFrame to a CSV file''')
        parser.add_argument('--debug', '--verbose', '-v', type=str, default='info', nargs='?', const='debug',
                            help='''set verbosity level for logging facility (default=%(default)s, %(const)s when specified with no arg)''')

        return parser

    @classmethod
    def parse_args(cls, args=None):
        """Parses the specified args or sys.argv by default."""
        parser = cls.get_arg_parser(add_help=True)
        if args is None:
            args = sys.argv[1:]

        return parser.parse_args(args)

    ### Functions you'll likely want to override in your own implementation

    def parse_results(self, results, filename, **params):
        """Parse the given results (raw string read from output file, likely containing JSON) using whichever
         ParsedSensedEvent object is selected by _choose_parser().  Return that resulting parsed object.
        :param results:
        :type results: str
        :param filename: the file these results were read from, which is potentially needed to determine the path of additional output files
        :param params: additional parameters related to these results; ignored by default
        :rtype: pd.DataFrame
        """
        parser = self.choose_parser(filename, **params)
        return parser(results, **params)

    def choose_parser(self, filename, **params):
        """
        Select which parser class should be used on the data extracted from this file.  params is currently ignored but
        may be useful for subclasses.  Default implementation always chooses ParsedSensedEvents
        NOTE: you'll likely want to override this method if you're using multiple different ParsedSensedEvent objects
        for parsing the different output files.
        :param filename:
        :param params:
        :return:
        :rtype: class[pd.DataFrame]
        """
        return ParsedSensedEvents

    def collate_results(self, *results):
        """
        Combine the given results into a single result.  By default, simply does a merge_all() on the DataFrames.
        :param results:
        :type results: list[results]
        :return:
        :rtype: pd.DataFrame
        """
        return self.merge_all(*results)

    ### Helper functions for working with the stats DataFrame object

    #########################################################################################################
    ####          FILTERING,  AGGREGATION,   and METRICS
    ### Helper functions for getting parsed outputs from certain types of clients
    ## Gathering certain types of results, which becomes hierarchical to build up to our final results
    #########################################################################################################

    def merge_all(self, *dfs):
        """
        Merges every data frame in dfs until only one is left.  This uses the 'reduce' function, 'outer' join,
        and doesn't sort the rows.
        :param dfs:
        :return:
        """
        return reduce(lambda left, right: pd.merge(left, right, how='outer', sort=False), dfs)

    # This will be used for the others
    def filter_outputs_by_params(self, logical_operator="and", **param_matches):
        """Filter the parsed outputs by the values of the specified column parameters (e.g. treatment, time_sent, etc.)
        The param_matches keys are columns and its values are the values that column should have in the resulting data.
        If you want to filter ranges of the data, just use the pandas DataFrame operations e.g.:
           df[df.col <= upper_bound]
        :param logical_operator: one of ("and", "or") for how to query the columns (all columns match or any match, respectively)
        :type logical_operator: str
        :rtype: pd.DataFrame
        """

        if logical_operator == "and":
            logical_operator = " & "
        elif logical_operator == "or":
            logical_operator = " | "
        else:
            raise ValueError("unrecognized logical_operator '%s'!  valid options are: 'or', 'and'")

        query_str = logical_operator.join('%s == "%s"' % (k, v) for k, v in param_matches)
        return self.stats.query(query_str)

    # ENHANCE: make filter handle operations other than ==  ?
    filter = filter_outputs_by_params

    def calc_latencies(self, data, time_sent_col='time_sent', time_rcvd_col='time_rcvd', resolution='ms'):
        """
        Adds a column to the given DataFrame with the latency (timedelta from specified sending time to receiving time),
        which is in the optionally requested resolution.
        NOTE: the time is expected in pandas format!  ParsedSensedEvent does this already using pandas.to_datetime

        :param data: the data to compute latencies on
        :type data: pd.DataFrame
        :param time_sent_col:
        :param time_rcvd_col:
        :param resolution: str representing the timedelta units/resolution e.g. ms, s, 10ms
        NOTE: resolution='10ms' would mean 1sec-->100; 13ms->1
        :rtype: pd.DataFrame
        """

        data['latency'] = (data[time_rcvd_col] - data[time_sent_col]).astype('timedelta64[%s]' % resolution)

        # ENHANCE: we can only do resampling when the INDEX is time, so we'd have to convert it to that first...
        # could help us look at only the events during a certain time period?
        # print 'LATENCY RESAMPLED:', picks['latency'].astype('timedelta64[ms]').resample('10ms')

        # ENHANCE: alternatively sample the latencies by event period using pd.cut with the bin edges being the event periods

        return data


    ### Helper functions to control flow of parsing files and outputting data

    def parse_all(self):
        """Parse all files and stores (as well as returns) the results as a single collated DataFrame in self.stats."""

        log.debug("parsing all files: %s" % self.files)
        stats = []
        for fname in self.files:
            results = self.parse_file(fname)

            # determine if we actually parsed anything before saving it
            try:
                # XXX: DataFrame throws error due to ambiguity of truth value
                is_results = bool(results)
            except ValueError:
                is_results = not results.empty  # hopefully a DataFrame

            if is_results:
                stats.append(results)

        if not stats:
            log.error("parse_all failed to generate any stats!")
            return None

        log.debug("done parsing files!  collating results...")
        self.stats = self.collate_results(*stats)
        log.info("final parsed results:\n %s" % self.stats)
        return self.stats

    def gather_files_from_dirs(self, dirs):
        """
        Collect all of the results files in the specified directory and return them as a list of file paths to be parsed
        :param dirs:
        :type dirs: list
        :return:
        :rtype: list[str]
        """

        log.debug("gathering files to parse from directories: %s" % dirs)
        results = []
        for dirname in dirs:
            for filename in os.listdir(dirname):
                filename = os.path.join(dirname, filename)
                # XXX: skip over progress indication files (RIDE-specific)
                if filename.endswith('.progress') or not os.path.isfile(filename):
                    continue

                results.append(filename)

        return results

    def parse_file(self, fname):
        """
        Parse the specified file and return the parsed DataFrame object
        :param fname:
        :return:
        :rtype: pd.DataFrame
        """
        log.debug("parsing file: %s" % fname)
        results = self.read_file(fname)
        try:
            results = self.parse_results(results, fname)
        except BaseException as e:
            log.error("parse_results skipping file %s that caused error: %s" % (fname, e))
            return None
        return results

    @staticmethod
    def read_file(fname):
        """Reads the file (likely JSON-encoded) and returns the raw string contents.
         Returns None if it fails and logs the error."""
        with open(fname) as f:
            # this try statement was added because the -d <dir> option didn't work with .progress files
            try:
                data = f.read()
            except (ValueError, IOError) as e:
                log.debug("Skipping file %s that raised error: %s" % (fname, e))
                return None
        return data

    def output_stats(self, stats=None, filename=None):
        """Outputs the specified stats object (self.stats by default) to the
        specified file (self.config.output_file by default) in CSV format."""
        if stats is None:
            stats = self.stats
        if filename is None:
            filename = self.config.output_file
        stats.to_csv(filename, index=False)

    @classmethod
    def main(cls):
        logging.basicConfig(format='%(levelname)s:%(message)s')  # if running stand-alone

        if len(sys.argv) > 1 and sys.argv[1] == 'test':
            run_tests()
            exit()

        # lets you print the data frames out on a wider screen
        pd.set_option('display.max_columns', 25)
        pd.set_option('display.width', 2500)

        args = sys.argv[1:]
        args = cls.parse_args(args)

        ## Manually set arguments, esp. if using an IDE rather than command line
        # args.debug = 'debug'
        # args.output_file = 'parsed_results/stats.csv'

        stats = cls(args)
        stats.parse_all()

        return stats


def run_tests():
    # TODO:
    raise NotImplementedError("no tests defined yet!")


if __name__ == '__main__':
    stats = ScaleStatistics.main()

    # now you can do something with the stats to e.g. get your own custom experiment results
    final_stats = stats.stats

    if stats.config.output_file:
        stats.output_stats(stats=final_stats)


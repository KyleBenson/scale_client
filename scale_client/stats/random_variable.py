import numbers

import numpy.random

from scale_client.util.common import _get_class_by_name
import logging
log = logging.getLogger(__name__)


class RandomVariable(object):
    """
    A wrapper class around `scipy.stats` random variables that adds optional bounds to the generated values and
    allows for creation through simple kwargs e.g. defining it as a dict:
    {'dist': 'zipf', 'seed': 1234, 'args': [2], ...}
    """

    def __init__(self, dist, args=(), seed=None, lbound=None, ubound=None, **kwargs):
        """
        :param dist: a classpath to the random variable distribution e.g. scipy.stats.zipf, zipf, rv_discrete
            (will append 'scipy.stats.' to it if first import fails)
            NOTE: we also add distribution 'const' for which the returned value is always args[0]
        :param args: positional arguments to the distribution e.g. lambda for exponential
        :param seed: random seed value
        :param lbound: optional lower bound for values drawn from the distribution
        :param ubound: optional upper bound for values drawn from the distribution
        :param kwargs: additional kwargs to pass to the underlying distribution class
        """

        self.dist = dist
        self.args = args
        self.lower_bound = lbound
        self.upper_bound = ubound
        self.extra_kwargs = kwargs

        # XXX: because we can't freeze the RV with a random_state, we need to create a separate RandomState object
        # to pass to the RV each time we draw from it
        self.seed = seed
        self._rand_state = numpy.random.RandomState(seed)


        # Tweak the parameters first to make things easier for user.
        # XXX: can specify a constant numeric value instead of using RV distributions
        if self.dist == 'const':
            self._rand_var = args[0]
            return

        # Some aliases:
        if dist == 'exponential' or dist == 'exp':
            dist = 'expon'
        elif dist in ('normal', 'gauss', 'gaussian'):
            dist = 'norm'

        # Now distribution-specific tweaks
        # XXX: the first parameter is 'loc', which shifts the distribution.  we want to scale it with lambda
        if dist == 'expon':
            args = [0] + list(args)

        # lookup the class by its path and create an instance
        try:
            rv_cls = _get_class_by_name(dist)
        except ValueError:
            backup_dist = 'scipy.stats.' + dist
            try:
                rv_cls = _get_class_by_name(backup_dist)
            except ValueError:
                raise ValueError("failed to import random variable distribution %s or the backup attempt of %s:"
                                 " check your PYTHONPATH!" % (dist, backup_dist))

        self._rand_var = rv_cls(*args, **kwargs)

    def get(self):

        if self.dist == 'const':
            return self._rand_var

        # NOTE: we redraw from the distribution if the bounds aren't met in order to avoid 'bunching up' the results at the bounds
        bounds_met = False
        max_redraws = 10000
        while not bounds_met and max_redraws > 0:
            d = self._rand_var.rvs(random_state=self._rand_state)
            bounds_met = True
            if self.lower_bound is not None and d < self.lower_bound:
                bounds_met = False
            if self.upper_bound is not None and d > self.upper_bound:
                bounds_met = False
            max_redraws -= 1

        if max_redraws == 0:
            raise ValueError("failed to draw a random variable within the requested bounds (%s, %s) after"
                             "10000 attempts!  Check your bounds..." % (self.lower_bound, self.upper_bound))
        return d

    def get_int(self):
        if self.dist == 'const':
            return int(self._rand_var)

        d = self.get()
        return int(d + 0.5)

    def pdf(self, val):
        """Returns the probability density at the specified value."""

        if self.dist == 'const':
            return self._rand_var if val == self._rand_var else 0

        return self._rand_var.pdf(val)

    @classmethod
    def build(cls, config):
        """
        Builds a RandomVariable instance from the specified configuration, which may be a constant value, string name
        of the distribution to use, or a configuration dict e.g. {'dist': 'uniform', 'args': [0, 10]}
        :param config:
        :return:
        """
        config = cls.expand_config(config)
        return cls(**config)

    @classmethod
    def expand_config(cls, config):
        """
        Expands the configuration parameter from possibly a constant numeric or just the name of the distribution into
        a complete dict that can be passed to the build function.
        :param config:
        :return:
        :rtype: dict
        """
        if isinstance(config, basestring):
            config = dict(dist=config)
        elif isinstance(config, numbers.Number):
            config = dict(dist='const', args=(config,))
        elif not isinstance(config, dict):
            raise TypeError("unrecognized RandomVariable configuration type: not a distribution name (str), dict of"
                            " params or constant numeric! params: %s" % config)
        return config

    def sample(self, population, nselections):
        """
        Using the underlying random distribution (i.e. its random values as indices), draw nselections samples from the
        specified population without repeat.
        :param population:
        :type population: list
        :param nselections:
        :raises ValueError: if requesting more selections than the population has or if underlying distribution fails
            to generate enough unique indices within a reasonable number of iterations
        :return:
        :rtype: list
        """

        if self.dist == 'const':
            raise TypeError("can't sample a population using a constant random variable!")

        if nselections > len(population):
            raise ValueError("requested too many selections (%d) from population with only %d items!" % (nselections, len(population)))

        max_redraws = max(1000, nselections**nselections*10)
        results = set()

        while len(results) < nselections and max_redraws > 0:
            i = self.get_int()
            try:
                results.add(population[i])
            except IndexError:
                pass  # out of range
            max_redraws -= 1

        if max_redraws <= 0 and len(results) < nselections:
            raise ValueError("failed to draw enough unique samples of the given population after many tries... check your distribution's bounds!")

        return list(results)

    def is_upper_bounded(self):
        """
        Returns true if the maximum returned value has an upper bound.  Useful for checking if some bounds need to be
        set to ensure we can properly call RV.sample(...) without hitting max_redraws.
        :return:
        """

        if self.dist == 'const':
            return False

        try:
            l, u = self.bounds()
            if u < float('inf'):
                return True
        except AttributeError as e:
            log.warning("failed to get interval of random variable %s\nError was: %s" % (self._rand_var, e))
        return False

    # TODO:
    # def mean(self):

    def bounds(self):
        """
        Returns a 2-tuple of (lower_bound, upper_bound)
        :return:
        """
        if self.dist == 'const':
            return [self._rand_var]*2

        # TODO: should probably consider the user-specified upper/lower bound here too!
        return self._rand_var.interval(1)
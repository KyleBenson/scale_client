import unittest

from scale_client.stats.random_variable import RandomVariable

ntests = 100  # set to larger numbers to be more certain everything is okay, but tests will take longer

class TestRandomVariable(unittest.TestCase):
    def test_distributions(self):
        # uniform
        rv = RandomVariable(dist='uniform', args=[5, 10])
        vals = [rv.get() for i in range(ntests)]
        self.assertTrue(all(5 <= i < 15 for i in vals), "not all values in expected range! got: %s" % vals)

        # zipf
        rv = RandomVariable(dist='zipf', args=[2, 2])
        vals = [rv.get() for i in range(ntests)]
        self.assertGreater(sum(vals), len(vals))  # at least one value should be > 1


        # TODO:
        # exponential


    def test_sampling(self):
        rv = RandomVariable(dist='uniform', args=[5, 10])
        res = rv.sample(range(15), 5)
        self.assertEqual(len(res), 5)
        self.assertEqual(len(set(res)), 5, "not all samples are unique! got: %s" % res)
        self.assertTrue(all(5 <= x < 15 for x in res), "samples outside of expected population range! got: %s" % res)

        # edge case
        res = rv.sample(range(10, 20), 1)
        self.assertEqual(len(res), 1)
        self.assertTrue(15 <= res[0] < 20)

        # skewed distributions
        rv = RandomVariable(dist='zipf', args=[2, -1])  # for sampling should shift dist. down
        res = rv.sample(range(15), 5)
        self.assertEqual(len(res), 5)
        self.assertEqual(len(set(res)), 5, "not all samples are unique! got: %s" % res)
        self.assertTrue(all(0 <= x < 15 for x in res), "samples outside of expected population range! got: %s" % res)


if __name__ == '__main__':
    unittest.main()

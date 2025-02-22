#
# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

from distutils.version import LooseVersion

import numpy as np
import pandas as pd

from pyspark import pandas as ps
from pyspark.pandas.config import set_option, reset_option
from pyspark.testing.pandasutils import PandasOnSparkTestCase, TestUtils


class OpsOnDiffFramesGroupByExpandingTest(PandasOnSparkTestCase, TestUtils):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        set_option("compute.ops_on_diff_frames", True)

    @classmethod
    def tearDownClass(cls):
        reset_option("compute.ops_on_diff_frames")
        super().tearDownClass()

    def _test_groupby_expanding_func(self, f):
        pser = pd.Series([1, 2, 3])
        pkey = pd.Series([1, 2, 3], name="a")
        psser = ps.from_pandas(pser)
        kkey = ps.from_pandas(pkey)

        self.assert_eq(
            getattr(psser.groupby(kkey).expanding(2), f)().sort_index(),
            getattr(pser.groupby(pkey).expanding(2), f)().sort_index(),
        )

        pdf = pd.DataFrame({"a": [1, 2, 3, 2], "b": [4.0, 2.0, 3.0, 1.0]})
        pkey = pd.Series([1, 2, 3, 2], name="a")
        psdf = ps.from_pandas(pdf)
        kkey = ps.from_pandas(pkey)

        if LooseVersion(pd.__version__) >= LooseVersion("1.3"):
            # TODO(SPARK-36367): Fix the behavior to follow pandas >= 1.3
            pass
        else:
            self.assert_eq(
                getattr(psdf.groupby(kkey).expanding(2), f)().sort_index(),
                getattr(pdf.groupby(pkey).expanding(2), f)().sort_index(),
            )

        self.assert_eq(
            getattr(psdf.groupby(kkey)["b"].expanding(2), f)().sort_index(),
            getattr(pdf.groupby(pkey)["b"].expanding(2), f)().sort_index(),
        )
        self.assert_eq(
            getattr(psdf.groupby(kkey)[["b"]].expanding(2), f)().sort_index(),
            getattr(pdf.groupby(pkey)[["b"]].expanding(2), f)().sort_index(),
        )

    def test_groupby_expanding_count(self):
        # The behaviour of ExpandingGroupby.count are different between pandas>=1.0.0 and lower,
        # and we're following the behaviour of latest version of pandas.
        if LooseVersion(pd.__version__) >= LooseVersion("1.0.0"):
            self._test_groupby_expanding_func("count")
        else:
            # Series
            psser = ps.Series([1, 2, 3])
            kkey = ps.Series([1, 2, 3], name="a")
            midx = pd.MultiIndex.from_tuples(
                list(zip(kkey.to_pandas().values, psser.index.to_pandas().values)),
                names=["a", None],
            )
            expected_result = pd.Series([np.nan, np.nan, np.nan], index=midx)
            self.assert_eq(
                psser.groupby(kkey).expanding(2).count().sort_index(), expected_result.sort_index()
            )

            # DataFrame
            psdf = ps.DataFrame({"a": [1, 2, 3, 2], "b": [4.0, 2.0, 3.0, 1.0]})
            kkey = ps.Series([1, 2, 3, 2], name="a")
            midx = pd.MultiIndex.from_tuples([(1, 0), (2, 1), (2, 3), (3, 2)], names=["a", None])
            expected_result = pd.DataFrame(
                {"a": [None, None, 2.0, None], "b": [None, None, 2.0, None]}, index=midx
            )
            self.assert_eq(
                psdf.groupby(kkey).expanding(2).count().sort_index(), expected_result.sort_index()
            )
            expected_result = pd.Series([None, None, 2.0, None], index=midx, name="b")
            self.assert_eq(
                psdf.groupby(kkey)["b"].expanding(2).count().sort_index(),
                expected_result.sort_index(),
            )
            expected_result = pd.DataFrame({"b": [None, None, 2.0, None]}, index=midx)
            self.assert_eq(
                psdf.groupby(kkey)[["b"]].expanding(2).count().sort_index(),
                expected_result.sort_index(),
            )

    def test_groupby_expanding_min(self):
        self._test_groupby_expanding_func("min")

    def test_groupby_expanding_max(self):
        self._test_groupby_expanding_func("max")

    def test_groupby_expanding_mean(self):
        self._test_groupby_expanding_func("mean")

    def test_groupby_expanding_sum(self):
        self._test_groupby_expanding_func("sum")

    def test_groupby_expanding_std(self):
        self._test_groupby_expanding_func("std")

    def test_groupby_expanding_var(self):
        self._test_groupby_expanding_func("var")


if __name__ == "__main__":
    import unittest
    from pyspark.pandas.tests.test_ops_on_diff_frames_groupby_expanding import *  # noqa: F401

    try:
        import xmlrunner  # type: ignore[import]

        testRunner = xmlrunner.XMLTestRunner(output="target/test-reports", verbosity=2)
    except ImportError:
        testRunner = None
    unittest.main(testRunner=testRunner, verbosity=2)

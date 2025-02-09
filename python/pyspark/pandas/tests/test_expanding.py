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

import pyspark.pandas as ps
from pyspark.pandas.window import Expanding
from pyspark.testing.pandasutils import PandasOnSparkTestCase, TestUtils


class ExpandingTest(PandasOnSparkTestCase, TestUtils):
    def _test_expanding_func(self, f):
        pser = pd.Series([1, 2, 3], index=np.random.rand(3))
        psser = ps.from_pandas(pser)
        self.assert_eq(getattr(psser.expanding(2), f)(), getattr(pser.expanding(2), f)())
        self.assert_eq(
            getattr(psser.expanding(2), f)().sum(), getattr(pser.expanding(2), f)().sum()
        )

        # Multiindex
        pser = pd.Series(
            [1, 2, 3], index=pd.MultiIndex.from_tuples([("a", "x"), ("a", "y"), ("b", "z")])
        )
        psser = ps.from_pandas(pser)
        self.assert_eq(getattr(psser.expanding(2), f)(), getattr(pser.expanding(2), f)())

        pdf = pd.DataFrame(
            {"a": [1.0, 2.0, 3.0, 2.0], "b": [4.0, 2.0, 3.0, 1.0]}, index=np.random.rand(4)
        )
        psdf = ps.from_pandas(pdf)
        self.assert_eq(getattr(psdf.expanding(2), f)(), getattr(pdf.expanding(2), f)())
        self.assert_eq(getattr(psdf.expanding(2), f)().sum(), getattr(pdf.expanding(2), f)().sum())

        # Multiindex column
        columns = pd.MultiIndex.from_tuples([("a", "x"), ("a", "y")])
        pdf.columns = columns
        psdf.columns = columns
        self.assert_eq(getattr(psdf.expanding(2), f)(), getattr(pdf.expanding(2), f)())

    def test_expanding_error(self):
        with self.assertRaisesRegex(ValueError, "min_periods must be >= 0"):
            ps.range(10).expanding(-1)

        with self.assertRaisesRegex(
            TypeError, "psdf_or_psser must be a series or dataframe; however, got:.*int"
        ):
            Expanding(1, 2)

    def test_expanding_repr(self):
        self.assertEqual(repr(ps.range(10).expanding(5)), "Expanding [min_periods=5]")

    def test_expanding_count(self):
        # The behaviour of Expanding.count are different between pandas>=1.0.0 and lower,
        # and we're following the behaviour of latest version of pandas.
        if LooseVersion(pd.__version__) >= LooseVersion("1.0.0"):
            self._test_expanding_func("count")
        else:
            # Series
            idx = np.random.rand(3)
            psser = ps.Series([1, 2, 3], index=idx, name="a")
            expected_result = pd.Series([None, 2.0, 3.0], index=idx, name="a")
            self.assert_eq(psser.expanding(2).count().sort_index(), expected_result.sort_index())
            self.assert_eq(psser.expanding(2).count().sum(), expected_result.sum())

            # MultiIndex
            midx = pd.MultiIndex.from_tuples([("a", "x"), ("a", "y"), ("b", "z")])
            psser = ps.Series([1, 2, 3], index=midx, name="a")
            expected_result = pd.Series([None, 2.0, 3.0], index=midx, name="a")
            self.assert_eq(psser.expanding(2).count().sort_index(), expected_result.sort_index())

            # DataFrame
            psdf = ps.DataFrame({"a": [1, 2, 3, 2], "b": [4.0, 2.0, 3.0, 1.0]})
            expected_result = pd.DataFrame({"a": [None, 2.0, 3.0, 4.0], "b": [None, 2.0, 3.0, 4.0]})
            self.assert_eq(psdf.expanding(2).count().sort_index(), expected_result.sort_index())
            self.assert_eq(psdf.expanding(2).count().sum(), expected_result.sum())

            # MultiIndex columns
            idx = np.random.rand(4)
            psdf = ps.DataFrame({"a": [1, 2, 3, 2], "b": [4.0, 2.0, 3.0, 1.0]}, index=idx)
            psdf.columns = pd.MultiIndex.from_tuples([("a", "x"), ("a", "y")])
            expected_result = pd.DataFrame(
                {("a", "x"): [None, 2.0, 3.0, 4.0], ("a", "y"): [None, 2.0, 3.0, 4.0]},
                index=idx,
            )
            self.assert_eq(psdf.expanding(2).count().sort_index(), expected_result.sort_index())

    def test_expanding_min(self):
        self._test_expanding_func("min")

    def test_expanding_max(self):
        self._test_expanding_func("max")

    def test_expanding_mean(self):
        self._test_expanding_func("mean")

    def test_expanding_sum(self):
        self._test_expanding_func("sum")

    def test_expanding_std(self):
        self._test_expanding_func("std")

    def test_expanding_var(self):
        self._test_expanding_func("var")

    def _test_groupby_expanding_func(self, f):
        pser = pd.Series([1, 2, 3, 2], index=np.random.rand(4), name="a")
        psser = ps.from_pandas(pser)
        self.assert_eq(
            getattr(psser.groupby(psser).expanding(2), f)().sort_index(),
            getattr(pser.groupby(pser).expanding(2), f)().sort_index(),
        )
        self.assert_eq(
            getattr(psser.groupby(psser).expanding(2), f)().sum(),
            getattr(pser.groupby(pser).expanding(2), f)().sum(),
        )

        # Multiindex
        pser = pd.Series(
            [1, 2, 3, 2],
            index=pd.MultiIndex.from_tuples([("a", "x"), ("a", "y"), ("b", "z"), ("c", "z")]),
            name="a",
        )
        psser = ps.from_pandas(pser)
        self.assert_eq(
            getattr(psser.groupby(psser).expanding(2), f)().sort_index(),
            getattr(pser.groupby(pser).expanding(2), f)().sort_index(),
        )

        pdf = pd.DataFrame({"a": [1.0, 2.0, 3.0, 2.0], "b": [4.0, 2.0, 3.0, 1.0]})
        psdf = ps.from_pandas(pdf)

        if LooseVersion(pd.__version__) >= LooseVersion("1.3"):
            # TODO(SPARK-36367): Fix the behavior to follow pandas >= 1.3
            pass
        else:
            self.assert_eq(
                getattr(psdf.groupby(psdf.a).expanding(2), f)().sort_index(),
                getattr(pdf.groupby(pdf.a).expanding(2), f)().sort_index(),
            )
            self.assert_eq(
                getattr(psdf.groupby(psdf.a).expanding(2), f)().sum(),
                getattr(pdf.groupby(pdf.a).expanding(2), f)().sum(),
            )
            self.assert_eq(
                getattr(psdf.groupby(psdf.a + 1).expanding(2), f)().sort_index(),
                getattr(pdf.groupby(pdf.a + 1).expanding(2), f)().sort_index(),
            )

        self.assert_eq(
            getattr(psdf.b.groupby(psdf.a).expanding(2), f)().sort_index(),
            getattr(pdf.b.groupby(pdf.a).expanding(2), f)().sort_index(),
        )
        self.assert_eq(
            getattr(psdf.groupby(psdf.a)["b"].expanding(2), f)().sort_index(),
            getattr(pdf.groupby(pdf.a)["b"].expanding(2), f)().sort_index(),
        )
        self.assert_eq(
            getattr(psdf.groupby(psdf.a)[["b"]].expanding(2), f)().sort_index(),
            getattr(pdf.groupby(pdf.a)[["b"]].expanding(2), f)().sort_index(),
        )

        # Multiindex column
        columns = pd.MultiIndex.from_tuples([("a", "x"), ("a", "y")])
        pdf.columns = columns
        psdf.columns = columns

        if LooseVersion(pd.__version__) >= LooseVersion("1.3"):
            # TODO(SPARK-36367): Fix the behavior to follow pandas >= 1.3
            pass
        else:
            self.assert_eq(
                getattr(psdf.groupby(("a", "x")).expanding(2), f)().sort_index(),
                getattr(pdf.groupby(("a", "x")).expanding(2), f)().sort_index(),
            )

            self.assert_eq(
                getattr(psdf.groupby([("a", "x"), ("a", "y")]).expanding(2), f)().sort_index(),
                getattr(pdf.groupby([("a", "x"), ("a", "y")]).expanding(2), f)().sort_index(),
            )

    def test_groupby_expanding_count(self):
        # The behaviour of ExpandingGroupby.count are different between pandas>=1.0.0 and lower,
        # and we're following the behaviour of latest version of pandas.
        if LooseVersion(pd.__version__) >= LooseVersion("1.0.0"):
            self._test_groupby_expanding_func("count")
        else:
            # Series
            psser = ps.Series([1, 2, 3, 2], index=np.random.rand(4))
            midx = pd.MultiIndex.from_tuples(
                list(zip(psser.to_pandas().values, psser.index.to_pandas().values))
            )
            expected_result = pd.Series([np.nan, np.nan, np.nan, 2], index=midx)
            self.assert_eq(
                psser.groupby(psser).expanding(2).count().sort_index(), expected_result.sort_index()
            )
            self.assert_eq(psser.groupby(psser).expanding(2).count().sum(), expected_result.sum())

            # MultiIndex
            psser = ps.Series(
                [1, 2, 3, 2],
                index=pd.MultiIndex.from_tuples([("a", "x"), ("a", "y"), ("b", "z"), ("a", "y")]),
            )
            midx = pd.MultiIndex.from_tuples(
                [(1, "a", "x"), (2, "a", "y"), (3, "b", "z"), (2, "a", "y")]
            )
            expected_result = pd.Series([np.nan, np.nan, np.nan, 2], index=midx)
            self.assert_eq(
                psser.groupby(psser).expanding(2).count().sort_index(), expected_result.sort_index()
            )

            # DataFrame
            psdf = ps.DataFrame({"a": [1, 2, 3, 2], "b": [4.0, 2.0, 3.0, 1.0]})
            midx = pd.MultiIndex.from_tuples([(1, 0), (2, 1), (2, 3), (3, 2)], names=["a", None])
            expected_result = pd.DataFrame(
                {"a": [None, None, 2.0, None], "b": [None, None, 2.0, None]}, index=midx
            )
            self.assert_eq(
                psdf.groupby(psdf.a).expanding(2).count().sort_index(), expected_result.sort_index()
            )
            self.assert_eq(psdf.groupby(psdf.a).expanding(2).count().sum(), expected_result.sum())
            expected_result = pd.DataFrame(
                {"a": [None, None, 2.0, None], "b": [None, None, 2.0, None]},
                index=pd.MultiIndex.from_tuples(
                    [(2, 0), (3, 1), (3, 3), (4, 2)], names=["a", None]
                ),
            )
            self.assert_eq(
                psdf.groupby(psdf.a + 1).expanding(2).count().sort_index(),
                expected_result.sort_index(),
            )
            expected_result = pd.Series([None, None, 2.0, None], index=midx, name="b")
            self.assert_eq(
                psdf.b.groupby(psdf.a).expanding(2).count().sort_index(),
                expected_result.sort_index(),
            )
            self.assert_eq(
                psdf.groupby(psdf.a)["b"].expanding(2).count().sort_index(),
                expected_result.sort_index(),
            )
            expected_result = pd.DataFrame({"b": [None, None, 2.0, None]}, index=midx)
            self.assert_eq(
                psdf.groupby(psdf.a)[["b"]].expanding(2).count().sort_index(),
                expected_result.sort_index(),
            )

            # MultiIndex column
            psdf = ps.DataFrame({"a": [1, 2, 3, 2], "b": [4.0, 2.0, 3.0, 1.0]})
            psdf.columns = pd.MultiIndex.from_tuples([("a", "x"), ("a", "y")])
            midx = pd.MultiIndex.from_tuples(
                [(1, 0), (2, 1), (2, 3), (3, 2)], names=[("a", "x"), None]
            )
            expected_result = pd.DataFrame(
                {"a": [None, None, 2.0, None], "b": [None, None, 2.0, None]}, index=midx
            )
            expected_result.columns = pd.MultiIndex.from_tuples([("a", "x"), ("a", "y")])
            self.assert_eq(
                psdf.groupby(("a", "x")).expanding(2).count().sort_index(),
                expected_result.sort_index(),
            )
            midx = pd.MultiIndex.from_tuples(
                [(1, 4.0, 0), (2, 1.0, 3), (2, 2.0, 1), (3, 3.0, 2)],
                names=[("a", "x"), ("a", "y"), None],
            )
            expected_result = pd.DataFrame(
                {
                    ("a", "x"): [np.nan, np.nan, np.nan, np.nan],
                    ("a", "y"): [np.nan, np.nan, np.nan, np.nan],
                },
                index=midx,
            )
            self.assert_eq(
                psdf.groupby([("a", "x"), ("a", "y")]).expanding(2).count().sort_index(),
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
    from pyspark.pandas.tests.test_expanding import *  # noqa: F401

    try:
        import xmlrunner  # type: ignore[import]

        testRunner = xmlrunner.XMLTestRunner(output="target/test-reports", verbosity=2)
    except ImportError:
        testRunner = None
    unittest.main(testRunner=testRunner, verbosity=2)

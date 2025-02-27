# -*- encoding: utf-8 -*-
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
from pyspark.sql.functions import sha2, to_timestamp
from pyspark.errors import (
    AnalysisException,
    ParseException,
    PySparkAssertionError,
    IllegalArgumentException,
    SparkUpgradeException,
)
from pyspark.testing.utils import assertDataFrameEqual, assertSchemaEqual
from pyspark.testing.sqlutils import ReusedSQLTestCase
import pyspark.sql.functions as F
from pyspark.sql.functions import to_date, unix_timestamp, from_unixtime
from pyspark.sql.types import (
    StringType,
    ArrayType,
    LongType,
    StructType,
    MapType,
    FloatType,
    DoubleType,
    StructField,
    IntegerType,
    BooleanType,
)

import difflib


class UtilsTestsMixin:
    def test_assert_equal_inttype(self):
        df1 = self.spark.createDataFrame(
            data=[
                ("1", 1000),
                ("2", 3000),
            ],
            schema=["id", "amount"],
        )
        df2 = self.spark.createDataFrame(
            data=[
                ("1", 1000),
                ("2", 3000),
            ],
            schema=["id", "amount"],
        )

        assertDataFrameEqual(df1, df2, checkRowOrder=False)
        assertDataFrameEqual(df1, df2, checkRowOrder=True)

    def test_assert_equal_arraytype(self):
        df1 = self.spark.createDataFrame(
            data=[
                ("john", ["Python", "Java"]),
                ("jane", ["Scala", "SQL", "Java"]),
            ],
            schema=StructType(
                [
                    StructField("name", StringType(), True),
                    StructField("languages", ArrayType(StringType()), True),
                ]
            ),
        )
        df2 = self.spark.createDataFrame(
            data=[
                ("john", ["Python", "Java"]),
                ("jane", ["Scala", "SQL", "Java"]),
            ],
            schema=StructType(
                [
                    StructField("name", StringType(), True),
                    StructField("languages", ArrayType(StringType()), True),
                ]
            ),
        )

        assertDataFrameEqual(df1, df2, checkRowOrder=False)
        assertDataFrameEqual(df1, df2, checkRowOrder=True)

    def test_assert_approx_equal_arraytype_float(self):
        df1 = self.spark.createDataFrame(
            data=[
                ("student1", [97.01, 89.23]),
                ("student2", [91.86, 84.34]),
            ],
            schema=StructType(
                [
                    StructField("student", StringType(), True),
                    StructField("grades", ArrayType(FloatType()), True),
                ]
            ),
        )
        df2 = self.spark.createDataFrame(
            data=[
                ("student1", [97.01, 89.23]),
                ("student2", [91.86, 84.339999]),
            ],
            schema=StructType(
                [
                    StructField("student", StringType(), True),
                    StructField("grades", ArrayType(FloatType()), True),
                ]
            ),
        )

        assertDataFrameEqual(df1, df2, checkRowOrder=False)
        assertDataFrameEqual(df1, df2, checkRowOrder=True)

    def test_assert_approx_equal_arraytype_float_default_rtol_fail(self):
        # fails with default rtol, 1e-5
        df1 = self.spark.createDataFrame(
            data=[
                ("student1", [97.01, 89.23]),
                ("student2", [91.86, 84.34]),
            ],
            schema=StructType(
                [
                    StructField("student", StringType(), True),
                    StructField("grades", ArrayType(FloatType()), True),
                ]
            ),
        )
        df2 = self.spark.createDataFrame(
            data=[
                ("student1", [97.01, 89.23]),
                ("student2", [91.86, 84.341]),
            ],
            schema=StructType(
                [
                    StructField("student", StringType(), True),
                    StructField("grades", ArrayType(FloatType()), True),
                ]
            ),
        )

        expected_error_message = "Results do not match: "
        percent_diff = (1 / 2) * 100
        expected_error_message += "( %.5f %% )" % percent_diff
        diff_msg = (
            "[actual]"
            + "\n"
            + str(df1.collect()[1])
            + "\n\n"
            + "[expected]"
            + "\n"
            + str(df2.collect()[1])
            + "\n\n"
            + "********************"
            + "\n\n"
        )
        expected_error_message += "\n" + diff_msg

        with self.assertRaises(PySparkAssertionError) as pe:
            assertDataFrameEqual(df1, df2)

        self.check_error(
            exception=pe.exception,
            error_class="DIFFERENT_ROWS",
            message_parameters={"error_msg": expected_error_message},
        )

    def test_assert_approx_equal_arraytype_float_custom_rtol_pass(self):
        # passes with custom rtol, 1e-2
        df1 = self.spark.createDataFrame(
            data=[
                ("student1", [97.01, 89.23]),
                ("student2", [91.86, 84.34]),
            ],
            schema=StructType(
                [
                    StructField("student", StringType(), True),
                    StructField("grades", ArrayType(FloatType()), True),
                ]
            ),
        )
        df2 = self.spark.createDataFrame(
            data=[
                ("student1", [97.01, 89.23]),
                ("student2", [91.86, 84.341]),
            ],
            schema=StructType(
                [
                    StructField("student", StringType(), True),
                    StructField("grades", ArrayType(FloatType()), True),
                ]
            ),
        )

        assertDataFrameEqual(df1, df2, rtol=1e-2)

    def test_assert_approx_equal_doubletype_custom_rtol_pass(self):
        # passes with custom rtol, 1e-2
        df1 = self.spark.createDataFrame(
            data=[
                ("student1", 97.01),
                ("student2", 84.34),
            ],
            schema=StructType(
                [
                    StructField("student", StringType(), True),
                    StructField("grade", DoubleType(), True),
                ]
            ),
        )
        df2 = self.spark.createDataFrame(
            data=[
                ("student1", 97.01),
                ("student2", 84.341),
            ],
            schema=StructType(
                [
                    StructField("student", StringType(), True),
                    StructField("grade", DoubleType(), True),
                ]
            ),
        )

        assertDataFrameEqual(df1, df2, rtol=1e-2)

    def test_assert_approx_equal_decimaltype_custom_rtol_pass(self):
        # passes with custom rtol, 1e-2
        df1 = self.spark.createDataFrame(
            data=[
                ("student1", 83.14),
                ("student2", 97.12),
            ],
            schema=StructType(
                [
                    StructField("student", StringType(), True),
                    StructField("grade", DoubleType(), True),
                ]
            ),
        )
        df2 = self.spark.createDataFrame(
            data=[
                ("student1", 83.14),
                ("student2", 97.111),
            ],
            schema=StructType(
                [
                    StructField("student", StringType(), True),
                    StructField("grade", DoubleType(), True),
                ]
            ),
        )

        # cast to DecimalType
        df1 = df1.withColumn("col_1", F.col("grade").cast("decimal(4,3)"))
        df2 = df2.withColumn("col_1", F.col("grade").cast("decimal(4,3)"))

        assertDataFrameEqual(df1, df2, rtol=1e-1)

    def test_assert_notequal_arraytype(self):
        df1 = self.spark.createDataFrame(
            data=[
                ("John", ["Python", "Java"]),
                ("Jane", ["Scala", "SQL", "Java"]),
            ],
            schema=StructType(
                [
                    StructField("name", StringType(), True),
                    StructField("languages", ArrayType(StringType()), True),
                ]
            ),
        )
        df2 = self.spark.createDataFrame(
            data=[
                ("John", ["Python", "Java"]),
                ("Jane", ["Scala", "Java"]),
            ],
            schema=StructType(
                [
                    StructField("name", StringType(), True),
                    StructField("languages", ArrayType(StringType()), True),
                ]
            ),
        )

        expected_error_message = "Results do not match: "
        percent_diff = (1 / 2) * 100
        expected_error_message += "( %.5f %% )" % percent_diff
        diff_msg = (
            "[actual]"
            + "\n"
            + str(df1.collect()[1])
            + "\n\n"
            + "[expected]"
            + "\n"
            + str(df2.collect()[1])
            + "\n\n"
            + "********************"
            + "\n\n"
        )
        expected_error_message += "\n" + diff_msg

        with self.assertRaises(PySparkAssertionError) as pe:
            assertDataFrameEqual(df1, df2)

        self.check_error(
            exception=pe.exception,
            error_class="DIFFERENT_ROWS",
            message_parameters={"error_msg": expected_error_message},
        )

        with self.assertRaises(PySparkAssertionError) as pe:
            assertDataFrameEqual(df1, df2, checkRowOrder=True)

        self.check_error(
            exception=pe.exception,
            error_class="DIFFERENT_ROWS",
            message_parameters={"error_msg": expected_error_message},
        )

    def test_assert_equal_maptype(self):
        df1 = self.spark.createDataFrame(
            data=[
                ("student1", {"id": 222342203655477580}),
                ("student2", {"id": 422322203155477692}),
            ],
            schema=StructType(
                [
                    StructField("student", StringType(), True),
                    StructField("properties", MapType(StringType(), LongType()), True),
                ]
            ),
        )
        df2 = self.spark.createDataFrame(
            data=[
                ("student1", {"id": 222342203655477580}),
                ("student2", {"id": 422322203155477692}),
            ],
            schema=StructType(
                [
                    StructField("student", StringType(), True),
                    StructField("properties", MapType(StringType(), LongType()), True),
                ]
            ),
        )

        assertDataFrameEqual(df1, df2, checkRowOrder=False)
        assertDataFrameEqual(df1, df2, checkRowOrder=True)

    def test_assert_approx_equal_maptype_double(self):
        df1 = self.spark.createDataFrame(
            data=[
                ("student1", {"math": 76.23, "english": 92.64}),
                ("student2", {"math": 87.89, "english": 84.48}),
            ],
            schema=StructType(
                [
                    StructField("student", StringType(), True),
                    StructField("grades", MapType(StringType(), DoubleType()), True),
                ]
            ),
        )
        df2 = self.spark.createDataFrame(
            data=[
                ("student1", {"math": 76.23, "english": 92.63999999}),
                ("student2", {"math": 87.89, "english": 84.48}),
            ],
            schema=StructType(
                [
                    StructField("student", StringType(), True),
                    StructField("grades", MapType(StringType(), DoubleType()), True),
                ]
            ),
        )

        assertDataFrameEqual(df1, df2, checkRowOrder=False)
        assertDataFrameEqual(df1, df2, checkRowOrder=True)

    def test_assert_approx_equal_nested_struct_double(self):
        df1 = self.spark.createDataFrame(
            data=[
                ("jane", (64.57, 76.63, 97.81)),
                ("john", (93.92, 91.57, 84.36)),
            ],
            schema=StructType(
                [
                    StructField("name", StringType(), True),
                    StructField(
                        "grades",
                        StructType(
                            [
                                StructField("math", DoubleType(), True),
                                StructField("english", DoubleType(), True),
                                StructField("biology", DoubleType(), True),
                            ]
                        ),
                    ),
                ]
            ),
        )

        df2 = self.spark.createDataFrame(
            data=[
                ("jane", (64.57, 76.63, 97.81000001)),
                ("john", (93.92, 91.57, 84.36)),
            ],
            schema=StructType(
                [
                    StructField("name", StringType(), True),
                    StructField(
                        "grades",
                        StructType(
                            [
                                StructField("math", DoubleType(), True),
                                StructField("english", DoubleType(), True),
                                StructField("biology", DoubleType(), True),
                            ]
                        ),
                    ),
                ]
            ),
        )

        assertDataFrameEqual(df1, df2, checkRowOrder=False)
        assertDataFrameEqual(df1, df2, checkRowOrder=True)

    def test_assert_equal_nested_struct_str(self):
        df1 = self.spark.createDataFrame(
            data=[
                (1, ("jane", "anne", "doe")),
                (2, ("john", "bob", "smith")),
            ],
            schema=StructType(
                [
                    StructField("id", IntegerType(), True),
                    StructField(
                        "name",
                        StructType(
                            [
                                StructField("first", StringType(), True),
                                StructField("middle", StringType(), True),
                                StructField("last", StringType(), True),
                            ]
                        ),
                    ),
                ]
            ),
        )

        df2 = self.spark.createDataFrame(
            data=[
                (1, ("jane", "anne", "doe")),
                (2, ("john", "bob", "smith")),
            ],
            schema=StructType(
                [
                    StructField("id", IntegerType(), True),
                    StructField(
                        "name",
                        StructType(
                            [
                                StructField("first", StringType(), True),
                                StructField("middle", StringType(), True),
                                StructField("last", StringType(), True),
                            ]
                        ),
                    ),
                ]
            ),
        )

        assertDataFrameEqual(df1, df2, checkRowOrder=False)
        assertDataFrameEqual(df1, df2, checkRowOrder=True)

    def test_assert_equal_nested_struct_str_duplicate(self):
        df1 = self.spark.createDataFrame(
            data=[
                (1, ("jane doe", "jane doe")),
                (2, ("john smith", "john smith")),
            ],
            schema=StructType(
                [
                    StructField("id", IntegerType(), True),
                    StructField(
                        "full name",
                        StructType(
                            [
                                StructField("name", StringType(), True),
                                StructField("name", StringType(), True),
                            ]
                        ),
                    ),
                ]
            ),
        )

        df2 = self.spark.createDataFrame(
            data=[
                (1, ("jane doe", "jane doe")),
                (2, ("john smith", "john smith")),
            ],
            schema=StructType(
                [
                    StructField("id", IntegerType(), True),
                    StructField(
                        "full name",
                        StructType(
                            [
                                StructField("name", StringType(), True),
                                StructField("name", StringType(), True),
                            ]
                        ),
                    ),
                ]
            ),
        )

        assertDataFrameEqual(df1, df2, checkRowOrder=False)
        assertDataFrameEqual(df1, df2, checkRowOrder=True)

    def test_assert_equal_duplicate_col(self):
        df1 = self.spark.createDataFrame(
            data=[
                (1, "Python", 1, 1),
                (2, "Scala", 2, 2),
            ],
            schema=["number", "language", "number", "number"],
        )
        df2 = self.spark.createDataFrame(
            data=[
                (1, "Python", 1, 1),
                (2, "Scala", 2, 2),
            ],
            schema=["number", "language", "number", "number"],
        )

        assertDataFrameEqual(df1, df2, checkRowOrder=False)
        assertDataFrameEqual(df1, df2, checkRowOrder=True)

    def test_assert_equal_timestamp(self):
        df1 = self.spark.createDataFrame(
            data=[("1", "2023-01-01 12:01:01.000")], schema=["id", "timestamp"]
        )

        df2 = self.spark.createDataFrame(
            data=[("1", "2023-01-01 12:01:01.000")], schema=["id", "timestamp"]
        )

        df1 = df1.withColumn("timestamp", to_timestamp("timestamp"))
        df2 = df2.withColumn("timestamp", to_timestamp("timestamp"))

        assertDataFrameEqual(df1, df2, checkRowOrder=False)
        assertDataFrameEqual(df1, df2, checkRowOrder=True)

    def test_assert_equal_nullrow(self):
        df1 = self.spark.createDataFrame(
            data=[
                ("1", 1000),
                (None, None),
            ],
            schema=["id", "amount"],
        )
        df2 = self.spark.createDataFrame(
            data=[
                ("1", 1000),
                (None, None),
            ],
            schema=["id", "amount"],
        )

        assertDataFrameEqual(df1, df2, checkRowOrder=False)
        assertDataFrameEqual(df1, df2, checkRowOrder=True)

    def test_assert_notequal_nullval(self):
        df1 = self.spark.createDataFrame(
            data=[
                ("1", 1000),
                ("2", 2000),
            ],
            schema=["id", "amount"],
        )
        df2 = self.spark.createDataFrame(
            data=[
                ("1", 1000),
                ("2", None),
            ],
            schema=["id", "amount"],
        )

        expected_error_message = "Results do not match: "
        percent_diff = (1 / 2) * 100
        expected_error_message += "( %.5f %% )" % percent_diff
        diff_msg = (
            "[actual]"
            + "\n"
            + str(df1.collect()[1])
            + "\n\n"
            + "[expected]"
            + "\n"
            + str(df2.collect()[1])
            + "\n\n"
            + "********************"
            + "\n\n"
        )
        expected_error_message += "\n" + diff_msg

        with self.assertRaises(PySparkAssertionError) as pe:
            assertDataFrameEqual(df1, df2)

        self.check_error(
            exception=pe.exception,
            error_class="DIFFERENT_ROWS",
            message_parameters={"error_msg": expected_error_message},
        )

        with self.assertRaises(PySparkAssertionError) as pe:
            assertDataFrameEqual(df1, df2, checkRowOrder=True)

        self.check_error(
            exception=pe.exception,
            error_class="DIFFERENT_ROWS",
            message_parameters={"error_msg": expected_error_message},
        )

    def test_assert_equal_nulldf(self):
        df1 = None
        df2 = None

        assertDataFrameEqual(df1, df2, checkRowOrder=False)
        assertDataFrameEqual(df1, df2, checkRowOrder=True)

    def test_assert_error_pandas_df(self):
        import pandas as pd

        df1 = pd.DataFrame(data=[10, 20, 30], columns=["Numbers"])
        df2 = pd.DataFrame(data=[10, 20, 30], columns=["Numbers"])

        with self.assertRaises(PySparkAssertionError) as pe:
            assertDataFrameEqual(df1, df2)

        self.check_error(
            exception=pe.exception,
            error_class="UNSUPPORTED_DATA_TYPE",
            message_parameters={"data_type": pd.DataFrame},
        )

        with self.assertRaises(PySparkAssertionError) as pe:
            assertDataFrameEqual(df1, df2, checkRowOrder=True)

        self.check_error(
            exception=pe.exception,
            error_class="UNSUPPORTED_DATA_TYPE",
            message_parameters={"data_type": pd.DataFrame},
        )

    def test_assert_error_non_pyspark_df(self):
        dict1 = {"a": 1, "b": 2}
        dict2 = {"a": 1, "b": 2}

        with self.assertRaises(PySparkAssertionError) as pe:
            assertDataFrameEqual(dict1, dict2)

        self.check_error(
            exception=pe.exception,
            error_class="UNSUPPORTED_DATA_TYPE",
            message_parameters={"data_type": type(dict1)},
        )

        with self.assertRaises(PySparkAssertionError) as pe:
            assertDataFrameEqual(dict1, dict2, checkRowOrder=True)

        self.check_error(
            exception=pe.exception,
            error_class="UNSUPPORTED_DATA_TYPE",
            message_parameters={"data_type": type(dict1)},
        )

    def test_row_order_ignored(self):
        # test that row order is ignored (not checked) by default
        df1 = self.spark.createDataFrame(
            data=[
                ("2", 3000.00),
                ("1", 1000.00),
            ],
            schema=["id", "amount"],
        )
        df2 = self.spark.createDataFrame(
            data=[
                ("1", 1000.00),
                ("2", 3000.00),
            ],
            schema=["id", "amount"],
        )

        assertDataFrameEqual(df1, df2)

    def test_check_row_order_error(self):
        # test checkRowOrder=True
        df1 = self.spark.createDataFrame(
            data=[
                ("2", 3000.00),
                ("1", 1000.00),
            ],
            schema=["id", "amount"],
        )
        df2 = self.spark.createDataFrame(
            data=[
                ("1", 1000.00),
                ("2", 3000.00),
            ],
            schema=["id", "amount"],
        )

        expected_error_message = "Results do not match: "
        percent_diff = (2 / 2) * 100
        expected_error_message += "( %.5f %% )" % percent_diff
        diff_msg = (
            "[actual]"
            + "\n"
            + str(df1.collect()[0])
            + "\n\n"
            + "[expected]"
            + "\n"
            + str(df2.collect()[0])
            + "\n\n"
            + "********************"
            + "\n\n"
        )
        diff_msg += (
            "[actual]"
            + "\n"
            + str(df1.collect()[1])
            + "\n\n"
            + "[expected]"
            + "\n"
            + str(df2.collect()[1])
            + "\n\n"
            + "********************"
            + "\n\n"
        )
        expected_error_message += "\n" + diff_msg

        with self.assertRaises(PySparkAssertionError) as pe:
            assertDataFrameEqual(df1, df2, checkRowOrder=True)

        self.check_error(
            exception=pe.exception,
            error_class="DIFFERENT_ROWS",
            message_parameters={"error_msg": expected_error_message},
        )

    def test_remove_non_word_characters_long(self):
        def remove_non_word_characters(col):
            return F.regexp_replace(col, "[^\\w\\s]+", "")

        source_data = [("jo&&se",), ("**li**",), ("#::luisa",), (None,)]
        source_df = self.spark.createDataFrame(source_data, ["name"])

        actual_df = source_df.withColumn("clean_name", remove_non_word_characters(F.col("name")))

        expected_data = [("jo&&se", "jose"), ("**li**", "li"), ("#::luisa", "luisa"), (None, None)]
        expected_df = self.spark.createDataFrame(expected_data, ["name", "clean_name"])

        assertDataFrameEqual(actual_df, expected_df)

    def test_assert_pyspark_approx_equal(self):
        df1 = self.spark.createDataFrame(
            data=[
                ("1", 1000.00),
                ("2", 3000.00),
            ],
            schema=["id", "amount"],
        )
        df2 = self.spark.createDataFrame(
            data=[
                ("1", 1000.0000001),
                ("2", 3000.00),
            ],
            schema=["id", "amount"],
        )

        assertDataFrameEqual(df1, df2, checkRowOrder=False)
        assertDataFrameEqual(df1, df2, checkRowOrder=True)

    def test_assert_pyspark_approx_equal_custom_rtol(self):
        df1 = self.spark.createDataFrame(
            data=[
                ("1", 1000.00),
                ("2", 3000.00),
            ],
            schema=["id", "amount"],
        )
        df2 = self.spark.createDataFrame(
            data=[
                ("1", 1000.01),
                ("2", 3000.00),
            ],
            schema=["id", "amount"],
        )

        assertDataFrameEqual(df1, df2, rtol=1e-2)

    def test_assert_pyspark_df_not_equal(self):
        df1 = self.spark.createDataFrame(
            data=[
                ("1", 1000.00),
                ("2", 3000.00),
                ("3", 2000.00),
            ],
            schema=["id", "amount"],
        )
        df2 = self.spark.createDataFrame(
            data=[
                ("1", 1001.00),
                ("2", 3000.00),
                ("3", 2003.00),
            ],
            schema=["id", "amount"],
        )

        expected_error_message = "Results do not match: "
        percent_diff = (2 / 3) * 100
        expected_error_message += "( %.5f %% )" % percent_diff
        diff_msg = (
            "[actual]"
            + "\n"
            + str(df1.collect()[0])
            + "\n\n"
            + "[expected]"
            + "\n"
            + str(df2.collect()[0])
            + "\n\n"
            + "********************"
            + "\n\n"
        )
        diff_msg += (
            "[actual]"
            + "\n"
            + str(df1.collect()[2])
            + "\n\n"
            + "[expected]"
            + "\n"
            + str(df2.collect()[2])
            + "\n\n"
            + "********************"
            + "\n\n"
        )
        expected_error_message += "\n" + diff_msg

        with self.assertRaises(PySparkAssertionError) as pe:
            assertDataFrameEqual(df1, df2)

        self.check_error(
            exception=pe.exception,
            error_class="DIFFERENT_ROWS",
            message_parameters={"error_msg": expected_error_message},
        )

        with self.assertRaises(PySparkAssertionError) as pe:
            assertDataFrameEqual(df1, df2, checkRowOrder=True)

        self.check_error(
            exception=pe.exception,
            error_class="DIFFERENT_ROWS",
            message_parameters={"error_msg": expected_error_message},
        )

    def test_assert_notequal_schema(self):
        df1 = self.spark.createDataFrame(
            data=[
                (1, 1000),
                (2, 3000),
            ],
            schema=["id", "number"],
        )
        df2 = self.spark.createDataFrame(
            data=[
                ("1", 1000),
                ("2", 5000),
            ],
            schema=["id", "amount"],
        )

        generated_diff = difflib.ndiff(str(df1.schema).splitlines(), str(df2.schema).splitlines())

        expected_error_msg = "\n".join(generated_diff)

        with self.assertRaises(PySparkAssertionError) as pe:
            assertDataFrameEqual(df1, df2)

        self.check_error(
            exception=pe.exception,
            error_class="DIFFERENT_SCHEMA",
            message_parameters={"error_msg": expected_error_msg},
        )

    def test_diff_schema_lens(self):
        df1 = self.spark.createDataFrame(
            data=[
                (1, 3000),
                (2, 1000),
            ],
            schema=["id", "amount"],
        )

        df2 = self.spark.createDataFrame(
            data=[
                (1, 3000, "a"),
                (2, 1000, "b"),
            ],
            schema=["id", "amount", "letter"],
        )

        generated_diff = difflib.ndiff(str(df1.schema).splitlines(), str(df2.schema).splitlines())

        expected_error_msg = "\n".join(generated_diff)

        with self.assertRaises(PySparkAssertionError) as pe:
            assertDataFrameEqual(df1, df2)

        self.check_error(
            exception=pe.exception,
            error_class="DIFFERENT_SCHEMA",
            message_parameters={"error_msg": expected_error_msg},
        )

    def test_schema_ignore_nullable(self):
        s1 = StructType(
            [StructField("id", IntegerType(), True), StructField("name", StringType(), True)]
        )

        df1 = self.spark.createDataFrame([(1, "jane"), (2, "john")], s1)

        s2 = StructType(
            [StructField("id", IntegerType(), True), StructField("name", StringType(), False)]
        )

        df2 = self.spark.createDataFrame([(1, "jane"), (2, "john")], s2)

        assertDataFrameEqual(df1, df2)

    def test_schema_ignore_nullable_array_equal(self):
        s1 = StructType([StructField("names", ArrayType(DoubleType(), True), True)])
        s2 = StructType([StructField("names", ArrayType(DoubleType(), False), False)])

        assertSchemaEqual(s1, s2)

    def test_schema_ignore_nullable_struct_equal(self):
        s1 = StructType(
            [StructField("names", StructType([StructField("age", IntegerType(), True)]), True)]
        )
        s2 = StructType(
            [StructField("names", StructType([StructField("age", IntegerType(), False)]), False)]
        )
        assertSchemaEqual(s1, s2)

    def test_schema_array_unequal(self):
        s1 = StructType([StructField("names", ArrayType(IntegerType(), True), True)])
        s2 = StructType([StructField("names", ArrayType(DoubleType(), False), False)])

        generated_diff = difflib.ndiff(str(s1).splitlines(), str(s2).splitlines())

        expected_error_msg = "\n".join(generated_diff)

        with self.assertRaises(PySparkAssertionError) as pe:
            assertSchemaEqual(s1, s2)

        self.check_error(
            exception=pe.exception,
            error_class="DIFFERENT_SCHEMA",
            message_parameters={"error_msg": expected_error_msg},
        )

    def test_schema_struct_unequal(self):
        s1 = StructType(
            [StructField("names", StructType([StructField("age", DoubleType(), True)]), True)]
        )
        s2 = StructType(
            [StructField("names", StructType([StructField("age", IntegerType(), True)]), True)]
        )

        generated_diff = difflib.ndiff(str(s1).splitlines(), str(s2).splitlines())

        expected_error_msg = "\n".join(generated_diff)

        with self.assertRaises(PySparkAssertionError) as pe:
            assertSchemaEqual(s1, s2)

        self.check_error(
            exception=pe.exception,
            error_class="DIFFERENT_SCHEMA",
            message_parameters={"error_msg": expected_error_msg},
        )

    def test_schema_more_nested_struct_unequal(self):
        s1 = StructType(
            [
                StructField(
                    "name",
                    StructType(
                        [
                            StructField("firstname", StringType(), True),
                            StructField("middlename", StringType(), True),
                            StructField("lastname", StringType(), True),
                        ]
                    ),
                ),
            ]
        )

        s2 = StructType(
            [
                StructField(
                    "name",
                    StructType(
                        [
                            StructField("firstname", StringType(), True),
                            StructField("middlename", BooleanType(), True),
                            StructField("lastname", StringType(), True),
                        ]
                    ),
                ),
            ]
        )

        generated_diff = difflib.ndiff(str(s1).splitlines(), str(s2).splitlines())

        expected_error_msg = "\n".join(generated_diff)

        with self.assertRaises(PySparkAssertionError) as pe:
            assertSchemaEqual(s1, s2)

        self.check_error(
            exception=pe.exception,
            error_class="DIFFERENT_SCHEMA",
            message_parameters={"error_msg": expected_error_msg},
        )

    def test_schema_unsupported_type(self):
        s1 = "names: int"
        s2 = "names: int"

        with self.assertRaises(PySparkAssertionError) as pe:
            assertSchemaEqual(s1, s2)

        self.check_error(
            exception=pe.exception,
            error_class="UNSUPPORTED_DATA_TYPE",
            message_parameters={"data_type": type(s1)},
        )

    def test_spark_sql(self):
        assertDataFrameEqual(self.spark.sql("select 1 + 2 AS x"), self.spark.sql("select 3 AS x"))
        assertDataFrameEqual(
            self.spark.sql("select 1 + 2 AS x"),
            self.spark.sql("select 3 AS x"),
            checkRowOrder=True,
        )

    def test_spark_sql_sort_rows(self):
        df1 = self.spark.createDataFrame(
            data=[
                (1, 3000),
                (2, 1000),
            ],
            schema=["id", "amount"],
        )

        df2 = self.spark.createDataFrame(
            data=[
                (2, 1000),
                (1, 3000),
            ],
            schema=["id", "amount"],
        )

        df1.createOrReplaceTempView("df1")
        df2.createOrReplaceTempView("df2")

        assertDataFrameEqual(
            self.spark.sql("select * from df1 order by amount"), self.spark.sql("select * from df2")
        )

        assertDataFrameEqual(
            self.spark.sql("select * from df1 order by amount"),
            self.spark.sql("select * from df2"),
            checkRowOrder=True,
        )

    def test_empty_dataset(self):
        df1 = self.spark.range(0, 10).limit(0)

        df2 = self.spark.range(0, 10).limit(0)

        assertDataFrameEqual(df1, df2, checkRowOrder=False)
        assertDataFrameEqual(df1, df2, checkRowOrder=True)

    def test_no_column(self):
        df1 = self.spark.range(0, 10).drop("id")

        df2 = self.spark.range(0, 10).drop("id")

        assertDataFrameEqual(df1, df2, checkRowOrder=False)
        assertDataFrameEqual(df1, df2, checkRowOrder=True)

    def test_empty_no_column(self):
        df1 = self.spark.range(0, 10).drop("id").limit(0)

        df2 = self.spark.range(0, 10).drop("id").limit(0)

        assertDataFrameEqual(df1, df2, checkRowOrder=False)
        assertDataFrameEqual(df1, df2, checkRowOrder=True)

    def test_special_vals(self):
        df1 = self.spark.createDataFrame(
            data=[
                (1, float("nan")),
                (2, float("inf")),
                (2, float("-inf")),
            ],
            schema=["id", "amount"],
        )

        df2 = self.spark.createDataFrame(
            data=[
                (1, float("nan")),
                (2, float("inf")),
                (2, float("-inf")),
            ],
            schema=["id", "amount"],
        )

        assertDataFrameEqual(df1, df2, checkRowOrder=False)
        assertDataFrameEqual(df1, df2, checkRowOrder=True)

    def test_list_row_equal(self):
        from pyspark.sql import Row

        df1 = self.spark.createDataFrame(
            data=[
                (1, 3000),
                (2, 1000),
            ],
            schema=["id", "amount"],
        )

        list_of_rows = [Row(1, 3000), Row(2, 1000)]

        assertDataFrameEqual(df1, list_of_rows, checkRowOrder=False)
        assertDataFrameEqual(df1, list_of_rows, checkRowOrder=True)

    def test_list_row_unequal_schema(self):
        from pyspark.sql import Row

        df1 = self.spark.createDataFrame(
            data=[
                (1, 3000),
                (2, 1000),
            ],
            schema=["id", "amount"],
        )

        list_of_rows = [Row(1, "3000"), Row(2, "1000")]

        expected_error_message = "Results do not match: "
        percent_diff = (2 / 2) * 100
        expected_error_message += "( %.5f %% )" % percent_diff
        diff_msg = (
            "[actual]"
            + "\n"
            + str(df1.collect()[0])
            + "\n\n"
            + "[expected]"
            + "\n"
            + str(list_of_rows[0])
            + "\n\n"
            + "********************"
            + "\n\n"
        )
        diff_msg += (
            "[actual]"
            + "\n"
            + str(df1.collect()[1])
            + "\n\n"
            + "[expected]"
            + "\n"
            + str(list_of_rows[1])
            + "\n\n"
            + "********************"
            + "\n\n"
        )
        expected_error_message += "\n" + diff_msg

        with self.assertRaises(PySparkAssertionError) as pe:
            assertDataFrameEqual(df1, list_of_rows)

        self.check_error(
            exception=pe.exception,
            error_class="DIFFERENT_ROWS",
            message_parameters={"error_msg": expected_error_message},
        )

        with self.assertRaises(PySparkAssertionError) as pe:
            assertDataFrameEqual(df1, list_of_rows, checkRowOrder=True)

        self.check_error(
            exception=pe.exception,
            error_class="DIFFERENT_ROWS",
            message_parameters={"error_msg": expected_error_message},
        )


class UtilsTests(ReusedSQLTestCase, UtilsTestsMixin):
    def test_capture_analysis_exception(self):
        self.assertRaises(AnalysisException, lambda: self.spark.sql("select abc"))
        self.assertRaises(AnalysisException, lambda: self.df.selectExpr("a + b"))

    def test_capture_user_friendly_exception(self):
        try:
            self.spark.sql("select `中文字段`")
        except AnalysisException as e:
            self.assertRegex(str(e), ".*UNRESOLVED_COLUMN.*`中文字段`.*")

    def test_spark_upgrade_exception(self):
        # SPARK-32161 : Test case to Handle SparkUpgradeException in pythonic way
        df = self.spark.createDataFrame([("2014-31-12",)], ["date_str"])
        df2 = df.select(
            "date_str", to_date(from_unixtime(unix_timestamp("date_str", "yyyy-dd-aa")))
        )
        self.assertRaises(SparkUpgradeException, df2.collect)

    def test_capture_parse_exception(self):
        self.assertRaises(ParseException, lambda: self.spark.sql("abc"))

    def test_capture_illegalargument_exception(self):
        self.assertRaisesRegex(
            IllegalArgumentException,
            "Setting negative mapred.reduce.tasks",
            lambda: self.spark.sql("SET mapred.reduce.tasks=-1"),
        )
        df = self.spark.createDataFrame([(1, 2)], ["a", "b"])
        self.assertRaisesRegex(
            IllegalArgumentException,
            "1024 is not in the permitted values",
            lambda: df.select(sha2(df.a, 1024)).collect(),
        )
        try:
            df.select(sha2(df.a, 1024)).collect()
        except IllegalArgumentException as e:
            self.assertRegex(e.desc, "1024 is not in the permitted values")
            self.assertRegex(e.stackTrace, "org.apache.spark.sql.functions")

    def test_get_error_class_state(self):
        # SPARK-36953: test CapturedException.getErrorClass and getSqlState (from SparkThrowable)
        try:
            self.spark.sql("""SELECT a""")
        except AnalysisException as e:
            self.assertEquals(e.getErrorClass(), "UNRESOLVED_COLUMN.WITHOUT_SUGGESTION")
            self.assertEquals(e.getSqlState(), "42703")


if __name__ == "__main__":
    import unittest
    from pyspark.sql.tests.test_utils import *  # noqa: F401

    try:
        import xmlrunner

        testRunner = xmlrunner.XMLTestRunner(output="target/test-reports", verbosity=2)
    except ImportError:
        testRunner = None
    unittest.main(testRunner=testRunner, verbosity=2)

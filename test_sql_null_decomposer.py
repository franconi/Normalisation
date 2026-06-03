import unittest

from sql_null_decomposer import (
    SQLNullDependency,
    SQLNullSchema,
    analyze_schema,
    fs,
    schema_from_text,
    sql_null_decomposition,
)


def dep(kind, lhs, rhs):
    return SQLNullDependency(kind, lhs, rhs)


def schema(attrs, nullable, dependencies=()):
    return SQLNullSchema(fs(attrs), fs(nullable), tuple(dependencies))


def rels(relations):
    return {"".join(sorted(relation)) for relation in relations}


class SQLNullDecomposerTests(unittest.TestCase):
    def test_provisional_is_unchanged_without_dependencies(self):
        final, removed = sql_null_decomposition(schema("ABCD", "BC"))
        self.assertEqual({"AD", "ABD", "ACD", "ABCD"}, rels(final))
        self.assertEqual({}, removed)

    def test_jointly_sql_null_removes_exclusive_relations(self):
        final, removed = sql_null_decomposition(
            schema(
                "ABCD",
                "BC",
                [dep("jointly_sql_null", "B", "C")],
            )
        )
        self.assertEqual({"AD", "ABCD"}, rels(final))
        self.assertEqual({"ABD", "ACD"}, set(removed))

    def test_implies_sql_null_removes_rhs_without_lhs(self):
        final, removed = sql_null_decomposition(
            schema(
                "ABCD",
                "BC",
                [dep("implies_sql_null", "B", "C")],
            )
        )
        self.assertEqual({"AD", "ABD", "ABCD"}, rels(final))
        self.assertEqual({"ACD"}, set(removed))

    def test_alternative_sql_null_removes_both_and_neither(self):
        final, removed = sql_null_decomposition(
            schema(
                "ABCD",
                "BC",
                [dep("alternative_sql_null", "B", "C")],
            )
        )
        self.assertEqual({"ABD", "ACD"}, rels(final))
        self.assertEqual({"AD", "ABCD"}, set(removed))

    def test_combined_dependencies(self):
        final, removed = sql_null_decomposition(
            schema(
                "ABCD",
                "BCD",
                [
                    dep("implies_sql_null", "B", "C"),
                    dep("jointly_sql_null", "C", "D"),
                ],
            )
        )
        self.assertEqual({"A", "AB", "ABCD"}, rels(final))
        self.assertEqual({"AC", "AD", "ABC", "ABD", "ACD"}, set(removed))

    def test_text_parser(self):
        parsed = schema_from_text(
            """
            relation Orders: A B C E
            nullable: B C
            B -N-> C
            B <-N-> C
            B ->N<- C
            """
        )
        self.assertEqual("Orders", parsed.relation_name)
        self.assertEqual(fs("ABCE"), parsed.attributes)
        self.assertEqual(fs("BC"), parsed.nullable)
        self.assertEqual(
            (
                dep("implies_sql_null", "B", "C"),
                dep("jointly_sql_null", "B", "C"),
                dep("alternative_sql_null", "B", "C"),
            ),
            parsed.dependencies,
        )

    def test_text_parser_supports_multi_character_attributes(self):
        parsed = schema_from_text(
            """
            attributes: Customer Order Invoice
            nullable: Order Invoice
            Order -N-> Invoice
            """
        )
        self.assertEqual({"Customer", "Order", "Invoice"}, set(parsed.attributes))
        self.assertEqual({"Order", "Invoice"}, set(parsed.nullable))
        self.assertEqual(dep("implies_sql_null", "Order", "Invoice"), parsed.dependencies[0])

    def test_unknown_dependency_attribute_is_invalid(self):
        with self.assertRaisesRegex(ValueError, "unknown attribute"):
            schema_from_text(
                """
                attributes: A B C
                nullable: B
                B -N-> D
                """
            )

    def test_sql_null_dependency_attributes_must_be_nullable(self):
        with self.assertRaisesRegex(ValueError, "non-nullable attributes"):
            schema_from_text(
                """
                attributes: A B C
                nullable: B
                B -N-> C
                """
            )

    def test_unknown_nullable_attribute_is_invalid(self):
        with self.assertRaisesRegex(ValueError, "unknown nullable attributes"):
            schema_from_text(
                """
                attributes: A B C
                nullable: D
                B -N-> C
                """
            )

    def test_analysis_payload_contains_removed_reasons(self):
        output = analyze_schema(
            schema(
                "ABC",
                "BC",
                [dep("implies_sql_null", "B", "C")],
            )
        )
        self.assertEqual([["A"], ["A", "B"], ["A", "B", "C"]], output["sql_null_decomposition"])
        named = output["named_sql_null_decomposition"]
        self.assertEqual(["R#1", "R#2", "R#3"], [item["name"] for item in named])
        self.assertEqual(
            [["A#1"], ["A#2", "B#2"], ["A#3", "B#3", "C#3"]],
            [item["attributes"] for item in named],
        )
        self.assertEqual(
            [["A"], ["A", "B"], ["A", "B", "C"]],
            [item["original_attributes"] for item in named],
        )
        self.assertEqual(
            [[], ["B#2"], ["B#3", "C#3"]],
            [item["renamed_nullable_subset"] for item in named],
        )
        self.assertEqual([[], ["B"], ["B", "C"]], output["restricted_nullable_powerset"])
        self.assertIn("C", output["removed_nullable_sets"])
        self.assertIn("AC", output["removed_relations"])

    def test_no_nullable_attributes_keeps_only_original_relation(self):
        output = analyze_schema(
            SQLNullSchema(
                fs("ABC"),
                frozenset(),
                (),
                "Orders",
            )
        )

        self.assertEqual([["A", "B", "C"]], output["sql_null_decomposition"])
        self.assertEqual(
            [
                {
                    "name": "Orders",
                    "attributes": ["A", "B", "C"],
                    "original_attributes": ["A", "B", "C"],
                    "nullable_subset": [],
                    "renamed_nullable_subset": [],
                }
            ],
            output["named_sql_null_decomposition"],
        )
        self.assertEqual(
            [["A", "B", "C"]],
            output["renamed_sql_null_decomposition"],
        )

    def test_named_relation_prefix_is_used_for_sql_null_decomposition(self):
        output = analyze_schema(
            SQLNullSchema(
                fs("ABC"),
                fs("BC"),
                (dep("implies_sql_null", "B", "C"),),
                "Orders",
            )
        )
        self.assertEqual(
            ["Orders#1", "Orders#2", "Orders#3"],
            [item["name"] for item in output["named_sql_null_decomposition"]],
        )
        self.assertEqual(
            [["A#1"], ["A#2", "B#2"], ["A#3", "B#3", "C#3"]],
            [
                item["attributes"]
                for item in output["named_sql_null_decomposition"]
            ],
        )


if __name__ == "__main__":
    unittest.main()

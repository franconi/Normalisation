import unittest

from combined_null_4nf_decomposer import analyze_combined_schema, schema_from_text
from six_nf import build_six_nf


class SixNFTests(unittest.TestCase):
    def test_six_nf_dependencies_match_target_display(self):
        analysis = analyze_combined_schema(
            schema_from_text(
                """
                relation R: A B C
                A -> B
                A -> C
                """
            )
        )

        six_nf = build_six_nf(analysis)

        self.assertEqual("6NF", six_nf["name"])
        self.assertEqual(
            [
                {
                    "name": "A_B",
                    "attributes": ["A", "B"],
                    "dependencies": ["A -> att(A_B)"],
                },
                {
                    "name": "A_C",
                    "attributes": ["A", "C"],
                    "dependencies": ["A -> att(A_C)"],
                },
            ],
            six_nf["relations"],
        )
        self.assertEqual([], six_nf["cross_relation_inclusion_dependencies"])

    def test_six_nf_contains_generated_numbered_suffix_dependencies(self):
        analysis = {
            "database_schemas": [
                {
                    "relations": [
                        {
                            "name": "R",
                            "attributes": ["A#1", "B#1", "A#2", "B#2"],
                            "nullable": [],
                        }
                    ]
                }
            ],
            "per_input_relation": [
                {
                    "input_relation": "R",
                    "attributes": ["A#1", "B#1", "A#2", "B#2"],
                    "nullable": [],
                    "per_relation_4nf": [
                        {
                            "sql_null_relation_name": "R1",
                            "sql_null_relation": ["A#1", "B#1"],
                            "renamed_sql_null_relation": ["A#1", "B#1"],
                            "applicable_fds": ["A#1 -> B#1", "A#1 -> B#1"],
                            "applicable_mvds": [],
                            "four_nf_decomposition": [["A#1", "B#1"]],
                        },
                        {
                            "sql_null_relation_name": "R2",
                            "sql_null_relation": ["A#2", "B#2"],
                            "renamed_sql_null_relation": ["A#2", "B#2"],
                            "applicable_fds": ["A#2 -> B#2"],
                            "applicable_mvds": [],
                            "four_nf_decomposition": [["A#2", "B#2"]],
                        },
                    ],
                }
            ],
            "final_decomposition": [["A#1", "B#1"], ["A#2", "B#2"]],
            "inclusion_dependencies": [],
        }

        six_nf = build_six_nf(analysis)

        self.assertEqual(
            ["A_k", "A#1_B#1", "A#2_B#2"],
            [relation["name"] for relation in six_nf["relations"]],
        )
        self.assertEqual(
            [
                "A#1, A#2 x=> A",
                "A#1, A#2 o=> A",
            ],
            six_nf["cross_relation_inclusion_dependencies"],
        )
        self.assertEqual(
            ["A#1 -> att(A#1_B#1)"],
            six_nf["relations"][1]["dependencies"],
        )

    def test_six_nf_carries_source_inclusion_split_across_target_relations(self):
        analysis = analyze_combined_schema(
            schema_from_text(
                """
                relation R: A B C
                A -> B
                A -> C
                B => C
                """
            )
        )

        six_nf = build_six_nf(analysis)

        self.assertEqual(
            ["B => C"],
            six_nf["cross_relation_inclusion_dependencies"],
        )

    def test_six_nf_keeps_source_inclusion_inside_target_relation_when_possible(self):
        analysis = analyze_combined_schema(
            schema_from_text(
                """
                relation R: A B C
                B => C
                """
            )
        )

        six_nf = build_six_nf(analysis)

        self.assertEqual([], six_nf["cross_relation_inclusion_dependencies"])
        self.assertEqual(["B => C"], six_nf["relations"][0]["dependencies"])


if __name__ == "__main__":
    unittest.main()

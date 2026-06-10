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

    def test_six_nf_adds_all_attributes_key_when_relation_has_no_key_constraint(self):
        analysis = analyze_combined_schema(
            schema_from_text(
                """
                relation R: A B C
                """
            )
        )

        six_nf = build_six_nf(analysis)

        self.assertEqual(
            [
                {
                    "name": "A_B_C",
                    "attributes": ["A", "B", "C"],
                    "dependencies": ["ABC -> att(A_B_C)"],
                },
            ],
            six_nf["relations"],
        )

    def test_six_nf_does_not_turn_trivial_mvd_into_key_constraint(self):
        analysis = analyze_combined_schema(
            schema_from_text(
                """
                relation R: a c
                a ->> c
                """
            )
        )

        six_nf = build_six_nf(analysis)

        self.assertEqual(
            [
                {
                    "name": "a_c",
                    "attributes": ["a", "c"],
                    "dependencies": ["ac -> att(a_c)"],
                },
            ],
            six_nf["relations"],
        )

    def test_six_nf_does_not_turn_nontrivial_mvd_into_key_constraint(self):
        analysis = analyze_combined_schema(
            schema_from_text(
                """
                relation R: a b c
                a ->> c
                """
            )
        )

        six_nf = build_six_nf(analysis)

        self.assertEqual(
            [
                {
                    "name": "a_b",
                    "attributes": ["a", "b"],
                    "dependencies": ["ab -> att(a_b)"],
                },
                {
                    "name": "a_c",
                    "attributes": ["a", "c"],
                    "dependencies": ["ac -> att(a_c)"],
                },
            ],
            six_nf["relations"],
        )

    def test_six_nf_does_not_use_mvd_as_key_after_fd_split(self):
        analysis = analyze_combined_schema(
            schema_from_text(
                """
                relation R: a b c
                a -> b
                a ->> c
                """
            )
        )

        six_nf = build_six_nf(analysis)

        self.assertEqual(
            [
                {
                    "name": "a_b",
                    "attributes": ["a", "b"],
                    "dependencies": ["a -> att(a_b)"],
                },
                {
                    "name": "a_c",
                    "attributes": ["a", "c"],
                    "dependencies": ["ac -> att(a_c)"],
                },
            ],
            six_nf["relations"],
        )

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
        self.assertEqual(
            ["B => C", "ABC -> att(A_B_C)"],
            six_nf["relations"][0]["dependencies"],
        )


if __name__ == "__main__":
    unittest.main()

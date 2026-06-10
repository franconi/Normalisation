import unittest

from fd_mvd_normalizer import Analyzer, FD, MVD, Schema, fs, schema_from_text


def fd(lhs: str, rhs: str) -> FD:
    return FD(fs(lhs), fs(rhs))


def mvd(lhs: str, rhs: str) -> MVD:
    return MVD(fs(lhs), fs(rhs))


def schema(attrs: str, fds=(), mvds=()) -> Schema:
    return Schema(fs(attrs), tuple(fds), tuple(mvds))


def rels(decomposition):
    return {"".join(sorted(relation)) for relation in decomposition}


class ExtendedConflictFreeTests(unittest.TestCase):
    def assert_good_schema(self, s: Schema, expected_rels=None):
        analyzer = Analyzer(s, max_rows=8192)
        ok, errors = analyzer.extended_conflict_free()
        self.assertTrue(ok, errors)

        decomposition, _ = analyzer.synthesize_decomposition(max_relations=8)

        if expected_rels is not None:
            self.assertEqual(set(expected_rels), rels(decomposition))

        self.assertTrue(analyzer.acyclic_decomposition(decomposition))
        self.assertTrue(analyzer.lossless(decomposition))
        self.assertTrue(analyzer.dependency_preserving(decomposition))

        for relation in decomposition:
            is_4nf, reason = analyzer.is_4nf_relation(relation)
            self.assertTrue(is_4nf, reason)

    def assert_bad_schema(self, s: Schema, expected_fragment: str):
        analyzer = Analyzer(s, max_rows=8192)
        ok, errors = analyzer.extended_conflict_free()
        self.assertFalse(ok)
        self.assertIn(expected_fragment, "\n".join(errors))

    def test_simple_fd_positive(self):
        self.assert_good_schema(
            schema("ABCD", fds=[fd("AB", "C")]),
            expected_rels={"ABC", "ABD"},
        )

    def test_good_fd_key_cycle_positive(self):
        self.assert_good_schema(
            schema("AB", fds=[fd("A", "B"), fd("B", "A")]),
            expected_rels={"AB"},
        )

    def test_independent_mvd_positive(self):
        self.assert_good_schema(
            schema("ABCDE", mvds=[mvd("A", "B"), mvd("A", "C")]),
            expected_rels={"AB", "AC", "ADE"},
        )

    def test_redundant_fd_lhs_does_not_create_mvd_split(self):
        self.assert_good_schema(
            Schema(
                fs(["Project_ID", "Project_Name", "Budget", "Consultant", "Tool"]),
                (
                    FD(fs(["Project_ID", "Consultant", "Tool"]), fs(["Budget"])),
                    FD(fs(["Project_ID", "Consultant", "Tool"]), fs(["Project_Name"])),
                    FD(fs(["Project_ID"]), fs(["Budget"])),
                    FD(fs(["Project_ID"]), fs(["Project_Name"])),
                ),
                (
                    MVD(fs(["Project_ID"]), fs(["Consultant"])),
                    MVD(fs(["Project_ID"]), fs(["Tool"])),
                ),
            )
        )

    def test_yuan_ozsoyoglu_mixed_example_positive(self):
        self.assert_good_schema(
            schema(
                "ABCEFG",
                fds=[
                    fd("A", "CG"),
                    fd("B", "A"),
                    fd("E", "GF"),
                    fd("GF", "E"),
                ],
                mvds=[
                    mvd("A", "B"),
                    mvd("CG", "ABC"),
                ],
            ),
            expected_rels={"AB", "ACG", "CFG", "EFG"},
        )

    def test_bad_fd_cycle_negative(self):
        self.assert_bad_schema(
            schema("ABC", fds=[fd("AB", "C"), fd("C", "B")]),
            "splits AB",
        )

    def test_cross_fd_f_intersection_negative(self):
        self.assert_bad_schema(
            schema("ABC", fds=[fd("A", "C"), fd("B", "C")]),
            "F-intersection fails",
        )

    def test_overlapping_fd_determinants_negative(self):
        self.assert_bad_schema(
            schema("ABCD", fds=[fd("AB", "D"), fd("AC", "D")]),
            "F-intersection fails",
        )

    def test_mvd_split_and_intersection_negative(self):
        self.assert_bad_schema(
            schema(
                "ABCD",
                mvds=[
                    mvd("A", "B"),
                    mvd("A", "C"),
                    mvd("BC", "D"),
                ],
            ),
            "M-splits BC",
        )

    def test_text_parser_accepts_fd_and_mvd_lines(self):
        parsed = schema_from_text(
            """
            attributes: A B C D E
            AB -> C
            A ->> D
            # comments are ignored
            """
        )
        self.assertEqual(fs("ABCDE"), parsed.attrs)
        self.assertEqual((fd("AB", "C"),), parsed.fds)
        self.assertEqual((mvd("A", "D"),), parsed.mvds)

    def test_text_parser_accepts_comma_separated_names(self):
        parsed = schema_from_text(
            """
            attrs: Customer, Order, Product
            Customer -> Order
            Customer ->> Product
            """
        )
        self.assertEqual(
            {"Customer", "Order", "Product"},
            set(parsed.attrs),
        )
        self.assertEqual(
            FD(fs(["Customer"]), fs(["Order"])),
            parsed.fds[0],
        )
        self.assertEqual(
            MVD(fs(["Customer"]), fs(["Product"])),
            parsed.mvds[0],
        )

    def test_text_parser_rejects_unknown_dependency_attributes(self):
        with self.assertRaisesRegex(ValueError, "unknown attributes"):
            schema_from_text(
                """
                attributes: A B C
                C -> D
                """
            )

    def test_text_parser_requires_declared_attributes(self):
        with self.assertRaisesRegex(ValueError, "attributes line"):
            schema_from_text("A -> B")


if __name__ == "__main__":
    unittest.main()

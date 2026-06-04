import unittest

from combined_null_4nf_decomposer import analyze_combined_schema, schema_from_text


def rel_name(relation):
    if any(len(attr) > 1 for attr in relation):
        return ",".join(sorted(relation))
    return "".join(sorted(relation))


def rels(relations):
    return {rel_name(relation) for relation in relations}


class CombinedNull4NFDecomposerTests(unittest.TestCase):
    def test_parser_accepts_sql_null_fds_and_mvds(self):
        parsed = schema_from_text(
            """
            attributes: A B C D
            nullable: B C
            B -N-> C
            B <-N-> C
            B ->N<- C
            AB -> D
            A ->> C
            """
        )

        self.assertEqual({"A", "B", "C", "D"}, set(parsed.attributes))
        self.assertEqual({"B", "C"}, set(parsed.nullable))
        self.assertEqual(3, len(parsed.sql_null_dependencies))
        self.assertEqual(1, len(parsed.fds))
        self.assertEqual(1, len(parsed.mvds))

    def test_cnf_starts_as_copy_of_six_nf(self):
        output = analyze_combined_schema(
            schema_from_text(
                """
                relation R: A B C
                A -> B
                A -> C
                """
            )
        )

        self.assertEqual("CNF", output["CNF"]["name"])
        self.assertEqual(output["6NF"]["relations"], output["CNF"]["relations"])
        self.assertEqual(
            output["6NF"]["cross_relation_inclusion_dependencies"],
            output["CNF"]["cross_relation_inclusion_dependencies"],
        )

    def test_non_extended_conflict_free_schema_stops_before_normalising(self):
        output = analyze_combined_schema(
            schema_from_text(
                """
                relation R: A B C
                AB -> C
                C -> B
                """
            )
        )

        self.assertFalse(output["extended_conflict_free"])
        self.assertEqual(
            "Source database schema is not extended conflict-free",
            output["message"],
        )
        self.assertIn("extended_conflict_free_failures", output)
        self.assertNotIn("per_input_relation", output)
        self.assertNotIn("6NF", output)
        self.assertNotIn("CNF", output)

    def test_sql_null_decomposition_is_computed_before_4nf(self):
        output = analyze_combined_schema(
            schema_from_text(
                """
                attributes: A B C E
                nullable: B C
                B -N-> C
                B -> C
                """
            )
        )

        self.assertEqual(
            {"AE", "ABE", "ABCE"},
            rels(output["sql_null_stage"]["sql_null_decomposition"]),
        )
        self.assertEqual(
            {"A#1,E#1", "A#2,B#2,E#2", "B#3,C#3", "A#3,B#3,E#3"},
            rels(output["final_decomposition"]),
        )
        self.assertEqual(
            {"AE", "ABE", "BC"},
            rels(output["original_final_decomposition"]),
        )

        abce_entry = next(
            item
            for item in output["per_relation_4nf"]
            if item["sql_null_relation_name"] == "R#3"
        )
        self.assertEqual(
            {"A#3,B#3,E#3", "B#3,C#3"},
            rels(abce_entry["four_nf_decomposition"]),
        )
        self.assertEqual(
            {"ABE", "BC"},
            rels(abce_entry["original_four_nf_decomposition"]),
        )
        self.assertEqual(["B#3 -> C#3"], abce_entry["applicable_fds"])
        self.assertEqual(["B -> C"], abce_entry["original_applicable_fds"])
        self.assertEqual("B#3 -> C#3", abce_entry["steps"][0]["dependency"])
        self.assertEqual("B -> C", abce_entry["original_steps"][0]["dependency"])

    def test_alternative_sql_null_decomposition_is_computed_before_4nf(self):
        output = analyze_combined_schema(
            schema_from_text(
                """
                attributes: A B C D
                nullable: B C
                B ->N<- C
                """
            )
        )

        self.assertEqual(
            {"ABD", "ACD"},
            rels(output["sql_null_stage"]["sql_null_decomposition"]),
        )
        self.assertEqual(
            {"A#1,B#1,D#1", "A#2,C#2,D#2"},
            rels(output["final_decomposition"]),
        )
        self.assertEqual(
            {"ABD", "ACD"},
            rels(output["original_final_decomposition"]),
        )

    def test_dependency_is_not_applicable_when_an_attribute_is_missing(self):
        output = analyze_combined_schema(
            schema_from_text(
                """
                attributes: A B C D
                nullable: C
                AB -> C
                """
            )
        )

        abd_entry = next(
            item
            for item in output["per_relation_4nf"]
            if rel_name(item["sql_null_relation"]) == "ABD"
        )
        abcd_entry = next(
            item
            for item in output["per_relation_4nf"]
            if rel_name(item["sql_null_relation"]) == "ABCD"
        )

        self.assertEqual([], abd_entry["applicable_fds"])
        self.assertEqual(["A#2, B#2 -> C#2"], abcd_entry["applicable_fds"])
        self.assertEqual(["AB -> C"], abcd_entry["original_applicable_fds"])

    def test_mvd_violation_decomposes_relation_to_4nf(self):
        output = analyze_combined_schema(
            schema_from_text(
                """
                attributes: A B C D
                nullable:
                A ->> B
                """
            )
        )

        self.assertEqual(
            {"AB", "ACD"},
            rels(output["final_decomposition"]),
        )
        self.assertEqual({"AB", "ACD"}, rels(output["original_final_decomposition"]))
        self.assertEqual(1, len(output["per_relation_4nf"]))
        self.assertEqual("R", output["per_relation_4nf"][0]["sql_null_relation_name"])
        steps = output["per_relation_4nf"][0]["steps"]
        self.assertEqual("MVD", steps[0]["dependency_kind"])
        self.assertEqual("A ->> B", steps[0]["dependency"])

    def test_4nf_decomposition_preserves_transitive_fd_dependency_relation(self):
        output = analyze_combined_schema(
            schema_from_text(
                """
                relation T: ssn name email dept manager
                ssn -> name
                ssn -> dept
                ssn ->> email
                dept -> manager
                """
            )
        )

        self.assertEqual(
            {
                "dept,manager",
                "dept,ssn",
                "email,ssn",
                "name,ssn",
            },
            rels(output["final_decomposition"]),
        )

    def test_multi_character_attributes_are_parsed_as_single_attributes(self):
        output = analyze_combined_schema(
            schema_from_text(
                """
                attributes: Customer Order Product
                nullable: Order Product
                Order -N-> Product
                Customer -> Order
                Customer ->> Product
                """
            )
        )

        self.assertEqual(
            {"Customer", "Order", "Product"},
            set(output["attributes"]),
        )
        self.assertIn("Customer -> Order", output["fds"])
        self.assertIn("Customer ->> Product", output["mvds"])

    def test_sql_null_dependency_attributes_must_be_nullable(self):
        with self.assertRaisesRegex(ValueError, "not over nullable attributes"):
            schema_from_text(
                """
                attributes: A B C
                nullable: B
                B -N-> C
                """
            )

    def test_fds_and_mvds_must_use_declared_attributes(self):
        with self.assertRaisesRegex(ValueError, "unknown attributes"):
            schema_from_text(
                """
                attributes: A B C
                nullable: B C
                A ->> D
                """
            )

    def test_multiple_input_relations_are_analyzed_separately(self):
        output = analyze_combined_schema(
            schema_from_text(
                """
                relation R1: A B C E
                nullable: B C
                B -N-> C
                B -> C

                relation R2: A D E
                nullable: D
                A ->> D
                """
            )
        )

        self.assertEqual(
            [
                {
                    "name": "R1",
                    "attributes": ["A", "B", "C", "E"],
                    "nullable": ["B", "C"],
                },
                {
                    "name": "R2",
                    "attributes": ["A", "D", "E"],
                    "nullable": ["D"],
                },
            ],
            output["input_relations"],
        )
        self.assertEqual(2, len(output["per_input_relation"]))

        r1 = next(
            item
            for item in output["per_input_relation"]
            if item["input_relation"] == "R1"
        )
        r2 = next(
            item
            for item in output["per_input_relation"]
            if item["input_relation"] == "R2"
        )

        self.assertEqual(["B -N-> C"], r1["applicable_sql_null_dependencies"])
        self.assertEqual(["B -> C"], r1["applicable_fds"])
        self.assertEqual([], r1["applicable_mvds"])
        self.assertEqual([], r2["applicable_sql_null_dependencies"])
        self.assertEqual([], r2["applicable_fds"])
        self.assertEqual(["A ->> D"], r2["applicable_mvds"])
        self.assertEqual(
            {"A#1,E#1", "A#2,D#2", "A#2,E#2"},
            rels(r2["final_decomposition"]),
        )
        self.assertEqual({"AD", "AE"}, rels(r2["original_final_decomposition"]))
        self.assertEqual(
            ["R1#1", "R1#2", "R1#3"],
            [
                item["sql_null_relation_name"]
                for item in r1["per_relation_4nf"]
            ],
        )
        self.assertEqual(
            [
                ["A#1", "E#1"],
                ["A#2", "B#2", "E#2"],
                ["A#3", "B#3", "C#3", "E#3"],
            ],
            [
                item["renamed_sql_null_relation"]
                for item in r1["per_relation_4nf"]
            ],
        )
        r1_generated_4nf = next(
            item
            for item in r1["per_relation_4nf"]
            if item["sql_null_relation_name"] == "R1#3"
        )
        self.assertEqual(
            {"A#3,B#3,E#3", "B#3,C#3"},
            rels(r1_generated_4nf["four_nf_decomposition"]),
        )
        self.assertEqual(["B#3 -> C#3"], r1_generated_4nf["applicable_fds"])
        self.assertEqual(
            ["R2#1", "R2#2"],
            [
                item["sql_null_relation_name"]
                for item in r2["per_relation_4nf"]
            ],
        )
        self.assertEqual(
            [
                ["A#1", "E#1"],
                ["A#2", "D#2", "E#2"],
            ],
            [
                item["renamed_sql_null_relation"]
                for item in r2["per_relation_4nf"]
            ],
        )

    def test_relation_specific_nullable_attributes_control_sql_null_dependencies(self):
        output = analyze_combined_schema(
            schema_from_text(
                """
                relation R1: A B C E
                nullable: B C
                B -N-> C

                relation R2: A B C D
                nullable: B C
                """
            )
        )

        r1 = next(
            item
            for item in output["per_input_relation"]
            if item["input_relation"] == "R1"
        )
        r2 = next(
            item
            for item in output["per_input_relation"]
            if item["input_relation"] == "R2"
        )

        self.assertEqual(["B -N-> C"], r1["applicable_sql_null_dependencies"])
        self.assertEqual([], r2["applicable_sql_null_dependencies"])
        self.assertEqual(["B", "C"], r1["nullable"])
        self.assertEqual(["B", "C"], r2["nullable"])

    def test_sql_null_dependency_must_use_nullable_attributes_in_same_relation(self):
        with self.assertRaisesRegex(ValueError, "not over nullable attributes"):
            schema_from_text(
                """
                relation R1: A B C
                nullable R1: B
                B -N-> C
                """
            )

    def test_relation_specific_nullable_attributes_must_belong_to_that_relation(self):
        with self.assertRaisesRegex(ValueError, "unknown attributes"):
            schema_from_text(
                """
                relation R1: A B
                nullable R1: C
                """
            )

    def test_sql_null_dependency_must_be_contained_in_current_input_relation(self):
        with self.assertRaisesRegex(ValueError, "unknown attributes"):
            schema_from_text(
                """
                relation R1: A B
                nullable: B
                B -N-> C
                """
            )

    def test_fd_or_mvd_must_be_contained_in_current_input_relation(self):
        with self.assertRaisesRegex(ValueError, "unknown attributes"):
            schema_from_text(
                """
                relation R1: A B
                nullable:
                A -> D
                """
            )

    def test_parser_accepts_database_schemas_and_inclusion_dependencies(self):
        parsed = schema_from_text(
            """
            database schema Sales:
            relation Orders: orderID orderCustomerID productID
            relation Customers: customerID region
            orderCustomerID => customerID
            """
        )

        self.assertEqual(["Sales"], [item.name for item in parsed.database_schemas])
        self.assertEqual(
            ["Orders", "Customers"],
            [item.name for item in parsed.database_schemas[0].relations],
        )
        self.assertEqual(
            [("orderCustomerID",)],
            [dep.lhs for dep in parsed.database_schemas[0].inclusion_dependencies],
        )

        output = analyze_combined_schema(parsed)
        self.assertEqual(
            [
                {
                    "lhs": ["orderCustomerID"],
                    "rhs": ["customerID"],
                    "text": "orderCustomerID => customerID",
                }
            ],
            output["inclusion_dependencies"],
        )

    def test_parser_accepts_typed_inclusion_dependencies(self):
        parsed = schema_from_text(
            """
            database schema Sales:
            relation Orders: orderID orderCustomerID orderRegion
            relation Customers: customerID region
            orderCustomerID == customerID
            orderRegion o=> region
            orderID x=> orderCustomerID
            """
        )

        self.assertEqual(
            ["equality", "covering", "disjoint"],
            [dep.kind for dep in parsed.database_schemas[0].inclusion_dependencies],
        )

        output = analyze_combined_schema(parsed)
        self.assertEqual(
            [
                {
                    "lhs": ["orderCustomerID"],
                    "rhs": ["customerID"],
                    "text": "orderCustomerID == customerID",
                },
                {
                    "lhs": ["orderRegion"],
                    "rhs": ["region"],
                    "text": "orderRegion o=> region",
                },
                {
                    "lhs": ["orderID"],
                    "rhs": ["orderCustomerID"],
                    "text": "orderID x=> orderCustomerID",
                },
            ],
            output["inclusion_dependencies"],
        )

    def test_inclusion_dependency_sides_must_have_same_arity(self):
        with self.assertRaisesRegex(ValueError, "same number of attributes"):
            schema_from_text(
                """
                relation R: A B C
                A B => C
                """
            )

    def test_functional_dependency_accepts_key_att_relation_notation(self):
        parsed = schema_from_text(
            """
            relation R: A B C
            A -> att(R)
            """
        )

        self.assertEqual(
            [("A", "B"), ("A", "C")],
            [
                (next(iter(fd.lhs)), next(iter(fd.rhs)))
                for fd in parsed.input_relations[0].fds
            ],
        )
        output = analyze_combined_schema(parsed)
        self.assertEqual(
            ["A -> B", "A -> C"],
            output["per_input_relation"][0]["applicable_fds"],
        )

    def test_multi_rhs_fd_matches_equivalent_split_fds(self):
        combined = analyze_combined_schema(
            schema_from_text(
                """
                relation T: ssn name dept
                ssn -> dept name
                """
            )
        )
        split = analyze_combined_schema(
            schema_from_text(
                """
                relation T: ssn name dept
                ssn -> name
                ssn -> dept
                """
            )
        )

        self.assertEqual(split["fds"], combined["fds"])
        self.assertEqual(split["final_decomposition"], combined["final_decomposition"])
        self.assertEqual(
            split["per_input_relation"][0]["applicable_fds"],
            combined["per_input_relation"][0]["applicable_fds"],
        )
        self.assertEqual(
            split["per_input_relation"][0]["per_relation_4nf"][0]["steps"],
            combined["per_input_relation"][0]["per_relation_4nf"][0]["steps"],
        )


if __name__ == "__main__":
    unittest.main()

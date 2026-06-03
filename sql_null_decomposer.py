#!/usr/bin/env python3
"""
Compute SQL-null decompositions.

Text input format:

  relation R: A B C E
  attributes: A B C E
  nullable: B C
  B -N-> C
  B <-N-> C
  B ->N<- C

JSON input format:

  {
    "attributes": ["A", "B", "C", "E"],
    "nullable": ["B", "C"],
    "implies": [{"lhs": "B", "rhs": "C"}],
    "jointly": [{"lhs": "B", "rhs": "C"}],
    "alternative": [{"lhs": "B", "rhs": "C"}]
  }

The provisional decomposition contains every relation of the form

  (attributes - nullable) union S

where S is any subset of the nullable attributes.
"""

from __future__ import annotations

import argparse
import itertools
import json
import re
import sys
from dataclasses import dataclass
from typing import Iterable, Literal, Sequence


AttrSet = frozenset[str]
Kind = Literal["implies_sql_null", "jointly_sql_null", "alternative_sql_null"]


def fs(values: Iterable[str]) -> AttrSet:
    return frozenset(values)


@dataclass(frozen=True)
class SQLNullDependency:
    kind: Kind
    lhs: str
    rhs: str


@dataclass(frozen=True)
class NamedSQLNullRelation:
    name: str
    attributes: AttrSet
    nullable_subset: AttrSet


@dataclass(frozen=True)
class SQLNullSchema:
    attributes: AttrSet
    nullable: AttrSet
    dependencies: tuple[SQLNullDependency, ...]
    relation_name: str = "R"

    @property
    def non_nullable(self) -> AttrSet:
        return self.attributes - self.nullable


def parse_attribute_list(text: str) -> AttrSet:
    value = text.strip()
    if not value or value in {"{}", "∅"}:
        return frozenset()

    value = value.strip("{}[]()")
    if "," in value or re.search(r"\s", value):
        return frozenset(token for token in re.split(r"[\s,]+", value) if token)

    return frozenset(value)


def powerset(attributes: Iterable[str]) -> list[AttrSet]:
    items = sorted(attributes)
    result: list[AttrSet] = []
    for size in range(len(items) + 1):
        for combo in itertools.combinations(items, size):
            result.append(frozenset(combo))
    return result


def sort_relations(relations: Iterable[AttrSet]) -> list[AttrSet]:
    return sorted(set(relations), key=lambda rel: (len(rel), tuple(sorted(rel))))


def format_relation(relation: AttrSet) -> str:
    if not relation:
        return "{}"
    if any(len(attr) > 1 for attr in relation):
        return ", ".join(sorted(relation))
    return "".join(sorted(relation))


def relation_number(relation_name: str) -> str | None:
    if "#" not in relation_name:
        return None
    suffix = relation_name.rsplit("#", 1)[1]
    return suffix or None


def rename_attributes_for_relation(attributes: AttrSet, relation_name: str) -> AttrSet:
    number = relation_number(relation_name)
    if number is None:
        return attributes
    return frozenset(f"{attribute}#{number}" for attribute in attributes)


def validate_schema(schema: SQLNullSchema) -> SQLNullSchema:
    unknown_nullable = schema.nullable - schema.attributes
    if unknown_nullable:
        raise ValueError(
            f"nullable attributes are not in attributes: {sorted(unknown_nullable)}"
        )

    for dep in schema.dependencies:
        dep_attributes = {dep.lhs, dep.rhs}
        unknown = dep_attributes - set(schema.attributes)
        if unknown:
            raise ValueError(
                f"dependency {dep.lhs} {dependency_symbol(dep.kind)} {dep.rhs} "
                f"uses unknown attributes: {sorted(unknown)}"
            )

        non_nullable = dep_attributes - set(schema.nullable)
        if non_nullable:
            raise ValueError(
                f"SQL-null dependency {dep.lhs} {dependency_symbol(dep.kind)} {dep.rhs} "
                f"uses non-nullable attributes: {sorted(non_nullable)}"
            )

    return schema


def dependency_symbol(kind: Kind) -> str:
    if kind == "implies_sql_null":
        return "-N->"
    if kind == "jointly_sql_null":
        return "<-N->"
    return "->N<-"


def nullable_powerset(schema: SQLNullSchema) -> list[AttrSet]:
    return powerset(schema.nullable)


def provisional_decomposition(schema: SQLNullSchema) -> list[AttrSet]:
    return [
        schema.non_nullable | nullable_subset
        for nullable_subset in nullable_powerset(schema)
    ]


def removal_reasons(nullable_subset: AttrSet, schema: SQLNullSchema) -> list[str]:
    reasons: list[str] = []
    for dep in schema.dependencies:
        has_lhs = dep.lhs in nullable_subset
        has_rhs = dep.rhs in nullable_subset

        if dep.kind == "jointly_sql_null" and has_lhs != has_rhs:
            reasons.append(
                f"{format_relation(nullable_subset)} contains exactly one of "
                f"{dep.lhs}, {dep.rhs} for {dep.lhs} <-N-> {dep.rhs}"
            )

        if dep.kind == "implies_sql_null" and has_rhs and not has_lhs:
            reasons.append(
                f"{format_relation(nullable_subset)} contains {dep.rhs} but not "
                f"{dep.lhs} for {dep.lhs} -N-> {dep.rhs}"
            )

        if dep.kind == "alternative_sql_null" and has_lhs == has_rhs:
            if has_lhs:
                reason = "contains both"
            else:
                reason = "contains neither"
            reasons.append(
                f"{format_relation(nullable_subset)} {reason} "
                f"{dep.lhs}, {dep.rhs} for {dep.lhs} ->N<- {dep.rhs}"
            )

    return reasons


def restricted_nullable_powerset(
    schema: SQLNullSchema,
) -> tuple[list[AttrSet], dict[str, list[str]]]:
    kept: list[AttrSet] = []
    removed: dict[str, list[str]] = {}

    for nullable_subset in nullable_powerset(schema):
        reasons = removal_reasons(nullable_subset, schema)
        if reasons:
            removed[format_relation(nullable_subset)] = reasons
        else:
            kept.append(nullable_subset)

    return kept, removed


def sql_null_decomposition(schema: SQLNullSchema) -> tuple[list[AttrSet], dict[str, list[str]]]:
    kept_nullable_sets, removed_nullable_sets = restricted_nullable_powerset(schema)
    kept_relations = [
        schema.non_nullable | nullable_subset
        for nullable_subset in kept_nullable_sets
    ]
    removed_relations: dict[str, list[str]] = {}
    for nullable_subset in nullable_powerset(schema):
        reasons = removed_nullable_sets.get(format_relation(nullable_subset))
        if reasons:
            removed_relations[format_relation(schema.non_nullable | nullable_subset)] = reasons
    return kept_relations, removed_relations


def named_sql_null_decomposition(
    schema: SQLNullSchema,
) -> tuple[list[NamedSQLNullRelation], dict[str, list[str]]]:
    if not schema.nullable:
        return [
            NamedSQLNullRelation(
                schema.relation_name,
                schema.attributes,
                frozenset(),
            )
        ], {}

    kept_nullable_sets, removed_nullable_sets = restricted_nullable_powerset(schema)
    named_relations = [
        NamedSQLNullRelation(
            f"{schema.relation_name}#{index}",
            schema.non_nullable | nullable_subset,
            nullable_subset,
        )
        for index, nullable_subset in enumerate(kept_nullable_sets, start=1)
    ]
    return named_relations, removed_nullable_sets


def analyze_schema(schema: SQLNullSchema) -> dict[str, object]:
    validate_schema(schema)
    provisional = provisional_decomposition(schema)
    final, removed = sql_null_decomposition(schema)
    restricted_nullable, removed_nullable = restricted_nullable_powerset(schema)
    named_final, _ = named_sql_null_decomposition(schema)

    return {
        "relation": schema.relation_name,
        "attributes": sorted(schema.attributes),
        "nullable": sorted(schema.nullable),
        "non_nullable": sorted(schema.non_nullable),
        "dependencies": [
            {
                "kind": dep.kind,
                "lhs": dep.lhs,
                "rhs": dep.rhs,
                "text": f"{dep.lhs} {dependency_symbol(dep.kind)} {dep.rhs}",
            }
            for dep in schema.dependencies
        ],
        "nullable_powerset": [sorted(relation) for relation in nullable_powerset(schema)],
        "restricted_nullable_powerset": [
            sorted(relation) for relation in restricted_nullable
        ],
        "removed_nullable_sets": removed_nullable,
        "provisional_decomposition": [sorted(relation) for relation in provisional],
        "sql_null_decomposition": [sorted(relation) for relation in final],
        "named_sql_null_decomposition": [
            {
                "name": relation.name,
                "attributes": sorted(rename_attributes_for_relation(relation.attributes, relation.name)),
                "original_attributes": sorted(relation.attributes),
                "nullable_subset": sorted(relation.nullable_subset),
                "renamed_nullable_subset": sorted(
                    rename_attributes_for_relation(relation.nullable_subset, relation.name)
                ),
            }
            for relation in named_final
        ],
        "renamed_sql_null_decomposition": [
            sorted(rename_attributes_for_relation(relation.attributes, relation.name))
            for relation in named_final
        ],
        "removed_relations": removed,
    }


def parse_dependency_object(obj: dict[str, object], kind: Kind) -> SQLNullDependency:
    lhs = str(obj.get("lhs", "")).strip()
    rhs = str(obj.get("rhs", "")).strip()
    if not lhs or not rhs:
        raise ValueError(f"{kind} dependency must have lhs and rhs")
    return SQLNullDependency(kind, lhs, rhs)


def schema_from_json(data: dict[str, object]) -> SQLNullSchema:
    relation_name = str(data.get("relation", data.get("name", "R"))).strip() or "R"
    attributes = frozenset(str(attr) for attr in data.get("attributes", []))
    nullable = frozenset(str(attr) for attr in data.get("nullable", []))
    dependencies = [
        parse_dependency_object(dep, "implies_sql_null")
        for dep in data.get("implies", [])
    ]
    dependencies += [
        parse_dependency_object(dep, "jointly_sql_null")
        for dep in data.get("jointly", [])
    ]
    dependencies += [
        parse_dependency_object(dep, "alternative_sql_null")
        for dep in data.get("alternative", [])
    ]
    dependencies += [
        parse_dependency_object(dep, "alternative_sql_null")
        for dep in data.get("alternative_sql_null", [])
    ]
    return validate_schema(SQLNullSchema(attributes, nullable, tuple(dependencies), relation_name))


def parse_single_attribute(text: str, known_attributes: AttrSet, line_no: int) -> str:
    value = text.strip()
    if not value:
        raise ValueError(f"line {line_no}: missing attribute")
    if value in known_attributes:
        return value
    if "," in value or re.search(r"\s", value):
        raise ValueError(f"line {line_no}: dependency sides must be single attributes")
    if known_attributes:
        raise ValueError(f"line {line_no}: unknown attribute {value!r}")
    return value


def parse_nullable_attribute_set(text: str, known_attributes: AttrSet, line_no: int) -> AttrSet:
    value = text.strip()
    if not value or value in {"{}", "∅"}:
        return frozenset()
    if value in known_attributes:
        return frozenset([value])

    parsed = parse_attribute_list(value)
    unknown = parsed - known_attributes
    if known_attributes and unknown:
        raise ValueError(f"line {line_no}: unknown nullable attributes {sorted(unknown)}")
    return parsed


def schema_from_text(text: str) -> SQLNullSchema:
    relation_name = "R"
    attributes: AttrSet = frozenset()
    nullable: AttrSet = frozenset()
    dependencies: list[SQLNullDependency] = []

    for line_no, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.split("#", 1)[0].split("--", 1)[0].strip()
        if not line:
            continue

        attrs_match = re.match(r"^(?:attributes|attrs|schema)\s*:\s*(.+)$", line, re.I)
        if attrs_match:
            attributes = parse_attribute_list(attrs_match.group(1))
            continue

        relation_match = re.match(r"^(?:relation|rel)\s+([A-Za-z][\w-]*)\s*:\s*(.+)$", line, re.I)
        if relation_match:
            relation_name = relation_match.group(1)
            attributes = parse_attribute_list(relation_match.group(2))
            continue

        nullable_match = re.match(r"^(?:nullable|sql-nullable|nulls)\s*:\s*(.*)$", line, re.I)
        if nullable_match:
            nullable = parse_nullable_attribute_set(
                nullable_match.group(1),
                attributes,
                line_no,
            )
            continue

        dep_match = re.match(r"^(.*?)\s*(<-N->|->N<-|-N->)\s*(.*?)$", line)
        if not dep_match:
            raise ValueError(
                f"line {line_no}: expected 'attributes:', 'nullable:', "
                "'A -N-> B', 'A <-N-> B', or 'A ->N<- B'"
            )

        lhs = parse_single_attribute(dep_match.group(1), attributes, line_no)
        rhs = parse_single_attribute(dep_match.group(3), attributes, line_no)
        symbol = dep_match.group(2)
        if symbol == "<-N->":
            kind: Kind = "jointly_sql_null"
        elif symbol == "->N<-":
            kind = "alternative_sql_null"
        else:
            kind = "implies_sql_null"
        dependencies.append(SQLNullDependency(kind, lhs, rhs))

    if not attributes:
        raise ValueError("missing attributes line")

    return validate_schema(SQLNullSchema(attributes, nullable, tuple(dependencies), relation_name))


def load_schema(path: str) -> SQLNullSchema:
    with open(path, "r", encoding="utf-8") as file:
        content = file.read()
    if path.lower().endswith(".json"):
        return schema_from_json(json.loads(content))
    return schema_from_text(content)


def main(argv: Sequence[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("schema_file")
    args = parser.parse_args(argv)

    schema = load_schema(args.schema_file)
    print(json.dumps(analyze_schema(schema), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

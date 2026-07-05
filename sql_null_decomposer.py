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
  B ->>N<<- C

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
from typing import Any, Callable, Iterable, Literal, Sequence


AttrSet = frozenset[str]
Kind = Literal[
    "implies_sql_null",
    "jointly_sql_null",
    "alternative_sql_null",
    "existential_sql_null",
]


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
    attribute_order: tuple[str, ...] = ()


NullTaxonomyTargetSelector = Callable[
    [NamedSQLNullRelation, NamedSQLNullRelation],
    Sequence[str] | dict[str, Any] | None,
]


@dataclass(frozen=True)
class SQLNullSchema:
    attributes: AttrSet
    nullable: AttrSet
    dependencies: tuple[SQLNullDependency, ...]
    relation_name: str = "R"
    attribute_order: tuple[str, ...] = ()

    @property
    def non_nullable(self) -> AttrSet:
        return self.attributes - self.nullable

    @property
    def ordered_attributes(self) -> tuple[str, ...]:
        ordered = [
            attr
            for attr in self.attribute_order
            if attr in self.attributes
        ]
        missing = sorted(self.attributes - frozenset(ordered))
        return tuple([*ordered, *missing])


def parse_attribute_list(text: str) -> AttrSet:
    return frozenset(parse_attribute_sequence(text))


def parse_attribute_sequence(text: str) -> tuple[str, ...]:
    value = text.strip()
    if not value or value in {"{}", "∅"}:
        return ()

    value = value.strip("{}[]()")
    if "," in value or re.search(r"\s", value):
        tokens = (token for token in re.split(r"[\s,]+", value) if token)
    else:
        tokens = tuple(value)

    return tuple(dict.fromkeys(tokens))


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


def format_sequence(attributes: Sequence[str]) -> str:
    if not attributes:
        return "{}"
    if any(len(attr) > 1 for attr in attributes):
        return ", ".join(attributes)
    return "".join(attributes)


def relation_number(relation_name: str) -> str | None:
    if "#" not in relation_name:
        return None
    suffix = relation_name.rsplit("#", 1)[1]
    return suffix or None


def rename_attribute_for_relation(attribute: str, relation_name: str) -> str:
    number = relation_number(relation_name)
    if number is None:
        return attribute
    return f"{attribute}#{number}"


def rename_attributes_for_relation(attributes: AttrSet, relation_name: str) -> AttrSet:
    return frozenset(
        rename_attribute_for_relation(attribute, relation_name)
        for attribute in attributes
    )


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
    if kind == "alternative_sql_null":
        return "->N<-"
    return "->>N<<-"


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

        if dep.kind == "existential_sql_null" and not (has_lhs or has_rhs):
            reasons.append(
                f"{format_relation(nullable_subset)} contains neither "
                f"{dep.lhs}, {dep.rhs} for {dep.lhs} ->>N<<- {dep.rhs}"
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

    top_nullable_subset = frozenset()
    if top_nullable_subset not in kept:
        kept.insert(0, top_nullable_subset)
        removed.pop(format_relation(top_nullable_subset), None)

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
    suffix_start: int = 1,
) -> tuple[list[NamedSQLNullRelation], dict[str, list[str]]]:
    if not schema.nullable:
        return [
            NamedSQLNullRelation(
                schema.relation_name,
                schema.attributes,
                frozenset(),
                schema.ordered_attributes,
            )
        ], {}

    kept_nullable_sets, removed_nullable_sets = restricted_nullable_powerset(schema)
    next_suffix = suffix_start
    named_relations: list[NamedSQLNullRelation] = []
    for nullable_subset in kept_nullable_sets:
        relation_name = schema.relation_name
        if nullable_subset:
            relation_name = f"{schema.relation_name}#{next_suffix}"
            next_suffix += 1
        named_relations.append(
            NamedSQLNullRelation(
                relation_name,
                schema.non_nullable | nullable_subset,
                nullable_subset,
                tuple(
                    attr
                    for attr in schema.ordered_attributes
                    if attr in schema.non_nullable or attr in nullable_subset
                ),
            )
        )
    return named_relations, removed_nullable_sets


def named_sql_null_decomposition_next_suffix(
    relations: Iterable[NamedSQLNullRelation],
    suffix_start: int,
) -> int:
    next_suffix = suffix_start
    for relation in relations:
        number = relation_number(relation.name)
        if number is None:
            continue
        try:
            next_suffix = max(next_suffix, int(number) + 1)
        except ValueError:
            continue
    return next_suffix


def ordered_attributes(attributes: Iterable[str]) -> list[str]:
    return sorted(attributes or [])


def null_taxonomy_edges(
    relations: Iterable[NamedSQLNullRelation],
) -> list[tuple[NamedSQLNullRelation, NamedSQLNullRelation]]:
    items = list(relations or [])
    edges: list[tuple[NamedSQLNullRelation, NamedSQLNullRelation]] = []
    for superior in items:
        superior_attrs = superior.attributes
        for inferior in items:
            inferior_attrs = inferior.attributes
            if superior is inferior or not superior_attrs < inferior_attrs:
                continue
            if any(
                superior_attrs < middle.attributes < inferior_attrs
                for middle in items
                if middle is not superior and middle is not inferior
            ):
                continue
            edges.append((inferior, superior))
    return sorted(
        edges,
        key=lambda edge: (
            len(edge[1].attributes),
            ordered_attributes(edge[1].attributes),
            len(edge[0].attributes),
            ordered_attributes(edge[0].attributes),
            edge[0].name,
            edge[1].name,
        ),
    )


def null_taxonomy_edge_attributes(
    inferior: NamedSQLNullRelation,
    superior: NamedSQLNullRelation,
    target_attribute_selector: NullTaxonomyTargetSelector | None = None,
) -> dict[str, object]:
    target_original = null_taxonomy_target_original_attributes(
        inferior,
        superior,
        target_attribute_selector,
    )
    target = [
        rename_attribute_for_relation(attribute, superior.name)
        for attribute in target_original
    ]
    source = [
        rename_attribute_for_relation(attribute, inferior.name)
        for attribute in target_original
    ]
    return {
        "source_attributes": source,
        "target_attributes": target,
        "source_relation": inferior.name,
        "target_relation": superior.name,
    }


def null_taxonomy_edge_attribute_entries(
    inferior: NamedSQLNullRelation,
    superior: NamedSQLNullRelation,
    target_attribute_selector: NullTaxonomyTargetSelector | None = None,
) -> list[dict[str, object]]:
    entries: list[dict[str, object]] = []
    seen: set[tuple[str, ...]] = set()
    for selection in null_taxonomy_target_selections(
        inferior,
        superior,
        target_attribute_selector,
    ):
        target_original = selection["target"] or tuple(superior.attribute_order) or tuple(
            ordered_attributes(superior.attributes)
        )
        key = tuple(target_original)
        if key in seen:
            continue
        seen.add(key)
        target = [
            rename_attribute_for_relation(attribute, superior.name)
            for attribute in target_original
        ]
        source = [
            rename_attribute_for_relation(attribute, inferior.name)
            for attribute in target_original
        ]
        entries.append(
            {
                "source_attributes": source,
                "target_attributes": target,
                "source_relation": inferior.name,
                "target_relation": superior.name,
            }
        )
    return entries


def null_taxonomy_target_original_attributes(
    inferior: NamedSQLNullRelation,
    superior: NamedSQLNullRelation,
    target_attribute_selector: NullTaxonomyTargetSelector | None = None,
) -> tuple[str, ...]:
    selected = null_taxonomy_target_selections(
        inferior,
        superior,
        target_attribute_selector,
    )[0]["target"]
    return selected or tuple(superior.attribute_order) or tuple(
        ordered_attributes(superior.attributes)
    )


def null_taxonomy_target_selection(
    inferior: NamedSQLNullRelation,
    superior: NamedSQLNullRelation,
    target_attribute_selector: NullTaxonomyTargetSelector | None = None,
) -> dict[str, Any]:
    return null_taxonomy_target_selections(
        inferior,
        superior,
        target_attribute_selector,
    )[0]


def null_taxonomy_target_selections(
    inferior: NamedSQLNullRelation,
    superior: NamedSQLNullRelation,
    target_attribute_selector: NullTaxonomyTargetSelector | None = None,
) -> list[dict[str, Any]]:
    if target_attribute_selector is None:
        return [{"target": (), "remove": (), "has_remove": False}]

    raw = target_attribute_selector(inferior, superior)
    if isinstance(raw, dict) and "choices" in raw:
        raw_choices = list(raw.get("choices") or [])
    elif isinstance(raw, (list, tuple)) and all(isinstance(item, dict) for item in raw):
        raw_choices = list(raw)
    else:
        raw_choices = [raw]

    selections: list[dict[str, Any]] = []
    for choice in raw_choices:
        has_remove = isinstance(choice, dict) and "remove" in choice
        raw_target = choice.get("target", ()) if isinstance(choice, dict) else choice
        raw_remove = choice.get("remove", ()) if isinstance(choice, dict) else ()
        selections.append(
            {
                "target": tuple(
                    attr
                    for attr in raw_target or ()
                    if attr in superior.attributes
                ),
                "remove": tuple(
                    attr
                    for attr in raw_remove or ()
                    if attr in superior.attributes
                ),
                "has_remove": has_remove,
            }
        )

    return selections or [{"target": (), "remove": (), "has_remove": False}]


def reduce_null_taxonomy_relations(
    relations: Iterable[NamedSQLNullRelation],
    target_attribute_selector: NullTaxonomyTargetSelector | None = None,
) -> list[NamedSQLNullRelation]:
    items = list(relations or [])
    if target_attribute_selector is None:
        return items

    removals_by_name: dict[str, set[str]] = {
        relation.name: set()
        for relation in items
    }
    for inferior, superior in null_taxonomy_edges(items):
        for selection in null_taxonomy_target_selections(
            inferior,
            superior,
            target_attribute_selector,
        ):
            target_original = selection["target"] or tuple(superior.attribute_order) or tuple(
                ordered_attributes(superior.attributes)
            )
            key_attrs = frozenset(target_original)
            if selection["has_remove"]:
                removals_by_name[inferior.name].update(selection["remove"])
            elif key_attrs and key_attrs < superior.attributes:
                removals_by_name[inferior.name].update(superior.attributes - key_attrs)

    reduced: list[NamedSQLNullRelation] = []
    for relation in items:
        removed = frozenset(removals_by_name.get(relation.name, ()))
        if not removed:
            reduced.append(relation)
            continue
        reduced.append(
            NamedSQLNullRelation(
                relation.name,
                relation.attributes - removed,
                relation.nullable_subset - removed,
                tuple(
                    attr
                    for attr in relation.attribute_order
                    if attr not in removed
                ),
            )
        )
    return reduced


def null_taxonomy_inclusion_dependency(edge: dict[str, object]) -> dict[str, object]:
    source = list(edge["source_attributes"])
    target = list(edge["target_attributes"])
    return {
        "kind": "inclusion",
        "sources": [source],
        "target": target,
        "lhs": source,
        "rhs": target,
        "text": f"{format_sequence(source)} => {format_sequence(target)}",
        "source_relation": edge["source_relation"],
        "target_relation": edge["target_relation"],
    }


def null_taxonomy_structure(
    relations: Iterable[NamedSQLNullRelation],
    target_attribute_selector: NullTaxonomyTargetSelector | None = None,
    display_relations: Iterable[NamedSQLNullRelation] | None = None,
) -> dict[str, object]:
    items = list(relations or [])
    display_by_name = {
        relation.name: relation
        for relation in (display_relations if display_relations is not None else items)
    }
    edge_attributes = [
        (inferior, superior, edge)
        for inferior, superior in null_taxonomy_edges(items)
        for edge in null_taxonomy_edge_attribute_entries(
            inferior,
            superior,
            target_attribute_selector,
        )
    ]
    return {
        "relations": [
            {
                "name": display_relation.name,
                "attributes": sorted(
                    rename_attributes_for_relation(
                        display_relation.attributes,
                        display_relation.name,
                    )
                ),
                "original_attributes": sorted(display_relation.attributes),
                "nullable_subset": sorted(display_relation.nullable_subset),
            }
            for relation in items
            for display_relation in [display_by_name.get(relation.name, relation)]
        ],
        "edges": [
            {
                "source_relation": inferior.name,
                "target_relation": superior.name,
                "source_attributes": edge["source_attributes"],
                "target_attributes": edge["target_attributes"],
            }
            for inferior, superior, edge in edge_attributes
        ],
        "inclusion_dependencies": [
            null_taxonomy_inclusion_dependency(edge)
            for _, _, edge in edge_attributes
        ],
    }


def analyze_schema(
    schema: SQLNullSchema,
    suffix_start: int = 1,
    target_attribute_selector: NullTaxonomyTargetSelector | None = None,
) -> dict[str, object]:
    validate_schema(schema)
    provisional = provisional_decomposition(schema)
    final, removed = sql_null_decomposition(schema)
    restricted_nullable, removed_nullable = restricted_nullable_powerset(schema)
    original_named_final, _ = named_sql_null_decomposition(
        schema,
        suffix_start=suffix_start,
    )
    named_final = reduce_null_taxonomy_relations(
        original_named_final,
        target_attribute_selector,
    )
    null_taxonomy = null_taxonomy_structure(
        original_named_final,
        target_attribute_selector,
        named_final,
    )

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
        "null_taxonomy": null_taxonomy,
        "null_taxonomy_inclusion_dependencies": null_taxonomy["inclusion_dependencies"],
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
    attribute_order = tuple(
        dict.fromkeys(str(attr) for attr in data.get("attributes", []))
    )
    attributes = frozenset(attribute_order)
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
    dependencies += [
        parse_dependency_object(dep, "existential_sql_null")
        for dep in data.get("existential", [])
    ]
    dependencies += [
        parse_dependency_object(dep, "existential_sql_null")
        for dep in data.get("existential_sql_null", [])
    ]
    return validate_schema(
        SQLNullSchema(
            attributes,
            nullable,
            tuple(dependencies),
            relation_name,
            attribute_order,
        )
    )


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
    attribute_order: tuple[str, ...] = ()
    nullable: AttrSet = frozenset()
    dependencies: list[SQLNullDependency] = []

    for line_no, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.split("#", 1)[0].split("--", 1)[0].split(";", 1)[0].strip()
        if not line:
            continue

        attrs_match = re.match(r"^(?:attributes|attrs|schema)\s*:\s*(.+)$", line, re.I)
        if attrs_match:
            attribute_order = parse_attribute_sequence(attrs_match.group(1))
            attributes = frozenset(attribute_order)
            continue

        relation_match = re.match(r"^(?:relation|rel)\s+([A-Za-z][\w-]*)\s*:\s*(.+)$", line, re.I)
        if relation_match:
            relation_name = relation_match.group(1)
            attribute_order = parse_attribute_sequence(relation_match.group(2))
            attributes = frozenset(attribute_order)
            continue

        nullable_match = re.match(r"^(?:nullable|sql-nullable|nulls)\s*:\s*(.*)$", line, re.I)
        if nullable_match:
            nullable = parse_nullable_attribute_set(
                nullable_match.group(1),
                attributes,
                line_no,
            )
            continue

        dep_match = re.match(r"^(.*?)\s*(->>N<<-|<-N->|->N<-|-N->)\s*(.*?)$", line)
        if not dep_match:
            raise ValueError(
                f"line {line_no}: expected 'attributes:', 'nullable:', "
                "'A -N-> B', 'A <-N-> B', 'A ->N<- B', or 'A ->>N<<- B'"
            )

        lhs = parse_single_attribute(dep_match.group(1), attributes, line_no)
        rhs = parse_single_attribute(dep_match.group(3), attributes, line_no)
        symbol = dep_match.group(2)
        if symbol == "<-N->":
            kind: Kind = "jointly_sql_null"
        elif symbol == "->N<-":
            kind = "alternative_sql_null"
        elif symbol == "->>N<<-":
            kind = "existential_sql_null"
        else:
            kind = "implies_sql_null"
        dependencies.append(SQLNullDependency(kind, lhs, rhs))

    if not attributes:
        raise ValueError("missing attributes line")

    return validate_schema(
        SQLNullSchema(
            attributes,
            nullable,
            tuple(dependencies),
            relation_name,
            attribute_order,
        )
    )


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

#!/usr/bin/env python3
"""
Compute a two-stage decomposition:

1. SQL-null decomposition.
2. For each SQL-null relation, a recursive 4NF decomposition using only
   FDs/MVDs whose attributes are contained in that relation.

Text input format:

  attributes: A B C D E
  nullable: B C D
  B -N-> C
  C <-N-> D
  B ->N<- D
  AB -> C
  A ->> D

Multi-relation text input format:

  relation R1: A B C E
  nullable: B C
  B -N-> C
  B -> C

  relation R2: A D E
  nullable: D
  A ->> D

Dependency syntax:
  A -N-> B     implies SQL-null
  A <-N-> B    jointly SQL-null
  A ->N<- B    alternative SQL-null
  X -> Y       functional dependency
  X ->> Y      multivalued dependency
"""

from __future__ import annotations

import argparse
import itertools
import json
import re
import sys
from dataclasses import dataclass, field
from typing import Iterable, Sequence

from fd_mvd_normalizer import Analyzer as DependencyAnalyzer
from fd_mvd_normalizer import FD, MVD, Schema as DependencySchema
from sql_null_decomposer import (
    SQLNullDependency,
    SQLNullSchema,
    analyze_schema as analyze_sql_null_schema,
    dependency_symbol,
    named_sql_null_decomposition,
    parse_attribute_list,
    rename_attributes_for_relation,
    validate_schema as validate_sql_null_schema,
)


AttrSet = frozenset[str]
AttrSeq = tuple[str, ...]


def normalize_fds(fds: Iterable[FD]) -> tuple[FD, ...]:
    normalized = set(
        FD(fd.lhs, frozenset([attr]))
        for fd in fds
        for attr in sorted(fd.rhs - fd.lhs)
    )
    return tuple(
        sorted(
            normalized,
            key=lambda fd: (tuple(sorted(fd.lhs)), tuple(sorted(fd.rhs))),
        )
    )


@dataclass(frozen=True)
class Attribute:
    name: str
    nullable: bool = False

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("attribute name must be non-empty")


@dataclass(frozen=True)
class InclusionDependency:
    lhs: AttrSeq
    rhs: AttrSeq


@dataclass(frozen=True, init=False)
class Relation:
    name: str
    attribute_objects: tuple[Attribute, ...]
    sql_null_dependencies: tuple[SQLNullDependency, ...] = ()
    fds: tuple[FD, ...] = ()
    mvds: tuple[MVD, ...] = ()
    inclusion_dependencies: tuple[InclusionDependency, ...] = ()

    def __init__(
        self,
        name: str,
        attributes: Iterable[str | Attribute],
        nullable: Iterable[str] = frozenset(),
        sql_null_dependencies: Iterable[SQLNullDependency] = (),
        fds: Iterable[FD] = (),
        mvds: Iterable[MVD] = (),
        inclusion_dependencies: Iterable[InclusionDependency] = (),
    ) -> None:
        object.__setattr__(self, "name", name)
        object.__setattr__(
            self,
            "attribute_objects",
            normalize_attribute_objects(attributes, nullable),
        )
        object.__setattr__(
            self,
            "sql_null_dependencies",
            tuple(sql_null_dependencies),
        )
        object.__setattr__(self, "fds", normalize_fds(fds))
        object.__setattr__(self, "mvds", tuple(mvds))
        object.__setattr__(
            self,
            "inclusion_dependencies",
            tuple(inclusion_dependencies),
        )

    @property
    def attributes(self) -> AttrSet:
        return frozenset(attribute.name for attribute in self.attribute_objects)

    @property
    def nullable(self) -> AttrSet:
        return frozenset(
            attribute.name
            for attribute in self.attribute_objects
            if attribute.nullable
        )


InputRelation = Relation


@dataclass(frozen=True, init=False)
class DatabaseSchema:
    name: str
    relations: tuple[Relation, ...]
    declared_attributes: AttrSet
    declared_nullable: AttrSet
    sql_null_dependencies: tuple[SQLNullDependency, ...]
    fds: tuple[FD, ...]
    mvds: tuple[MVD, ...]
    inclusion_dependencies: tuple[InclusionDependency, ...]

    def __init__(
        self,
        name: str,
        relations: Iterable[Relation],
        sql_null_dependencies: Iterable[SQLNullDependency] = (),
        fds: Iterable[FD] = (),
        mvds: Iterable[MVD] = (),
        inclusion_dependencies: Iterable[InclusionDependency] = (),
        attributes: Iterable[str] = frozenset(),
        nullable: Iterable[str] = frozenset(),
    ) -> None:
        object.__setattr__(self, "name", name)
        object.__setattr__(self, "relations", tuple(relations))
        object.__setattr__(self, "declared_attributes", frozenset(attributes))
        object.__setattr__(self, "declared_nullable", frozenset(nullable))
        object.__setattr__(
            self,
            "sql_null_dependencies",
            tuple(sql_null_dependencies),
        )
        object.__setattr__(self, "fds", normalize_fds(fds))
        object.__setattr__(self, "mvds", tuple(mvds))
        object.__setattr__(
            self,
            "inclusion_dependencies",
            tuple(inclusion_dependencies),
        )

    @property
    def attributes(self) -> AttrSet:
        return self.declared_attributes | frozenset(
            attr
            for relation in self.relations
            for attr in relation.attributes
        )

    @property
    def nullable(self) -> AttrSet:
        return self.declared_nullable | frozenset(
            attr
            for relation in self.relations
            for attr in relation.nullable
        )


@dataclass(frozen=True, init=False)
class CombinedSchema:
    database_schemas: tuple[DatabaseSchema, ...]

    def __init__(
        self,
        attributes: Iterable[str] | None = None,
        nullable: Iterable[str] = frozenset(),
        input_relations: Iterable[Relation] | None = None,
        sql_null_dependencies: Iterable[SQLNullDependency] = (),
        fds: Iterable[FD] = (),
        mvds: Iterable[MVD] = (),
        inclusion_dependencies: Iterable[InclusionDependency] = (),
        *,
        database_schemas: Iterable[DatabaseSchema] | None = None,
        name: str = "default",
    ) -> None:
        if database_schemas is None:
            declared_attributes = frozenset(attributes or ())
            relations = tuple(input_relations or ())
            if not relations and declared_attributes:
                relations = (Relation("R", declared_attributes, nullable),)
            database_schemas = (
                DatabaseSchema(
                    name,
                    relations,
                    sql_null_dependencies,
                    fds,
                    mvds,
                    inclusion_dependencies,
                    declared_attributes,
                    nullable,
                ),
            )
        object.__setattr__(self, "database_schemas", tuple(database_schemas))

    @property
    def attributes(self) -> AttrSet:
        return frozenset(
            attr
            for database_schema in self.database_schemas
            for attr in database_schema.attributes
        )

    @property
    def nullable(self) -> AttrSet:
        return frozenset(
            attr
            for database_schema in self.database_schemas
            for attr in database_schema.nullable
        )

    @property
    def input_relations(self) -> tuple[Relation, ...]:
        return tuple(
            relation
            for database_schema in self.database_schemas
            for relation in database_schema.relations
        )

    @property
    def sql_null_dependencies(self) -> tuple[SQLNullDependency, ...]:
        return unique_tuple(
            dep
            for database_schema in self.database_schemas
            for dep in database_schema.sql_null_dependencies
        )

    @property
    def fds(self) -> tuple[FD, ...]:
        return unique_tuple(
            dep
            for database_schema in self.database_schemas
            for dep in database_schema.fds
        )

    @property
    def mvds(self) -> tuple[MVD, ...]:
        return unique_tuple(
            dep
            for database_schema in self.database_schemas
            for dep in database_schema.mvds
        )

    @property
    def inclusion_dependencies(self) -> tuple[InclusionDependency, ...]:
        return unique_tuple(
            dep
            for database_schema in self.database_schemas
            for dep in database_schema.inclusion_dependencies
        )


@dataclass
class DatabaseSchemaBuilder:
    name: str
    attributes: AttrSet = frozenset()
    nullable: AttrSet = frozenset()
    input_relations: list[Relation] = field(default_factory=list)
    nullable_by_relation: dict[str, AttrSet] = field(default_factory=dict)
    current_relation_name: str | None = None
    sql_null_dependencies: list[SQLNullDependency] = field(default_factory=list)
    fds: list[FD] = field(default_factory=list)
    mvds: list[MVD] = field(default_factory=list)
    inclusion_dependencies: list[InclusionDependency] = field(default_factory=list)

    def is_empty(self) -> bool:
        return (
            not self.attributes
            and not self.nullable
            and not self.input_relations
            and not self.nullable_by_relation
            and not self.sql_null_dependencies
            and not self.fds
            and not self.mvds
            and not self.inclusion_dependencies
        )

    def build(self) -> DatabaseSchema:
        attributes = self.attributes
        input_relations = self.input_relations
        if input_relations and not attributes:
            attributes = relation_attributes_so_far(attributes, input_relations)
        if not input_relations and attributes:
            input_relations = [Relation("R", attributes)]
        input_relations_tuple = apply_nullable_defaults(
            input_relations,
            self.nullable,
            self.nullable_by_relation,
        )
        nullable = relation_nullable_union(input_relations_tuple)
        return DatabaseSchema(
            self.name,
            input_relations_tuple,
            self.sql_null_dependencies,
            self.fds,
            self.mvds,
            self.inclusion_dependencies,
            attributes,
            nullable,
        )


def fs(values: Iterable[str]) -> AttrSet:
    return frozenset(values)


def normalize_attribute_objects(
    attributes: Iterable[str | Attribute],
    nullable: Iterable[str] = frozenset(),
) -> tuple[Attribute, ...]:
    nullable_names = frozenset(nullable)
    by_name: dict[str, Attribute] = {}
    order: list[str] = []
    if isinstance(attributes, (set, frozenset)):
        values = sorted(
            attributes,
            key=lambda item: item.name if isinstance(item, Attribute) else str(item),
        )
    else:
        values = tuple(attributes)
    for value in values:
        if isinstance(value, Attribute):
            name = value.name
            is_nullable = value.nullable or name in nullable_names
        else:
            name = str(value)
            is_nullable = name in nullable_names

        if name not in by_name:
            order.append(name)
            by_name[name] = Attribute(name, is_nullable)
        elif is_nullable and not by_name[name].nullable:
            by_name[name] = Attribute(name, True)

    return tuple(by_name[name] for name in order)


def fmt_set(values: Iterable[str]) -> str:
    relation = frozenset(values)
    if not relation:
        return "{}"
    if any(len(attr) > 1 for attr in relation):
        return ", ".join(sorted(relation))
    return "".join(sorted(relation))


def fmt_sequence(values: Iterable[str]) -> str:
    sequence = tuple(values)
    if not sequence:
        return "{}"
    if any(len(attr) > 1 for attr in sequence):
        return ", ".join(sequence)
    return "".join(sequence)


def dependency_attrs(dep: FD | MVD) -> AttrSet:
    return dep.lhs | dep.rhs


def sql_null_dependency_attrs(dep: SQLNullDependency) -> AttrSet:
    return frozenset([dep.lhs, dep.rhs])


def inclusion_dependency_attrs(dep: InclusionDependency) -> AttrSet:
    return frozenset(dep.lhs) | frozenset(dep.rhs)


def applicable_fds(relation: AttrSet, fds: Iterable[FD]) -> tuple[FD, ...]:
    return tuple(fd for fd in fds if dependency_attrs(fd) <= relation)


def applicable_mvds(relation: AttrSet, mvds: Iterable[MVD]) -> tuple[MVD, ...]:
    return tuple(mvd for mvd in mvds if dependency_attrs(mvd) <= relation)


def fd_closure(lhs: AttrSet, relation: AttrSet, fds: Iterable[FD]) -> AttrSet:
    closure = set(lhs & relation)
    changed = True
    usable = applicable_fds(relation, fds)
    while changed:
        changed = False
        for fd in usable:
            if fd.lhs <= closure and not fd.rhs <= closure:
                closure |= set(fd.rhs & relation)
                changed = True
    return frozenset(closure)


def is_superkey(lhs: AttrSet, relation: AttrSet, fds: Iterable[FD]) -> bool:
    return relation <= fd_closure(lhs, relation, fds)


def is_fd_nontrivial(fd: FD, relation: AttrSet) -> bool:
    return bool((fd.rhs & relation) - fd.lhs)


def is_mvd_nontrivial(mvd: MVD, relation: AttrSet) -> bool:
    rhs = mvd.rhs & relation
    return bool(rhs - mvd.lhs) and (mvd.lhs | rhs) != relation


def find_4nf_violation(
    relation: AttrSet,
    fds: Iterable[FD],
    mvds: Iterable[MVD],
) -> tuple[str, FD | MVD] | None:
    for fd in applicable_fds(relation, fds):
        if is_fd_nontrivial(fd, relation) and not is_superkey(fd.lhs, relation, fds):
            return ("fd", fd)

    for mvd in applicable_mvds(relation, mvds):
        if is_mvd_nontrivial(mvd, relation) and not is_superkey(mvd.lhs, relation, fds):
            return ("mvd", mvd)

    return None


def decompose_by_dependency(relation: AttrSet, dep: FD | MVD) -> tuple[AttrSet, AttrSet]:
    rhs_inside = dep.rhs & relation
    first = relation & (dep.lhs | rhs_inside)
    second = relation - (rhs_inside - dep.lhs)
    return frozenset(first), frozenset(second)


def normalize_decomposition(relations: Iterable[AttrSet]) -> list[AttrSet]:
    unique = set(relations)
    minimal = [
        relation
        for relation in unique
        if not any(relation < other for other in unique)
    ]
    return sorted(minimal, key=lambda relation: (len(relation), tuple(sorted(relation))))


def sort_relations(relations: Iterable[AttrSet]) -> list[AttrSet]:
    return sorted(set(relations), key=lambda relation: (len(relation), tuple(sorted(relation))))


def unique_tuple(values: Iterable[object]) -> tuple:
    return tuple(dict.fromkeys(values))


def four_nf_decomposition(
    relation: AttrSet,
    fds: Iterable[FD],
    mvds: Iterable[MVD],
) -> tuple[list[AttrSet], list[dict[str, object]]]:
    work = [relation]
    steps: list[dict[str, object]] = []

    changed = True
    while changed:
        changed = False
        next_work: list[AttrSet] = []

        for current in work:
            violation = find_4nf_violation(current, fds, mvds)
            if violation is None:
                next_work.append(current)
                continue

            kind, dep = violation
            left, right = decompose_by_dependency(current, dep)
            steps.append(
                {
                    "relation": sorted(current),
                    "dependency_kind": "FD" if kind == "fd" else "MVD",
                    "dependency": dependency_text(dep, "->" if kind == "fd" else "->>"),
                    "dependency_lhs": sorted(dep.lhs),
                    "dependency_rhs": sorted(dep.rhs),
                    "result": [sorted(left), sorted(right)],
                }
            )
            next_work.extend([left, right])
            changed = True

        work = normalize_decomposition(next_work)

    return normalize_decomposition(work), steps


def dependency_preservation_relations(
    relation: AttrSet,
    fds: Iterable[FD],
    mvds: Iterable[MVD],
) -> tuple[list[AttrSet], list[dict[str, object]]]:
    relations: list[AttrSet] = []
    steps: list[dict[str, object]] = []

    for fd in applicable_fds(relation, fds):
        for attr in sorted((fd.rhs & relation) - fd.lhs):
            dep_relation = frozenset(fd.lhs | {attr})
            relations.append(dep_relation)
            steps.append(
                {
                    "relation": sorted(relation),
                    "dependency_kind": "FD",
                    "dependency": dependency_text(
                        FD(fd.lhs, frozenset([attr])),
                        "->",
                    ),
                    "dependency_lhs": sorted(fd.lhs),
                    "dependency_rhs": [attr],
                    "result": [sorted(dep_relation)],
                    "action": "preserve_dependency",
                }
            )

    for mvd in applicable_mvds(relation, mvds):
        rhs = mvd.rhs & relation
        if not is_mvd_nontrivial(MVD(mvd.lhs, rhs), relation):
            continue
        dep_relation = frozenset(mvd.lhs | rhs)
        relations.append(dep_relation)
        steps.append(
            {
                "relation": sorted(relation),
                "dependency_kind": "MVD",
                "dependency": dependency_text(MVD(mvd.lhs, rhs), "->>"),
                "dependency_lhs": sorted(mvd.lhs),
                "dependency_rhs": sorted(rhs),
                "result": [sorted(dep_relation)],
                "action": "preserve_dependency",
            }
        )

    return relations, steps


def prune_preserving_decomposition(
    relation: AttrSet,
    relations: Iterable[AttrSet],
    protected: Iterable[AttrSet],
    fds: Iterable[FD],
    mvds: Iterable[MVD],
) -> list[AttrSet]:
    current = set(relations)
    protected_set = set(protected)
    analyzer = DependencyAnalyzer(
        DependencySchema(relation, tuple(fds), tuple(mvds))
    )

    def valid(candidate: Iterable[AttrSet]) -> bool:
        decomposition = list(candidate)
        if not relation <= frozenset().union(*decomposition):
            return False
        return (
            analyzer.lossless(decomposition)
            and analyzer.dependency_preserving(decomposition)
        )

    removable = sorted(
        current - protected_set,
        key=lambda rel: (len(rel), tuple(sorted(rel))),
    )
    for candidate in removable:
        trial = current - {candidate}
        if valid(trial):
            current = trial

    return sorted(current, key=lambda rel: (len(rel), tuple(sorted(rel))))


def dependency_preserving_four_nf_decomposition(
    relation: AttrSet,
    fds: Iterable[FD],
    mvds: Iterable[MVD],
) -> tuple[list[AttrSet], list[dict[str, object]]]:
    usable_fds = applicable_fds(relation, fds)
    usable_mvds = applicable_mvds(relation, mvds)
    recursive_4nf, recursive_steps = four_nf_decomposition(
        relation,
        usable_fds,
        usable_mvds,
    )
    preserving_relations, preserving_steps = dependency_preservation_relations(
        relation,
        usable_fds,
        usable_mvds,
    )

    if not preserving_relations:
        return recursive_4nf, recursive_steps

    final = prune_preserving_decomposition(
        relation,
        [*recursive_4nf, *preserving_relations],
        preserving_relations,
        usable_fds,
        usable_mvds,
    )
    existing = {frozenset(step_relation) for step in recursive_steps for step_relation in step["result"]}
    extra_steps = [
        step
        for step in preserving_steps
        if frozenset(step["result"][0]) not in existing
    ]
    return final, [*recursive_steps, *extra_steps]


def dependency_text(dep: FD | MVD, symbol: str) -> str:
    return f"{fmt_set(dep.lhs)} {symbol} {fmt_set(dep.rhs)}"


def dependency_text_for_relation(
    dep: FD | MVD,
    symbol: str,
    relation: Relation | None,
) -> str:
    if isinstance(dep, FD) and relation is not None and dep.rhs == relation.attributes:
        return f"{fmt_set(dep.lhs)} {symbol} att({relation.name})"
    return dependency_text(dep, symbol)


def renamed_dependency_text(
    dep: FD | MVD,
    symbol: str,
    relation_name: str,
) -> str:
    lhs = rename_attributes_for_relation(dep.lhs, relation_name)
    rhs = rename_attributes_for_relation(dep.rhs, relation_name)
    return f"{fmt_set(lhs)} {symbol} {fmt_set(rhs)}"


def renamed_relations_for_relation(
    relations: Iterable[AttrSet],
    relation_name: str,
) -> list[AttrSet]:
    return [
        rename_attributes_for_relation(relation, relation_name)
        for relation in relations
    ]


def renamed_steps_for_relation(
    steps: Iterable[dict[str, object]],
    relation_name: str,
) -> list[dict[str, object]]:
    renamed_steps: list[dict[str, object]] = []

    for step in steps:
        symbol = "->" if step["dependency_kind"] == "FD" else "->>"
        lhs = rename_attributes_for_relation(
            frozenset(step.get("dependency_lhs", [])),
            relation_name,
        )
        rhs = rename_attributes_for_relation(
            frozenset(step.get("dependency_rhs", [])),
            relation_name,
        )
        renamed_steps.append(
            {
                **step,
                "relation": sorted(
                    rename_attributes_for_relation(
                        frozenset(step["relation"]),
                        relation_name,
                    )
                ),
                "dependency": f"{fmt_set(lhs)} {symbol} {fmt_set(rhs)}",
                "dependency_lhs": sorted(lhs),
                "dependency_rhs": sorted(rhs),
                "result": [
                    sorted(
                        rename_attributes_for_relation(
                            frozenset(relation),
                            relation_name,
                        )
                    )
                    for relation in step["result"]
                ],
            }
        )

    return renamed_steps


def sql_null_dependency_text(dep: SQLNullDependency) -> str:
    return f"{dep.lhs} {dependency_symbol(dep.kind)} {dep.rhs}"


def inclusion_dependency_text(dep: InclusionDependency) -> str:
    return f"{fmt_sequence(dep.lhs)} => {fmt_sequence(dep.rhs)}"


def relation_contains_dependency(relation: InputRelation, dep_attrs: AttrSet) -> bool:
    return dep_attrs <= relation.attributes


def relation_nullable_contains_dependency(
    relation: InputRelation,
    dep_attrs: AttrSet,
) -> bool:
    return dep_attrs <= relation.attributes and dep_attrs <= relation.nullable


def containing_relation_names(
    input_relations: Iterable[InputRelation],
    dep_attrs: AttrSet,
) -> list[str]:
    return [
        relation.name
        for relation in input_relations
        if relation_contains_dependency(relation, dep_attrs)
    ]


def nullable_containing_relation_names(
    input_relations: Iterable[InputRelation],
    dep_attrs: AttrSet,
) -> list[str]:
    return [
        relation.name
        for relation in input_relations
        if relation_nullable_contains_dependency(relation, dep_attrs)
    ]


def all_sql_null_dependencies(schema: CombinedSchema) -> tuple[SQLNullDependency, ...]:
    return unique_tuple(
        itertools.chain(
            schema.sql_null_dependencies,
            *(
                relation.sql_null_dependencies
                for relation in schema.input_relations
            ),
        )
    )


def all_fds(schema: CombinedSchema) -> tuple[FD, ...]:
    return unique_tuple(
        itertools.chain(
            schema.fds,
            *(relation.fds for relation in schema.input_relations),
        )
    )


def all_mvds(schema: CombinedSchema) -> tuple[MVD, ...]:
    return unique_tuple(
        itertools.chain(
            schema.mvds,
            *(relation.mvds for relation in schema.input_relations),
        )
    )


def all_inclusion_dependencies(schema: CombinedSchema) -> tuple[InclusionDependency, ...]:
    return unique_tuple(
        itertools.chain(
            schema.inclusion_dependencies,
            *(
                relation.inclusion_dependencies
                for relation in schema.input_relations
            ),
        )
    )


def database_join_dependencies(
    database_schema: DatabaseSchema,
) -> tuple[FD | MVD, ...]:
    return unique_tuple(
        itertools.chain(
            database_schema.fds,
            database_schema.mvds,
            *(
                itertools.chain(relation.fds, relation.mvds)
                for relation in database_schema.relations
            ),
        )
    )


def containing_relation_names_for_sequence(
    input_relations: Iterable[InputRelation],
    attrs: AttrSeq,
) -> list[str]:
    return containing_relation_names(input_relations, frozenset(attrs))


def validate_inclusion_dependency(
    database_schema: DatabaseSchema,
    dep: InclusionDependency,
    *,
    relation_name: str | None = None,
) -> None:
    location = f" in relation {relation_name}" if relation_name else ""
    if not dep.lhs or not dep.rhs:
        raise ValueError(
            f"inclusion dependency {inclusion_dependency_text(dep)}{location} "
            "must have non-empty sides"
        )
    if len(dep.lhs) != len(dep.rhs):
        raise ValueError(
            f"inclusion dependency {inclusion_dependency_text(dep)}{location} "
            "must have the same number of attributes on both sides"
        )

    unknown = inclusion_dependency_attrs(dep) - database_schema.attributes
    if unknown:
        raise ValueError(
            f"inclusion dependency {inclusion_dependency_text(dep)}{location} "
            f"uses unknown attributes: {sorted(unknown)}"
        )

    lhs_relations = containing_relation_names_for_sequence(
        database_schema.relations,
        dep.lhs,
    )
    if not lhs_relations:
        raise ValueError(
            f"inclusion dependency {inclusion_dependency_text(dep)}{location} "
            "has a left side that is not contained in one relation"
        )

    rhs_relations = containing_relation_names_for_sequence(
        database_schema.relations,
        dep.rhs,
    )
    if not rhs_relations:
        raise ValueError(
            f"inclusion dependency {inclusion_dependency_text(dep)}{location} "
            "has a right side that is not contained in one relation"
        )


def validate_combined_schema(schema: CombinedSchema) -> CombinedSchema:
    if not schema.database_schemas:
        raise ValueError("missing database schema declaration")

    schema_names = [database_schema.name for database_schema in schema.database_schemas]
    duplicate_schema_names = sorted(
        name for name in set(schema_names) if schema_names.count(name) > 1
    )
    if duplicate_schema_names:
        raise ValueError(f"duplicate database schema names: {duplicate_schema_names}")

    if not schema.input_relations:
        raise ValueError("missing relation declaration")

    relation_names = [relation.name for relation in schema.input_relations]
    duplicate_names = sorted(
        name for name in set(relation_names) if relation_names.count(name) > 1
    )
    if duplicate_names:
        raise ValueError(f"duplicate relation names: {duplicate_names}")

    for database_schema in schema.database_schemas:
        if not database_schema.relations:
            raise ValueError(
                f"database schema {database_schema.name} has no relations"
            )

        validate_sql_null_schema(
            SQLNullSchema(
                database_schema.attributes,
                database_schema.nullable,
                (),
            )
        )

        for relation in database_schema.relations:
            if not relation.attributes:
                raise ValueError(f"relation {relation.name} has no attributes")
            unknown = relation.attributes - database_schema.attributes
            if unknown:
                raise ValueError(
                    f"relation {relation.name} uses unknown attributes: {sorted(unknown)}"
                )
            non_relation_nullable = relation.nullable - relation.attributes
            if non_relation_nullable:
                raise ValueError(
                    f"relation {relation.name} has nullable attributes outside the "
                    f"relation: {sorted(non_relation_nullable)}"
                )

        for dep in database_schema.sql_null_dependencies:
            dep_attrs = sql_null_dependency_attrs(dep)
            unknown = dep_attrs - database_schema.attributes
            if unknown:
                raise ValueError(
                    f"SQL-null dependency {sql_null_dependency_text(dep)} uses unknown "
                    f"attributes: {sorted(unknown)}"
                )

            if not containing_relation_names(database_schema.relations, dep_attrs):
                raise ValueError(
                    f"SQL-null dependency {sql_null_dependency_text(dep)} is not contained "
                    "in any input relation"
                )

            if not nullable_containing_relation_names(database_schema.relations, dep_attrs):
                names = containing_relation_names(database_schema.relations, dep_attrs)
                raise ValueError(
                    f"SQL-null dependency {sql_null_dependency_text(dep)} is not over "
                    f"nullable attributes of any containing input relation: {names}"
                )

        for relation in database_schema.relations:
            for dep in relation.sql_null_dependencies:
                dep_attrs = sql_null_dependency_attrs(dep)
                unknown = dep_attrs - database_schema.attributes
                if unknown:
                    raise ValueError(
                        f"SQL-null dependency {sql_null_dependency_text(dep)} in relation "
                        f"{relation.name} uses unknown attributes: {sorted(unknown)}"
                    )
                if not relation_contains_dependency(relation, dep_attrs):
                    raise ValueError(
                        f"SQL-null dependency {sql_null_dependency_text(dep)} is not "
                        f"contained in relation {relation.name}"
                    )
                if not relation_nullable_contains_dependency(relation, dep_attrs):
                    raise ValueError(
                        f"SQL-null dependency {sql_null_dependency_text(dep)} is not over "
                        f"nullable attributes of relation {relation.name}"
                    )

            local_sql_deps = tuple(
                dep
                for dep in database_schema.sql_null_dependencies
                if relation_nullable_contains_dependency(
                    relation,
                    sql_null_dependency_attrs(dep),
                )
            )
            local_sql_deps = unique_tuple(
                itertools.chain(local_sql_deps, relation.sql_null_dependencies)
            )
            validate_sql_null_schema(
                SQLNullSchema(
                    relation.attributes,
                    relation.nullable,
                    local_sql_deps,
                    relation.name,
                )
            )

        for dep in itertools.chain(database_schema.fds, database_schema.mvds):
            unknown = dependency_attrs(dep) - database_schema.attributes
            symbol = "->" if isinstance(dep, FD) else "->>"
            if unknown:
                raise ValueError(
                    f"dependency {dependency_text(dep, symbol)} uses unknown attributes: "
                    f"{sorted(unknown)}"
                )

            if not containing_relation_names(database_schema.relations, dependency_attrs(dep)):
                raise ValueError(
                    f"dependency {dependency_text(dep, symbol)} is not contained in any "
                    "input relation"
                )

        for relation in database_schema.relations:
            for dep in itertools.chain(relation.fds, relation.mvds):
                dep_attrs = dependency_attrs(dep)
                symbol = "->" if isinstance(dep, FD) else "->>"
                unknown = dep_attrs - database_schema.attributes
                if unknown:
                    raise ValueError(
                        f"dependency {dependency_text(dep, symbol)} in relation "
                        f"{relation.name} uses unknown attributes: {sorted(unknown)}"
                    )
                if not relation_contains_dependency(relation, dep_attrs):
                    raise ValueError(
                        f"dependency {dependency_text(dep, symbol)} is not contained in "
                        f"relation {relation.name}"
                    )

        for dep in database_schema.inclusion_dependencies:
            validate_inclusion_dependency(database_schema, dep)

        for relation in database_schema.relations:
            for dep in relation.inclusion_dependencies:
                validate_inclusion_dependency(
                    database_schema,
                    dep,
                    relation_name=relation.name,
                )

    return schema


def analyze_input_relation(
    schema: CombinedSchema,
    database_schema: DatabaseSchema,
    input_relation: InputRelation,
) -> dict[str, object]:
    local_sql_deps = tuple(
        dep
        for dep in database_schema.sql_null_dependencies
        if relation_nullable_contains_dependency(
            input_relation,
            sql_null_dependency_attrs(dep),
        )
    )
    local_sql_deps = unique_tuple(
        itertools.chain(local_sql_deps, input_relation.sql_null_dependencies)
    )
    local_fds = unique_tuple(
        itertools.chain(
            applicable_fds(input_relation.attributes, database_schema.fds),
            input_relation.fds,
        )
    )
    local_mvds = unique_tuple(
        itertools.chain(
            applicable_mvds(input_relation.attributes, database_schema.mvds),
            input_relation.mvds,
        )
    )
    sql_schema = SQLNullSchema(
        input_relation.attributes,
        input_relation.nullable,
        local_sql_deps,
        input_relation.name,
    )
    sql_output = analyze_sql_null_schema(sql_schema)
    sql_relations, _ = named_sql_null_decomposition(sql_schema)

    per_relation: list[dict[str, object]] = []
    final_relations: list[AttrSet] = []
    original_final_relations: list[AttrSet] = []

    for sql_relation in sql_relations:
        relation = sql_relation.attributes
        local_relation_fds = applicable_fds(relation, local_fds)
        local_relation_mvds = applicable_mvds(relation, local_mvds)
        local_4nf, steps = dependency_preserving_four_nf_decomposition(
            relation,
            local_relation_fds,
            local_relation_mvds,
        )
        renamed_4nf = renamed_relations_for_relation(local_4nf, sql_relation.name)
        final_relations.extend(renamed_4nf)
        original_final_relations.extend(local_4nf)
        renamed_relation = rename_attributes_for_relation(relation, sql_relation.name)
        renamed_nullable_subset = rename_attributes_for_relation(
            sql_relation.nullable_subset,
            sql_relation.name,
        )
        per_relation.append(
            {
                "input_relation": input_relation.name,
                "sql_null_relation_name": sql_relation.name,
                "sql_null_relation": sorted(relation),
                "renamed_sql_null_relation": sorted(renamed_relation),
                "sql_null_nullable_subset": sorted(sql_relation.nullable_subset),
                "renamed_sql_null_nullable_subset": sorted(renamed_nullable_subset),
                "applicable_fds": [
                    renamed_dependency_text(fd, "->", sql_relation.name)
                    for fd in local_relation_fds
                ],
                "original_applicable_fds": [
                    dependency_text_for_relation(fd, "->", input_relation)
                    for fd in local_relation_fds
                ],
                "applicable_mvds": [
                    renamed_dependency_text(mvd, "->>", sql_relation.name)
                    for mvd in local_relation_mvds
                ],
                "original_applicable_mvds": [
                    dependency_text(mvd, "->>") for mvd in local_relation_mvds
                ],
                "four_nf_decomposition": [sorted(rel) for rel in renamed_4nf],
                "original_four_nf_decomposition": [
                    sorted(rel) for rel in local_4nf
                ],
                "steps": renamed_steps_for_relation(steps, sql_relation.name),
                "original_steps": steps,
            }
        )

    return {
        "database_schema": database_schema.name,
        "input_relation": input_relation.name,
        "attributes": sorted(input_relation.attributes),
        "nullable": sorted(input_relation.nullable),
        "attribute_definitions": [
            {
                "name": attribute.name,
                "nullable": attribute.nullable,
            }
            for attribute in input_relation.attribute_objects
        ],
        "applicable_sql_null_dependencies": [
            sql_null_dependency_text(dep) for dep in local_sql_deps
        ],
        "applicable_fds": [
            dependency_text_for_relation(fd, "->", input_relation)
            for fd in local_fds
        ],
        "applicable_mvds": [dependency_text(mvd, "->>") for mvd in local_mvds],
        "applicable_inclusion_dependencies": [
            inclusion_dependency_text(dep)
            for dep in itertools.chain(
                database_schema.inclusion_dependencies,
                input_relation.inclusion_dependencies,
            )
            if (
                relation_contains_dependency(input_relation, frozenset(dep.lhs))
                or relation_contains_dependency(input_relation, frozenset(dep.rhs))
            )
        ],
        "sql_null_stage": sql_output,
        "per_relation_4nf": per_relation,
        "final_decomposition": [sorted(rel) for rel in sort_relations(final_relations)],
        "original_final_decomposition": [
            sorted(rel) for rel in sort_relations(original_final_relations)
        ],
    }


def analyze_combined_schema(schema: CombinedSchema) -> dict[str, object]:
    validate_combined_schema(schema)

    per_input_relation = [
        analyze_input_relation(schema, database_schema, relation)
        for database_schema in schema.database_schemas
        for relation in database_schema.relations
    ]
    final_relations = [
        frozenset(relation)
        for item in per_input_relation
        for relation in item["final_decomposition"]
    ]
    original_final_relations = [
        frozenset(relation)
        for item in per_input_relation
        for relation in item["original_final_decomposition"]
    ]
    first_relation = per_input_relation[0]

    return {
        "attributes": sorted(schema.attributes),
        "nullable": sorted(schema.nullable),
        "database_schemas": [
            {
                "name": database_schema.name,
                "attributes": sorted(database_schema.attributes),
                "nullable": sorted(database_schema.nullable),
                "relations": [
                    {
                        "name": relation.name,
                        "attributes": sorted(relation.attributes),
                        "nullable": sorted(relation.nullable),
                        "attribute_definitions": [
                            {
                                "name": attribute.name,
                                "nullable": attribute.nullable,
                            }
                            for attribute in relation.attribute_objects
                        ],
                    }
                    for relation in database_schema.relations
                ],
                "sql_null_dependencies": [
                    {
                        "kind": dep.kind,
                        "lhs": dep.lhs,
                        "rhs": dep.rhs,
                        "text": sql_null_dependency_text(dep),
                    }
                    for dep in database_schema.sql_null_dependencies
                ],
                "fds": [
                    dependency_text(fd, "->") for fd in database_schema.fds
                ],
                "mvds": [
                    dependency_text(mvd, "->>") for mvd in database_schema.mvds
                ],
                "inclusion_dependencies": [
                    {
                        "lhs": list(dep.lhs),
                        "rhs": list(dep.rhs),
                        "text": inclusion_dependency_text(dep),
                    }
                    for dep in database_schema.inclusion_dependencies
                ],
            }
            for database_schema in schema.database_schemas
        ],
        "input_relations": [
            {
                "name": relation.name,
                "attributes": sorted(relation.attributes),
                "nullable": sorted(relation.nullable),
            }
            for relation in schema.input_relations
        ],
        "sql_null_dependencies": [
            {
                "kind": dep.kind,
                "lhs": dep.lhs,
                "rhs": dep.rhs,
                "text": sql_null_dependency_text(dep),
            }
            for dep in all_sql_null_dependencies(schema)
        ],
        "fds": [dependency_text(fd, "->") for fd in all_fds(schema)],
        "mvds": [dependency_text(mvd, "->>") for mvd in all_mvds(schema)],
        "join_dependencies": [
            {
                "kind": "FD",
                "lhs": sorted(fd.lhs),
                "rhs": sorted(fd.rhs),
                "text": dependency_text(fd, "->"),
            }
            for fd in all_fds(schema)
        ]
        + [
            {
                "kind": "MVD",
                "lhs": sorted(mvd.lhs),
                "rhs": sorted(mvd.rhs),
                "text": dependency_text(mvd, "->>"),
            }
            for mvd in all_mvds(schema)
        ],
        "inclusion_dependencies": [
            {
                "lhs": list(dep.lhs),
                "rhs": list(dep.rhs),
                "text": inclusion_dependency_text(dep),
            }
            for dep in all_inclusion_dependencies(schema)
        ],
        "per_input_relation": per_input_relation,
        "sql_null_stage": first_relation["sql_null_stage"],
        "per_relation_4nf": first_relation["per_relation_4nf"],
        "final_decomposition": [
            sorted(rel) for rel in sort_relations(final_relations)
        ],
        "original_final_decomposition": [
            sorted(rel) for rel in sort_relations(original_final_relations)
        ],
    }


def parse_attribute_set_with_known(
    text: str,
    known_attributes: AttrSet,
    line_no: int,
    *,
    allow_empty: bool,
) -> AttrSet:
    value = text.strip()
    if value in known_attributes:
        parsed = frozenset([value])
    else:
        parsed = parse_attribute_list(value)
    if not parsed and not allow_empty:
        raise ValueError(f"line {line_no}: dependency side must be non-empty")
    unknown = parsed - known_attributes
    if known_attributes and unknown:
        raise ValueError(f"line {line_no}: unknown attributes {sorted(unknown)}")
    return parsed


def parse_attribute_sequence_with_known(
    text: str,
    known_attributes: AttrSet,
    line_no: int,
    *,
    allow_empty: bool,
) -> AttrSeq:
    value = text.strip()
    if not value or value in {"{}", "∅"}:
        parsed: AttrSeq = ()
    elif value in known_attributes:
        parsed = (value,)
    else:
        value = value.strip("{}[]()")
        if "," in value or re.search(r"\s", value):
            parsed = tuple(token for token in re.split(r"[\s,]+", value) if token)
        else:
            parsed = tuple(value)

    if not parsed and not allow_empty:
        raise ValueError(f"line {line_no}: dependency side must be non-empty")
    unknown = frozenset(parsed) - known_attributes
    if known_attributes and unknown:
        raise ValueError(f"line {line_no}: unknown attributes {sorted(unknown)}")
    return parsed


def parse_dep_attribute_set(text: str, known_attributes: AttrSet, line_no: int) -> AttrSet:
    return parse_attribute_set_with_known(
        text,
        known_attributes,
        line_no,
        allow_empty=False,
    )


def parse_single_attr(text: str, known_attributes: AttrSet, line_no: int) -> str:
    parsed = parse_dep_attribute_set(text, known_attributes, line_no)
    if len(parsed) != 1:
        raise ValueError(f"line {line_no}: SQL-null dependency sides must be single attributes")
    return next(iter(parsed))


def parse_database_schema_declaration(line: str) -> str | None:
    patterns = [
        r"^(?:database\s+schema|dbschema|database|db)\s+([A-Za-z][\w-]*)\s*:?\s*$",
        r"^(?:database\s+schema|dbschema|database|db)\s*:\s*([A-Za-z][\w-]*)\s*$",
        r"^schema\s+([A-Za-z][\w-]*)\s*:?\s*$",
    ]
    for pattern in patterns:
        match = re.match(pattern, line, re.I)
        if match:
            return match.group(1)
    return None


def parse_att_reference(text: str) -> str | None:
    match = re.match(r"^att\s*\(\s*([A-Za-z][\w-]*)\s*\)$", text.strip(), re.I)
    if match:
        return match.group(1)
    return None


def parse_dep_rhs_attribute_set(
    text: str,
    known_attributes: AttrSet,
    input_relations: Sequence[InputRelation],
    line_no: int,
) -> AttrSet:
    relation_name = parse_att_reference(text)
    if relation_name is not None:
        relation = find_input_relation(input_relations, relation_name)
        if relation is None:
            raise ValueError(f"line {line_no}: unknown relation {relation_name!r}")
        return relation.attributes

    return parse_dep_attribute_set(text, known_attributes, line_no)


def relation_attributes_so_far(
    attributes: AttrSet,
    input_relations: Sequence[InputRelation],
) -> AttrSet:
    if attributes:
        return attributes
    return frozenset(
        attr
        for relation in input_relations
        for attr in relation.attributes
    )


def parse_relation_declaration(
    line: str,
    known_attributes: AttrSet,
    line_no: int,
    relation_index: int,
) -> InputRelation | None:
    patterns = [
        r"^(?:relation|rel)\s+([A-Za-z][\w-]*)\s*:\s*(.+)$",
        r"^(?:relation|rel)\s+([A-Za-z][\w-]*)\s*\((.*?)\)\s*$",
        r"^(?:relation|rel)\s*:\s*([A-Za-z][\w-]*)\s*\((.*?)\)\s*$",
    ]
    for pattern in patterns:
        match = re.match(pattern, line, re.I)
        if match:
            name = match.group(1)
            attrs_text = match.group(2)
            break
    else:
        match = re.match(r"^(?:relation|rel)\s*:\s*(.+)$", line, re.I)
        if not match:
            return None
        name = f"R{relation_index}"
        attrs_text = match.group(1)

    attrs = parse_attribute_list(attrs_text)
    if not attrs:
        raise ValueError(f"line {line_no}: relation {name} must have attributes")
    unknown = attrs - known_attributes
    if known_attributes and unknown:
        raise ValueError(
            f"line {line_no}: relation {name} uses unknown attributes: {sorted(unknown)}"
        )
    return InputRelation(name, attrs)


def find_input_relation(
    input_relations: Sequence[InputRelation],
    name: str,
) -> InputRelation | None:
    for relation in input_relations:
        if relation.name == name:
            return relation
    return None


def replace_input_relation(
    input_relations: list[InputRelation],
    updated: InputRelation,
) -> None:
    for index, relation in enumerate(input_relations):
        if relation.name == updated.name:
            input_relations[index] = updated
            return
    raise ValueError(f"unknown relation {updated.name!r}")


def set_relation_nullable(
    input_relations: list[InputRelation],
    name: str,
    nullable: AttrSet,
) -> None:
    relation = find_input_relation(input_relations, name)
    if relation is None:
        raise ValueError(f"unknown relation {name!r}")
    replace_input_relation(
        input_relations,
        InputRelation(
            relation.name,
            relation.attributes,
            nullable,
            relation.sql_null_dependencies,
            relation.fds,
            relation.mvds,
            relation.inclusion_dependencies,
        ),
    )


def add_relation_sql_null_dependency(
    input_relations: list[InputRelation],
    name: str,
    dependency: SQLNullDependency,
) -> None:
    relation = find_input_relation(input_relations, name)
    if relation is None:
        raise ValueError(f"unknown relation {name!r}")
    replace_input_relation(
        input_relations,
        InputRelation(
            relation.name,
            relation.attributes,
            relation.nullable,
            relation.sql_null_dependencies + (dependency,),
            relation.fds,
            relation.mvds,
            relation.inclusion_dependencies,
        ),
    )


def add_relation_fd(
    input_relations: list[InputRelation],
    name: str,
    dependency: FD,
) -> None:
    relation = find_input_relation(input_relations, name)
    if relation is None:
        raise ValueError(f"unknown relation {name!r}")
    replace_input_relation(
        input_relations,
        InputRelation(
            relation.name,
            relation.attributes,
            relation.nullable,
            relation.sql_null_dependencies,
            relation.fds + (dependency,),
            relation.mvds,
            relation.inclusion_dependencies,
        ),
    )


def add_relation_mvd(
    input_relations: list[InputRelation],
    name: str,
    dependency: MVD,
) -> None:
    relation = find_input_relation(input_relations, name)
    if relation is None:
        raise ValueError(f"unknown relation {name!r}")
    replace_input_relation(
        input_relations,
        InputRelation(
            relation.name,
            relation.attributes,
            relation.nullable,
            relation.sql_null_dependencies,
            relation.fds,
            relation.mvds + (dependency,),
            relation.inclusion_dependencies,
        ),
    )


def add_relation_inclusion_dependency(
    input_relations: list[InputRelation],
    name: str,
    dependency: InclusionDependency,
) -> None:
    relation = find_input_relation(input_relations, name)
    if relation is None:
        raise ValueError(f"unknown relation {name!r}")
    replace_input_relation(
        input_relations,
        InputRelation(
            relation.name,
            relation.attribute_objects,
            relation.nullable,
            relation.sql_null_dependencies,
            relation.fds,
            relation.mvds,
            relation.inclusion_dependencies + (dependency,),
        ),
    )


def parse_relation_nullable_declaration(
    line: str,
    input_relations: Sequence[InputRelation],
    line_no: int,
) -> tuple[str, AttrSet] | None:
    patterns = [
        r"^(?:nullable|sql-nullable|nulls)\s+([A-Za-z][\w-]*)\s*:\s*(.*)$",
        r"^(?:nullable|sql-nullable|nulls)\s*\(\s*([A-Za-z][\w-]*)\s*\)\s*:\s*(.*)$",
        r"^([A-Za-z][\w-]*)\s+(?:nullable|sql-nullable|nulls)\s*:\s*(.*)$",
    ]
    for pattern in patterns:
        match = re.match(pattern, line, re.I)
        if not match:
            continue

        name = match.group(1)
        relation = find_input_relation(input_relations, name)
        if relation is None:
            raise ValueError(f"line {line_no}: unknown relation {name!r}")
        nullable = parse_attribute_set_with_known(
            match.group(2),
            relation.attributes,
            line_no,
            allow_empty=True,
        )
        return name, nullable

    return None


def relation_nullable_union(input_relations: Sequence[InputRelation]) -> AttrSet:
    return frozenset(
        attr
        for relation in input_relations
        for attr in relation.nullable
    )


def apply_nullable_defaults(
    input_relations: Sequence[InputRelation],
    default_nullable: AttrSet,
    nullable_by_relation: dict[str, AttrSet],
) -> tuple[InputRelation, ...]:
    return tuple(
        InputRelation(
            relation.name,
            relation.attributes,
            nullable_by_relation.get(
                relation.name,
                relation.nullable | (default_nullable & relation.attributes),
            ),
            relation.sql_null_dependencies,
            relation.fds,
            relation.mvds,
            relation.inclusion_dependencies,
        )
        for relation in input_relations
    )


def schema_from_text(text: str) -> CombinedSchema:
    builders: list[DatabaseSchemaBuilder] = []
    current_builder: DatabaseSchemaBuilder | None = None

    def builder() -> DatabaseSchemaBuilder:
        nonlocal current_builder
        if current_builder is None:
            current_builder = DatabaseSchemaBuilder("default")
            builders.append(current_builder)
        return current_builder

    def start_database_schema(name: str) -> None:
        nonlocal current_builder
        if current_builder is None:
            current_builder = DatabaseSchemaBuilder(name)
            builders.append(current_builder)
            return
        if current_builder.name == "default" and current_builder.is_empty():
            current_builder.name = name
            return
        current_builder = DatabaseSchemaBuilder(name)
        builders.append(current_builder)

    for line_no, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.split("#", 1)[0].split("--", 1)[0].strip()
        if not line:
            continue

        database_schema_name = parse_database_schema_declaration(line)
        if database_schema_name is not None:
            start_database_schema(database_schema_name)
            continue

        current = builder()

        attrs_match = re.match(r"^(?:attributes|attrs|schema)\s*:\s*(.+)$", line, re.I)
        if attrs_match:
            current.attributes = parse_attribute_list(attrs_match.group(1))
            continue

        relation = parse_relation_declaration(
            line,
            current.attributes,
            line_no,
            len(current.input_relations) + 1,
        )
        if relation is not None:
            current.input_relations.append(relation)
            current.current_relation_name = relation.name
            continue

        known_attributes = relation_attributes_so_far(
            current.attributes,
            current.input_relations,
        )

        relation_nullable = parse_relation_nullable_declaration(
            line,
            current.input_relations,
            line_no,
        )
        if relation_nullable is not None:
            name, relation_nullable_attrs = relation_nullable
            current.nullable_by_relation[name] = relation_nullable_attrs
            if current.current_relation_name == name:
                set_relation_nullable(
                    current.input_relations,
                    name,
                    relation_nullable_attrs,
                )
            continue

        nullable_match = re.match(r"^(?:nullable|sql-nullable|nulls)\s*:\s*(.*)$", line, re.I)
        if nullable_match:
            if not known_attributes:
                raise ValueError(
                    f"line {line_no}: attributes or relation line must appear before nullable"
                )
            if current.current_relation_name is not None:
                current_relation = find_input_relation(
                    current.input_relations,
                    current.current_relation_name,
                )
                if current_relation is None:
                    raise ValueError(
                        f"line {line_no}: unknown relation {current.current_relation_name!r}"
                    )
                relation_nullable_attrs = parse_attribute_set_with_known(
                    nullable_match.group(1),
                    current_relation.attributes,
                    line_no,
                    allow_empty=True,
                )
                set_relation_nullable(
                    current.input_relations,
                    current.current_relation_name,
                    relation_nullable_attrs,
                )
                current.nullable_by_relation[current.current_relation_name] = (
                    relation_nullable_attrs
                )
            else:
                current.nullable = parse_attribute_set_with_known(
                    nullable_match.group(1),
                    known_attributes,
                    line_no,
                    allow_empty=True,
                )
            continue

        sql_dep_match = re.match(r"^(.*?)\s*(<-N->|->N<-|-N->)\s*(.*?)$", line)
        if sql_dep_match:
            if not known_attributes:
                raise ValueError(
                    f"line {line_no}: attributes or relation line must appear before dependencies"
                )
            local_attributes = known_attributes
            if current.current_relation_name is not None:
                current_relation = find_input_relation(
                    current.input_relations,
                    current.current_relation_name,
                )
                if current_relation is None:
                    raise ValueError(
                        f"line {line_no}: unknown relation {current.current_relation_name!r}"
                    )
                local_attributes = current_relation.attributes

            lhs = parse_single_attr(sql_dep_match.group(1), local_attributes, line_no)
            rhs = parse_single_attr(sql_dep_match.group(3), local_attributes, line_no)
            symbol = sql_dep_match.group(2)
            if symbol == "<-N->":
                kind = "jointly_sql_null"
            elif symbol == "->N<-":
                kind = "alternative_sql_null"
            else:
                kind = "implies_sql_null"
            dep = SQLNullDependency(kind, lhs, rhs)
            if current.current_relation_name is not None:
                add_relation_sql_null_dependency(
                    current.input_relations,
                    current.current_relation_name,
                    dep,
                )
            else:
                current.sql_null_dependencies.append(dep)
            continue

        inclusion_match = re.match(r"^(.*?)\s*=>\s*(.*?)$", line)
        if inclusion_match:
            if not known_attributes:
                raise ValueError(
                    f"line {line_no}: attributes or relation line must appear before dependencies"
                )
            lhs = parse_attribute_sequence_with_known(
                inclusion_match.group(1),
                known_attributes,
                line_no,
                allow_empty=False,
            )
            rhs = parse_attribute_sequence_with_known(
                inclusion_match.group(2),
                known_attributes,
                line_no,
                allow_empty=False,
            )
            current.inclusion_dependencies.append(InclusionDependency(lhs, rhs))
            continue

        fd_mvd_match = re.match(r"^(.*?)\s*(->>|↠|-->>|->)\s*(.*?)$", line)
        if fd_mvd_match:
            if not known_attributes:
                raise ValueError(
                    f"line {line_no}: attributes or relation line must appear before dependencies"
                )
            local_attributes = known_attributes
            if current.current_relation_name is not None:
                current_relation = find_input_relation(
                    current.input_relations,
                    current.current_relation_name,
                )
                if current_relation is None:
                    raise ValueError(
                        f"line {line_no}: unknown relation {current.current_relation_name!r}"
                    )
                local_attributes = current_relation.attributes

            lhs = parse_dep_attribute_set(fd_mvd_match.group(1), local_attributes, line_no)
            rhs = parse_dep_rhs_attribute_set(
                fd_mvd_match.group(3),
                local_attributes,
                current.input_relations,
                line_no,
            )
            if fd_mvd_match.group(2) in {"->>", "↠", "-->>"}:
                dep = MVD(lhs, rhs)
                if current.current_relation_name is not None:
                    add_relation_mvd(
                        current.input_relations,
                        current.current_relation_name,
                        dep,
                    )
                else:
                    current.mvds.append(dep)
            else:
                dep = FD(lhs, rhs)
                if current.current_relation_name is not None:
                    add_relation_fd(
                        current.input_relations,
                        current.current_relation_name,
                        dep,
                    )
                else:
                    current.fds.append(dep)
            continue

        raise ValueError(
            f"line {line_no}: expected database schema, attributes, relation, "
            "nullable, SQL-null dependency, FD, MVD, or inclusion dependency"
        )

    if not builders:
        raise ValueError("missing attributes or relation line")

    return validate_combined_schema(
        CombinedSchema(
            database_schemas=tuple(builder.build() for builder in builders),
        )
    )


def parse_json_attr_set(value: object) -> AttrSet:
    if isinstance(value, str):
        return parse_attribute_list(value)
    if isinstance(value, list):
        return frozenset(
            str(attr.get("name", ""))
            if isinstance(attr, dict)
            else str(attr)
            for attr in value
        )
    raise ValueError(f"dependency side must be a string or list, got {type(value).__name__}")


def parse_json_attributes(value: object) -> tuple[Attribute, ...]:
    if isinstance(value, str):
        return tuple(Attribute(attr) for attr in sorted(parse_attribute_list(value)))
    if isinstance(value, list):
        attributes: list[Attribute] = []
        for item in value:
            if isinstance(item, dict):
                name = str(item.get("name", "")).strip()
                nullable = bool(item.get("nullable", False))
                attributes.append(Attribute(name, nullable))
            else:
                attributes.append(Attribute(str(item)))
        return tuple(attributes)
    raise ValueError(
        f"attributes must be a string or list, got {type(value).__name__}"
    )


def parse_json_attr_sequence(value: object) -> AttrSeq:
    if isinstance(value, str):
        return parse_attribute_sequence_with_known(
            value,
            frozenset(),
            0,
            allow_empty=False,
        )
    if isinstance(value, list):
        return tuple(
            str(attr.get("name", ""))
            if isinstance(attr, dict)
            else str(attr)
            for attr in value
        )
    raise ValueError(
        f"inclusion dependency side must be a string or list, got {type(value).__name__}"
    )


def parse_json_sql_null_dependencies(data: dict[str, object]) -> list[SQLNullDependency]:
    sql_null_dependencies: list[SQLNullDependency] = []

    for dep in data.get("implies_sql_null", []):
        sql_null_dependencies.append(
            SQLNullDependency("implies_sql_null", str(dep["lhs"]), str(dep["rhs"]))
        )

    for dep in data.get("jointly_sql_null", []):
        sql_null_dependencies.append(
            SQLNullDependency("jointly_sql_null", str(dep["lhs"]), str(dep["rhs"]))
        )

    for dep in data.get("alternative_sql_null", []):
        sql_null_dependencies.append(
            SQLNullDependency("alternative_sql_null", str(dep["lhs"]), str(dep["rhs"]))
        )

    for dep in data.get("alternative", []):
        sql_null_dependencies.append(
            SQLNullDependency("alternative_sql_null", str(dep["lhs"]), str(dep["rhs"]))
        )

    return sql_null_dependencies


def parse_json_inclusion_dependencies(data: dict[str, object]) -> tuple[InclusionDependency, ...]:
    dependencies: list[InclusionDependency] = []
    raw_dependencies = data.get(
        "inclusion_dependencies",
        data.get("inclusions", data.get("inds", [])),
    )
    for dep in raw_dependencies:
        dependencies.append(
            InclusionDependency(
                parse_json_attr_sequence(dep["lhs"]),
                parse_json_attr_sequence(dep["rhs"]),
            )
        )
    return tuple(dependencies)


def parse_json_dep_rhs_attr_set(
    value: object,
    relations: Sequence[Relation],
    default_relation: Relation | None = None,
) -> AttrSet:
    if isinstance(value, str):
        relation_name = parse_att_reference(value)
        if relation_name is not None:
            relation = find_input_relation(relations, relation_name)
            if relation is None and default_relation is not None:
                if default_relation.name == relation_name:
                    relation = default_relation
            if relation is None:
                raise ValueError(f"unknown relation {relation_name!r}")
            return relation.attributes
    return parse_json_attr_set(value)


def parse_json_database_schema(
    data: dict[str, object],
    default_name: str,
) -> DatabaseSchema:
    schema_name = str(
        data.get(
            "name",
            data.get("database_schema", data.get("schema", default_name)),
        )
    )
    attributes = parse_json_attr_set(data.get("attributes", []))
    input_relations: list[InputRelation] = []
    nullable_by_relation: dict[str, AttrSet] = {}

    for index, relation in enumerate(data.get("relations", []), start=1):
        if isinstance(relation, dict):
            name = str(relation.get("name", f"R{index}"))
            attrs = parse_json_attributes(relation.get("attributes", []))
            local_nullable = parse_json_attr_set(relation.get("nullable", []))
            if "nullable" in relation:
                nullable_by_relation[name] = local_nullable
            local_sql_null_dependencies = parse_json_sql_null_dependencies(relation)
            relation_stub = Relation(name, attrs, local_nullable)
            local_fds = tuple(
                FD(
                    parse_json_attr_set(dep["lhs"]),
                    parse_json_dep_rhs_attr_set(
                        dep["rhs"],
                        input_relations,
                        relation_stub,
                    ),
                )
                for dep in relation.get("fds", [])
            )
            local_mvds = tuple(
                MVD(
                    parse_json_attr_set(dep["lhs"]),
                    parse_json_dep_rhs_attr_set(
                        dep["rhs"],
                        input_relations,
                        relation_stub,
                    ),
                )
                for dep in relation.get("mvds", [])
            )
            local_inclusion_dependencies = parse_json_inclusion_dependencies(relation)
        else:
            name = f"R{index}"
            attrs = parse_json_attributes(relation)
            local_nullable = frozenset()
            local_sql_null_dependencies = []
            local_fds = ()
            local_mvds = ()
            local_inclusion_dependencies = ()
        input_relations.append(
            InputRelation(
                name,
                attrs,
                local_nullable,
                tuple(local_sql_null_dependencies),
                local_fds,
                local_mvds,
                local_inclusion_dependencies,
            )
        )

    if input_relations and not attributes:
        attributes = relation_attributes_so_far(attributes, input_relations)

    if not input_relations and attributes:
        input_relations.append(InputRelation("R", attributes))

    nullable = parse_json_attr_set(data.get("nullable", []))
    input_relations = list(
        apply_nullable_defaults(
            input_relations,
            nullable,
            nullable_by_relation,
        )
    )
    nullable = relation_nullable_union(input_relations)
    sql_null_dependencies = parse_json_sql_null_dependencies(data)

    fds = tuple(
        FD(
            parse_json_attr_set(dep["lhs"]),
            parse_json_dep_rhs_attr_set(dep["rhs"], input_relations),
        )
        for dep in data.get("fds", [])
    )
    mvds = tuple(
        MVD(
            parse_json_attr_set(dep["lhs"]),
            parse_json_dep_rhs_attr_set(dep["rhs"], input_relations),
        )
        for dep in data.get("mvds", [])
    )
    inclusion_dependencies = parse_json_inclusion_dependencies(data)

    return DatabaseSchema(
        schema_name,
        input_relations,
        sql_null_dependencies,
        fds,
        mvds,
        inclusion_dependencies,
        attributes,
        nullable,
    )


def schema_from_json(data: dict[str, object]) -> CombinedSchema:
    raw_schemas = data.get("database_schemas", data.get("schemas"))
    if raw_schemas is not None:
        if not isinstance(raw_schemas, list):
            raise ValueError("database_schemas must be a list")
        database_schemas = tuple(
            parse_json_database_schema(
                item,
                f"S{index}",
            )
            for index, item in enumerate(raw_schemas, start=1)
        )
    else:
        database_schemas = (
            parse_json_database_schema(data, "default"),
        )

    return validate_combined_schema(
        CombinedSchema(
            database_schemas=database_schemas,
        )
    )


def load_schema(path: str) -> CombinedSchema:
    with open(path, "r", encoding="utf-8") as file:
        content = file.read()
    if path.lower().endswith(".json"):
        return schema_from_json(json.loads(content))
    return schema_from_text(content)


def main(argv: Sequence[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("schema_file")
    args = parser.parse_args(argv)

    print(json.dumps(analyze_combined_schema(load_schema(args.schema_file)), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

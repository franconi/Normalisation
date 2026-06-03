#!/usr/bin/env python3
"""
Check the Yuan-Ozsoyoglu extended conflict-free condition for a finite
schema with FDs and MVDs, and synthesize a lossless dependency-preserving
4NF decomposition when the condition holds.

Input JSON format:

{
  "attributes": ["A", "B", "C"],
  "fds":  [{"lhs": ["A", "B"], "rhs": ["C"]}],
  "mvds": [{"lhs": ["A"], "rhs": ["B"]}]
}

Run:

  python3 fd_mvd_normalizer.py schema.json

Notes:
  * Implication tests use a finite chase for FDs, MVDs, and JDs.
  * The extended conflict-free check follows Definitions 4.1--4.3 of
    Yuan and Ozsoyoglu's PODS 1987 paper.
  * The decomposition synthesizer is exact but exhaustive. It is intended
    for small schemas, which is normally enough for examples and proofs.
"""

from __future__ import annotations

import argparse
import itertools
import json
import re
import sys
from dataclasses import dataclass
from typing import Iterable, Sequence


AttrSet = frozenset[str]
Row = tuple[str, ...]
JD = tuple[AttrSet, ...]


@dataclass(frozen=True)
class FD:
    lhs: AttrSet
    rhs: AttrSet


@dataclass(frozen=True)
class MVD:
    lhs: AttrSet
    rhs: AttrSet


@dataclass
class Schema:
    attrs: AttrSet
    fds: tuple[FD, ...]
    mvds: tuple[MVD, ...]

    @property
    def lhs_sets(self) -> set[AttrSet]:
        return {d.lhs for d in (*self.fds, *self.mvds)}


class ChaseTooLarge(RuntimeError):
    pass


class UnionFind:
    def __init__(self) -> None:
        self.parent: dict[str, str] = {}

    def find(self, x: str) -> str:
        self.parent.setdefault(x, x)
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])
        return self.parent[x]

    def union(self, a: str, b: str) -> bool:
        ra, rb = self.find(a), self.find(b)
        if ra == rb:
            return False
        if rb < ra:
            ra, rb = rb, ra
        self.parent[rb] = ra
        return True


def fs(values: Iterable[str]) -> AttrSet:
    return frozenset(values)


def powerset(s: Iterable[str], *, include_empty: bool = True) -> list[AttrSet]:
    items = sorted(s)
    out: list[AttrSet] = []
    start = 0 if include_empty else 1
    for r in range(start, len(items) + 1):
        for combo in itertools.combinations(items, r):
            out.append(frozenset(combo))
    return out


def fmt_set(s: AttrSet) -> str:
    return "".join(sorted(s)) or "{}"


class Chaser:
    def __init__(self, attrs: Iterable[str], max_rows: int = 4096) -> None:
        self.attrs = tuple(sorted(attrs))
        self.pos = {a: i for i, a in enumerate(self.attrs)}
        self.max_rows = max_rows

    def canonical_row(self, row: Row, uf: UnionFind) -> Row:
        return tuple(uf.find(v) for v in row)

    def canonical_rows(self, rows: set[Row], uf: UnionFind) -> set[Row]:
        return {self.canonical_row(r, uf) for r in rows}

    def agree(self, r1: Row, r2: Row, attrs: AttrSet, uf: UnionFind) -> bool:
        return all(
            uf.find(r1[self.pos[a]]) == uf.find(r2[self.pos[a]]) for a in attrs
        )

    def chase(
        self,
        initial_rows: Iterable[Row],
        fds: Sequence[FD],
        mvds: Sequence[MVD],
        jds: Sequence[JD] = (),
    ) -> tuple[set[Row], UnionFind]:
        uf = UnionFind()
        rows = {tuple(row) for row in initial_rows}

        # Treat each MVD X ->> Y as the binary join dependency
        # *(X union Y, X union (U - Y)).
        all_jds: list[JD] = list(jds)
        universe = frozenset(self.attrs)
        for mvd in mvds:
            all_jds.append(
                (
                    frozenset(mvd.lhs | mvd.rhs),
                    frozenset(mvd.lhs | (universe - mvd.rhs)),
                )
            )

        changed = True
        while changed:
            changed = False
            rows = self.canonical_rows(rows, uf)
            if len(rows) > self.max_rows:
                raise ChaseTooLarge(f"chase exceeded {self.max_rows} rows")

            row_list = list(rows)

            for fd in fds:
                for r1 in row_list:
                    for r2 in row_list:
                        if not self.agree(r1, r2, fd.lhs, uf):
                            continue
                        for a in fd.rhs:
                            changed |= uf.union(r1[self.pos[a]], r2[self.pos[a]])

            if changed:
                continue

            for jd in all_jds:
                if not jd:
                    continue
                for chosen in itertools.product(row_list, repeat=len(jd)):
                    merged: list[str | None] = [None] * len(self.attrs)
                    ok = True
                    for comp, row in zip(jd, chosen):
                        for a in comp:
                            i = self.pos[a]
                            value = uf.find(row[i])
                            if merged[i] is None:
                                merged[i] = value
                            elif merged[i] != value:
                                ok = False
                                break
                        if not ok:
                            break
                    if not ok or any(v is None for v in merged):
                        continue
                    new_row = tuple(v for v in merged if v is not None)
                    if new_row not in rows:
                        rows.add(new_row)
                        changed = True

        return self.canonical_rows(rows, uf), uf

    def two_row_tableau(self, x: AttrSet) -> tuple[Row, Row]:
        r0: list[str] = []
        r1: list[str] = []
        for a in self.attrs:
            if a in x:
                r0.append(f"x_{a}")
                r1.append(f"x_{a}")
            else:
                r0.append(f"r0_{a}")
                r1.append(f"r1_{a}")
        return tuple(r0), tuple(r1)

    def jd_tableau(self, jd: JD) -> list[Row]:
        rows: list[Row] = []
        for i, comp in enumerate(jd):
            row = []
            for a in self.attrs:
                row.append(f"a_{a}" if a in comp else f"b{i}_{a}")
            rows.append(tuple(row))
        return rows

    def implies_fd(
        self,
        fds: Sequence[FD],
        mvds: Sequence[MVD],
        lhs: AttrSet,
        rhs: AttrSet,
        jds: Sequence[JD] = (),
    ) -> bool:
        if rhs <= lhs:
            return True
        r0, r1 = self.two_row_tableau(lhs)
        rows, uf = self.chase([r0, r1], fds, mvds, jds)
        c0, c1 = self.canonical_row(r0, uf), self.canonical_row(r1, uf)
        return all(c0[self.pos[a]] == c1[self.pos[a]] for a in rhs)

    def implies_mvd(
        self,
        fds: Sequence[FD],
        mvds: Sequence[MVD],
        lhs: AttrSet,
        rhs: AttrSet,
        jds: Sequence[JD] = (),
    ) -> bool:
        universe = frozenset(self.attrs)
        if rhs <= lhs or lhs | rhs == universe:
            return True
        r0, r1 = self.two_row_tableau(lhs)
        rows, uf = self.chase([r0, r1], fds, mvds, jds)
        c0, c1 = self.canonical_row(r0, uf), self.canonical_row(r1, uf)
        target = []
        for a in self.attrs:
            if a in lhs or a in rhs:
                target.append(c0[self.pos[a]])
            else:
                target.append(c1[self.pos[a]])
        return tuple(target) in rows

    def implies_jd(
        self,
        fds: Sequence[FD],
        mvds: Sequence[MVD],
        jd: JD,
        jds: Sequence[JD] = (),
    ) -> bool:
        rows0 = self.jd_tableau(jd)
        rows, uf = self.chase(rows0, fds, mvds, jds)
        distinguished = tuple(f"a_{a}" for a in self.attrs)
        distinguished = self.canonical_row(distinguished, uf)
        return distinguished in rows


class Analyzer:
    def __init__(self, schema: Schema, max_rows: int = 4096) -> None:
        self.schema = schema
        self.chaser = Chaser(schema.attrs, max_rows=max_rows)
        self._dep_basis_cache: dict[AttrSet, tuple[AttrSet, ...]] = {}
        self._fd_closure_cache: dict[AttrSet, AttrSet] = {}

    def implies_fd(self, lhs: AttrSet, rhs: AttrSet) -> bool:
        return self.chaser.implies_fd(self.schema.fds, self.schema.mvds, lhs, rhs)

    def implies_mvd(self, lhs: AttrSet, rhs: AttrSet) -> bool:
        return self.chaser.implies_mvd(self.schema.fds, self.schema.mvds, lhs, rhs)

    def fd_closure(self, lhs: AttrSet) -> AttrSet:
        if lhs not in self._fd_closure_cache:
            closure = set(lhs)
            for a in self.schema.attrs - lhs:
                if self.implies_fd(lhs, frozenset([a])):
                    closure.add(a)
            self._fd_closure_cache[lhs] = frozenset(closure)
        return self._fd_closure_cache[lhs]

    def dependency_basis(self, lhs: AttrSet) -> tuple[AttrSet, ...]:
        if lhs in self._dep_basis_cache:
            return self._dep_basis_cache[lhs]

        rest = self.schema.attrs - lhs
        if not rest:
            self._dep_basis_cache[lhs] = ()
            return ()

        implied_sets = [
            s for s in powerset(rest) if self.implies_mvd(lhs, s)
        ]

        blocks: list[set[str]] = []
        unseen = set(rest)
        while unseen:
            a = min(unseen)
            block = {
                b
                for b in rest
                if all((a in s) == (b in s) for s in implied_sets)
            }
            blocks.append(block)
            unseen -= block

        result = tuple(sorted((frozenset(b) for b in blocks), key=lambda x: sorted(x)))
        self._dep_basis_cache[lhs] = result
        return result

    def fdep(self, lhs: AttrSet) -> set[AttrSet]:
        return {
            block
            for block in self.dependency_basis(lhs)
            if self.implies_fd(lhs, block)
        }

    def mdep(self, lhs: AttrSet) -> set[AttrSet]:
        return set(self.dependency_basis(lhs)) - self.fdep(lhs)

    def m_splits(self, x: AttrSet, y: AttrSet) -> bool:
        hits = [w for w in self.mdep(x) if w & y]
        return len(hits) >= 2

    def mvd_split_witnesses(self, x: AttrSet, y: AttrSet) -> list[AttrSet]:
        return [
            w
            for w in self.mdep(x)
            if (w & y) and (y - x - w)
        ]

    def extended_split_free(self) -> tuple[bool, list[str]]:
        errors: list[str] = []
        lhs_sets = sorted(self.schema.lhs_sets, key=lambda s: (len(s), sorted(s)))

        for x in lhs_sets:
            for y in lhs_sets:
                if self.m_splits(x, y):
                    errors.append(
                        f"{fmt_set(x)} M-splits {fmt_set(y)}"
                    )

        for x in lhs_sets:
            for y in lhs_sets:
                for w in self.mvd_split_witnesses(x, y):
                    ok = False
                    for z in lhs_sets:
                        if (
                            w in self.mdep(z)
                            and self.implies_fd(x, z)
                            and y <= (z | w)
                        ):
                            ok = True
                            break
                    if not ok:
                        errors.append(
                            f"{fmt_set(x)} ->> {fmt_set(w)} splits "
                            f"{fmt_set(y)} without the required Z witness"
                        )

        return not errors, errors

    def m_intersection_property(self) -> tuple[bool, list[str]]:
        errors: list[str] = []
        lhs_sets = sorted(self.schema.lhs_sets, key=lambda s: (len(s), sorted(s)))
        for x in lhs_sets:
            for y in lhs_sets:
                common = self.mdep(x) & self.mdep(y)
                base_xy = self.mdep(x & y)
                for w in common:
                    if w in base_xy:
                        continue
                    ok = any(
                        w in self.mdep(z)
                        and self.implies_fd(x, z)
                        and self.implies_fd(y, z)
                        for z in lhs_sets
                    )
                    if not ok:
                        errors.append(
                            f"M-intersection fails for X={fmt_set(x)}, "
                            f"Y={fmt_set(y)}, W={fmt_set(w)}"
                        )
        return not errors, errors

    def f_intersection_property(self) -> tuple[bool, list[str]]:
        errors: list[str] = []
        lhs_sets = sorted(self.schema.lhs_sets, key=lambda s: (len(s), sorted(s)))
        for x in lhs_sets:
            for y in lhs_sets:
                common_attrs = set().union(*self.fdep(x)) if self.fdep(x) else set()
                common_attrs &= set().union(*self.fdep(y)) if self.fdep(y) else set()
                xy_fattrs = set().union(*self.fdep(x & y)) if self.fdep(x & y) else set()

                for a in sorted(common_attrs - xy_fattrs):
                    if self.implies_fd(x, y) or self.implies_fd(y, x):
                        continue
                    ok = False
                    for z in lhs_sets:
                        if z <= x:
                            # The F-intersection witness must be a non-trivial
                            # FD consequence of X. Otherwise Z = X would make
                            # the second disjunct vacuous whenever MDEP(X) is
                            # non-empty.
                            continue
                        for w in self.mdep(x) & self.mdep(z):
                            if y <= (z | w) and self.implies_fd(x, z):
                                ok = True
                                break
                        if ok:
                            break
                    if not ok:
                        errors.append(
                            f"F-intersection fails for X={fmt_set(x)}, "
                            f"Y={fmt_set(y)}, A={a}"
                        )
        return not errors, errors

    def extended_conflict_free(self) -> tuple[bool, list[str]]:
        checks = [
            self.extended_split_free(),
            self.m_intersection_property(),
            self.f_intersection_property(),
        ]
        errors = [e for ok, es in checks if not ok for e in es]
        return not errors, errors

    def is_4nf_relation(self, relation: AttrSet) -> tuple[bool, str | None]:
        subsets = powerset(relation)
        for x in subsets:
            superkey = self.implies_fd(x, relation)

            for a in relation - x:
                if self.implies_fd(x, frozenset([a])) and not superkey:
                    return (
                        False,
                        f"FD {fmt_set(x)} -> {a} violates BCNF/4NF in "
                        f"{fmt_set(relation)}",
                    )

            for y in subsets:
                if y <= x or x | y == relation:
                    continue
                if self.implies_mvd(x, y) and not superkey:
                    return (
                        False,
                        f"MVD {fmt_set(x)} ->> {fmt_set(y)} violates 4NF in "
                        f"{fmt_set(relation)}",
                    )

        return True, None

    def lossless(self, decomposition: Sequence[AttrSet]) -> bool:
        jd = tuple(frozenset(r) for r in decomposition)
        return self.chaser.implies_jd(self.schema.fds, self.schema.mvds, jd)

    def local_fds(self, decomposition: Sequence[AttrSet]) -> tuple[FD, ...]:
        found: set[FD] = set()
        for relation in decomposition:
            for x in powerset(relation):
                for a in relation - x:
                    if self.implies_fd(x, frozenset([a])):
                        found.add(FD(x, frozenset([a])))
        return tuple(sorted(found, key=lambda fd: (fmt_set(fd.lhs), fmt_set(fd.rhs))))

    def dependency_preserving(self, decomposition: Sequence[AttrSet]) -> bool:
        jd = tuple(frozenset(r) for r in decomposition)
        local_fds = self.local_fds(decomposition)
        empty_mvds: tuple[MVD, ...] = ()
        jds = (jd,)

        for fd in self.schema.fds:
            if not self.chaser.implies_fd(local_fds, empty_mvds, fd.lhs, fd.rhs, jds):
                return False

        for mvd in self.schema.mvds:
            if not self.chaser.implies_mvd(local_fds, empty_mvds, mvd.lhs, mvd.rhs, jds):
                return False

        return True

    def acyclic_decomposition(self, decomposition: Sequence[AttrSet]) -> bool:
        """Alpha-acyclicity of the decomposition hypergraph via GYO reduction."""
        edges = {frozenset(r) for r in decomposition if r}

        changed = True
        while changed:
            changed = False

            redundant = {
                e for e in edges
                if any(e < other for other in edges)
            }
            if redundant:
                edges -= redundant
                changed = True
                continue

            occurrences = {a: 0 for a in self.schema.attrs}
            for edge in edges:
                for a in edge:
                    occurrences[a] += 1

            disposable = {a for a, count in occurrences.items() if count <= 1}
            if disposable:
                new_edges = {frozenset(edge - disposable) for edge in edges}
                new_edges = {edge for edge in new_edges if edge}
                if new_edges != edges:
                    edges = new_edges
                    changed = True

        return not edges

    def synthesize_decomposition(
        self,
        max_relations: int | None = None,
        exhaustive_attr_limit: int = 8,
    ) -> tuple[list[AttrSet], tuple[FD, ...]]:
        attrs = self.schema.attrs
        if len(attrs) > exhaustive_attr_limit:
            raise ValueError(
                f"exhaustive synthesis is limited to {exhaustive_attr_limit} "
                f"attributes by default; got {len(attrs)}"
            )

        all_candidates = [s for s in powerset(attrs, include_empty=False)]
        candidates = []
        for c in all_candidates:
            ok, _ = self.is_4nf_relation(c)
            if ok:
                candidates.append(c)

        # Larger relations first usually finds cleaner decompositions.
        candidates.sort(key=lambda s: (-len(s), fmt_set(s)))
        by_attr = {
            a: [c for c in candidates if a in c]
            for a in attrs
        }

        if max_relations is None:
            max_relations = len(attrs)

        seen: set[tuple[AttrSet, ...]] = set()

        def normalize(decomp: Sequence[AttrSet]) -> tuple[AttrSet, ...]:
            # Remove schemas contained in another selected schema.
            minimal = []
            for r in decomp:
                if not any(r < s for s in decomp):
                    minimal.append(r)
            return tuple(sorted(set(minimal), key=lambda s: (len(s), fmt_set(s))))

        def search(selected: list[AttrSet], covered: AttrSet) -> list[AttrSet] | None:
            norm = normalize(selected)
            if norm in seen:
                return None
            seen.add(norm)

            if len(norm) > max_relations:
                return None

            if covered == attrs:
                if (
                    self.acyclic_decomposition(norm)
                    and self.lossless(norm)
                    and self.dependency_preserving(norm)
                ):
                    return list(norm)

                if len(norm) >= max_relations:
                    return None

                for cand in candidates:
                    if cand in norm or any(cand < existing for existing in norm):
                        continue
                    result = search(list(norm) + [cand], covered | cand)
                    if result is not None:
                        return result
                return None

            missing = sorted(attrs - covered)
            a = missing[0]
            for cand in by_attr[a]:
                if cand in selected:
                    continue
                result = search(selected + [cand], covered | cand)
                if result is not None:
                    return result
            return None

        result = search([], frozenset())
        if result is None:
            raise RuntimeError("no lossless dependency-preserving 4NF decomposition found")
        return result, self.local_fds(result)


def parse_dep(obj: dict[str, object], cls: type[FD] | type[MVD]) -> FD | MVD:
    return cls(fs(obj.get("lhs", [])), fs(obj.get("rhs", [])))  # type: ignore[arg-type]


def parse_attribute_set(text: str, known_attrs: Iterable[str] = ()) -> AttrSet:
    value = text.strip()
    if not value or value in {"{}", "∅"}:
        return frozenset()

    value = value.strip("{}[]()")
    known = set(known_attrs)
    if value in known:
        return frozenset([value])

    if "," in value or re.search(r"\s", value):
        return frozenset(token for token in re.split(r"[\s,]+", value) if token)

    return frozenset(value)


def validate_dependency_attrs(
    dep_attrs: AttrSet,
    declared_attrs: set[str],
    line_no: int,
) -> None:
    unknown = dep_attrs - declared_attrs
    if unknown:
        raise ValueError(f"line {line_no}: dependency uses unknown attributes: {sorted(unknown)}")


def schema_from_text(text: str) -> Schema:
    attrs: set[str] = set()
    explicit_attrs: set[str] = set()
    saw_attribute_line = False
    fds: list[FD] = []
    mvds: list[MVD] = []

    for line_no, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.split("#", 1)[0].split("--", 1)[0].strip()
        if not line:
            continue

        attr_match = re.match(r"^(?:attributes|attrs|schema)\s*:\s*(.+)$", line, re.I)
        if attr_match:
            saw_attribute_line = True
            explicit_attrs |= set(parse_attribute_set(attr_match.group(1)))
            continue

        dep_match = re.match(r"^(?:fd|mvd)?\s*:?\s*(.*?)\s*(->>|↠|-->>|->)\s*(.*?)\s*$", line, re.I)
        if not dep_match:
            raise ValueError(f"line {line_no}: expected 'X -> Y' or 'X ->> Y'")

        if not saw_attribute_line:
            raise ValueError(f"line {line_no}: attributes line must appear before dependencies")

        lhs = parse_attribute_set(dep_match.group(1), explicit_attrs)
        op = dep_match.group(2)
        rhs = parse_attribute_set(dep_match.group(3), explicit_attrs)
        if not lhs or not rhs:
            raise ValueError(f"line {line_no}: both sides of a dependency must be non-empty")

        if explicit_attrs:
            validate_dependency_attrs(lhs | rhs, explicit_attrs, line_no)

        attrs |= set(lhs | rhs)
        if op in {"->>", "↠", "-->>"}:
            mvds.append(MVD(lhs, rhs))
        else:
            fds.append(FD(lhs, rhs))

    attrs |= explicit_attrs
    if not saw_attribute_line:
        raise ValueError("missing attributes line")
    if not attrs:
        raise ValueError("no attributes or dependencies found")

    return Schema(frozenset(attrs), tuple(fds), tuple(mvds))


def load_schema(path: str) -> Schema:
    with open(path, "r", encoding="utf-8") as f:
        if path.lower().endswith(".json"):
            data = json.load(f)
        else:
            return schema_from_text(f.read())
    attrs = fs(data["attributes"])
    fds = tuple(parse_dep(d, FD) for d in data.get("fds", []))
    mvds = tuple(parse_dep(d, MVD) for d in data.get("mvds", []))

    for dep in (*fds, *mvds):
        unknown = (dep.lhs | dep.rhs) - attrs
        if unknown:
            raise ValueError(f"dependency uses unknown attributes: {sorted(unknown)}")

    return Schema(attrs, fds, mvds)


def analyze_schema(
    schema: Schema,
    *,
    max_rows: int = 4096,
    max_relations: int | None = None,
    exhaustive_attr_limit: int = 8,
) -> dict[str, object]:
    analyzer = Analyzer(schema, max_rows=max_rows)
    ok, errors = analyzer.extended_conflict_free()

    output: dict[str, object] = {
        "attributes": sorted(schema.attrs),
        "fds": [
            {"lhs": sorted(dep.lhs), "rhs": sorted(dep.rhs)}
            for dep in schema.fds
        ],
        "mvds": [
            {"lhs": sorted(dep.lhs), "rhs": sorted(dep.rhs)}
            for dep in schema.mvds
        ],
        "extended_conflict_free": ok,
    }

    if not ok:
        output["errors"] = errors
        return output

    decomposition, preserved_fds = analyzer.synthesize_decomposition(
        max_relations=max_relations,
        exhaustive_attr_limit=exhaustive_attr_limit,
    )
    output["decomposition"] = [sorted(r) for r in decomposition]
    output["preserved_fds"] = [
        {"lhs": sorted(fd.lhs), "rhs": sorted(fd.rhs)}
        for fd in preserved_fds
    ]
    output["acyclic"] = analyzer.acyclic_decomposition(decomposition)
    output["lossless"] = analyzer.lossless(decomposition)
    output["dependency_preserving"] = analyzer.dependency_preserving(decomposition)
    return output


def main(argv: Sequence[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("schema_file")
    parser.add_argument("--max-rows", type=int, default=4096)
    parser.add_argument("--max-relations", type=int)
    parser.add_argument("--exhaustive-attr-limit", type=int, default=8)
    args = parser.parse_args(argv)

    schema = load_schema(args.schema_file)
    output = analyze_schema(
        schema,
        max_rows=args.max_rows,
        max_relations=args.max_relations,
        exhaustive_attr_limit=args.exhaustive_attr_limit,
    )
    print(json.dumps(output, indent=2))
    return 0 if output.get("extended_conflict_free") else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

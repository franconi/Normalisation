from __future__ import annotations

import re
from typing import Any, Iterable, Mapping


DEPENDENCY_SYMBOLS = ("<-N->", "->N<-", "-N->", "->>", "o=>", "x=>", "==", "->", "=>")


def build_six_nf(analysis: Mapping[str, Any]) -> dict[str, Any]:
    relations = build_target_relations(analysis)
    relation_items: list[dict[str, Any]] = []
    for relation in relations:
        dependencies = target_relation_dependencies(relation, analysis)
        dependencies = dependencies_with_fallback_key_constraint(relation, dependencies)
        relation_items.append(
            {
                "name": relation["name"],
                "attributes": list(relation["attributes"]),
                "dependencies": display_dependencies_for_relation(
                    relation["name"],
                    relation["attributes"],
                    dependencies,
                ),
            }
        )

    return {
        "name": "6NF",
        "relations": relation_items,
        "cross_relation_inclusion_dependencies": target_cross_inclusion_texts(
            analysis,
            relations,
        ),
    }


def fmt_set(values: Iterable[str]) -> str:
    items = list(values or [])
    if not items:
        return "{}"
    return ", ".join(items) if any(len(value) > 1 for value in items) else "".join(items)


def natural_key(value: str) -> tuple[Any, ...]:
    return tuple(
        int(part) if part.isdigit() else part
        for part in re.split(r"(\d+)", str(value))
    )


def relation_name_for(attributes: Iterable[str]) -> str:
    items = list(attributes or [])
    if not items:
        return "{}"
    return "_".join(sorted(items, key=natural_key))


def attr_postfix_number(attribute: str) -> int:
    match = re.search(r"#(\d+)$", str(attribute))
    return int(match.group(1)) if match else 0


def attr_postfix_suffix(attribute: str) -> str | None:
    match = re.search(r"#(\d+)$", str(attribute))
    return match.group(1) if match else None


def relation_postfix_number(attributes: Iterable[str]) -> int:
    numbers = [attr_postfix_number(attribute) for attribute in attributes or []]
    return min(numbers) if numbers else 0


def normalized_dependency_text(value: Any) -> str:
    text = re.sub(r"\s+", " ", str(value).strip())
    return re.sub(r"\s*,\s*", ", ", text)


def split_dependency_text(text: Any) -> dict[str, str] | None:
    value = str(text)
    for symbol in DEPENDENCY_SYMBOLS:
        index = value.find(symbol)
        if index != -1:
            return {
                "lhs": value[:index].strip(),
                "symbol": symbol,
                "rhs": value[index + len(symbol) :].strip(),
            }
    return None


def dependency_key(item: Any) -> str:
    split = split_dependency_text(item)
    if not split:
        return normalized_dependency_text(item)
    return (
        f"{normalized_dependency_text(split['lhs'])} "
        f"{split['symbol']} "
        f"{normalized_dependency_text(split['rhs'])}"
    )


def unique_dependencies(items: Iterable[Any]) -> list[Any]:
    out: list[Any] = []
    seen: set[str] = set()
    for item in items or []:
        if item is None or not str(item).strip():
            continue
        key = dependency_key(item)
        if key in seen:
            continue
        seen.add(key)
        out.append(item)
    return out


def inclusion_symbol(dep: Mapping[str, Any]) -> str:
    text = dep.get("text")
    split = split_dependency_text(text) if text else None
    if split and split["symbol"] in {"==", "o=>", "x=>", "=>"}:
        return normalized_inclusion_symbol(split["symbol"], len(inclusion_sources(dep)))
    symbol = dep.get("symbol")
    if symbol:
        return normalized_inclusion_symbol(str(symbol), len(inclusion_sources(dep)))
    kind = dep.get("kind")
    if kind == "equality":
        return "=="
    if kind == "covering":
        return normalized_inclusion_symbol("o=>", len(inclusion_sources(dep)))
    if kind == "disjoint":
        return normalized_inclusion_symbol("x=>", len(inclusion_sources(dep)))
    return "=>"


def normalized_inclusion_symbol(symbol: str, source_count: int) -> str:
    if source_count == 1 and symbol == "x=>":
        return "=>"
    if source_count == 1 and symbol == "o=>":
        return "=="
    return symbol


def inclusion_sources(dep: Mapping[str, Any]) -> list[list[str]]:
    if isinstance(dep.get("sources"), list):
        return [list(source) for source in dep.get("sources", []) or []]
    text = dep.get("text")
    split = split_dependency_text(text) if text else None
    if split and split["symbol"] in {"==", "o=>", "x=>", "=>"}:
        return [
            parse_attribute_side(source.strip())
            for source in split["lhs"].split("|")
            if source.strip()
        ]
    return [list(dep.get("lhs", []) or [])]


def inclusion_target(dep: Mapping[str, Any]) -> list[str]:
    if isinstance(dep.get("target"), list):
        return list(dep.get("target", []) or [])
    text = dep.get("text")
    split = split_dependency_text(text) if text else None
    if split and split["symbol"] in {"==", "o=>", "x=>", "=>"}:
        return parse_attribute_side(split["rhs"])
    return list(dep.get("rhs", []) or [])


def inclusion_attributes(dep: Mapping[str, Any]) -> list[str]:
    return [
        attribute
        for source in inclusion_sources(dep)
        for attribute in source
    ] + inclusion_target(dep)


def inclusion_text(dep: Mapping[str, Any]) -> str:
    sources = inclusion_sources(dep)
    target = inclusion_target(dep)
    source_text = " | ".join(fmt_set(source) for source in sources)
    return f"{source_text} {inclusion_symbol(dep)} {fmt_set(target)}"


def unique_inclusion_dependencies(items: Iterable[Mapping[str, Any]]) -> list[Mapping[str, Any]]:
    out: list[Mapping[str, Any]] = []
    seen: set[str] = set()
    for item in items or []:
        key = dependency_key(inclusion_text(item))
        if key in seen:
            continue
        seen.add(key)
        out.append(item)
    return out


def is_subset(values: Iterable[str], attrs: set[str]) -> bool:
    return all(value in attrs for value in values or [])


def canonical_attributes(attributes: Iterable[str]) -> str:
    return "\x01".join(sorted(attributes or [], key=natural_key))


def parse_attribute_side(text: Any, known_attributes: Iterable[str] = ()) -> list[str]:
    value = str(text or "").strip()
    if not value or value in {"{}", "∅"}:
        return []

    known = set(known_attributes or [])
    if value in known:
        return [value]
    if re.match(r"^att\s*\(", value, re.IGNORECASE):
        return list(known)

    value = re.sub(r"^[\{\[\(]|[\}\]\)]$", "", value)
    if value in known:
        return [value]
    if "," in value or re.search(r"\s", value):
        return [token.strip() for token in re.split(r"[\s,]+", value) if token.strip()]
    return list(value)


def dependency_attributes(text: Any, known_attributes: Iterable[str] = ()) -> list[str]:
    split = split_dependency_text(text)
    if not split:
        return []
    return [
        *parse_attribute_side(split["lhs"], known_attributes),
        *parse_attribute_side(split["rhs"], known_attributes),
    ]


def functional_dependency_parts(dependency: Any, known_attributes: Iterable[str]) -> dict[str, list[str]] | None:
    split = split_dependency_text(dependency)
    if not split or split["symbol"] != "->":
        return None
    return {
        "lhs": parse_attribute_side(split["lhs"], known_attributes),
        "rhs": parse_attribute_side(split["rhs"], known_attributes),
    }


def closure(attributes: Iterable[str], functional_dependencies: Iterable[Mapping[str, list[str]]]) -> set[str]:
    result = set(attributes or [])
    changed = True
    while changed:
        changed = False
        for dep in functional_dependencies:
            if not is_subset(dep["lhs"], result):
                continue
            for attr in dep["rhs"]:
                if attr not in result:
                    result.add(attr)
                    changed = True
    return result


def has_key_constraint(attributes: Iterable[str], dependencies: Iterable[str]) -> bool:
    relation_attributes = list(attributes or [])
    if not relation_attributes:
        return True

    target_attrs = set(relation_attributes)
    functional_dependencies = [
        dep
        for text in dependencies or []
        for dep in [functional_dependency_parts(text, relation_attributes)]
        if dep and is_subset([*dep["lhs"], *dep["rhs"]], target_attrs)
    ]
    return any(
        is_subset(relation_attributes, closure(dep["lhs"], functional_dependencies))
        for dep in functional_dependencies
    )


def dependencies_with_fallback_key_constraint(
    relation: Mapping[str, Any],
    dependencies: Iterable[str],
) -> list[str]:
    items = list(dependencies or [])
    attributes = list(relation.get("attributes", []) or [])
    if not attributes or has_key_constraint(attributes, items):
        return items

    relation_name = str(relation.get("name") or relation_name_for(attributes))
    return [
        *items,
        f"{fmt_set(attributes)} -> att({relation_name})",
    ]


def display_dependencies_for_relation(
    relation_name: str,
    attributes: Iterable[str],
    dependencies: Iterable[str],
) -> list[str]:
    relation_attributes = list(attributes or [])
    items = unique_dependencies(dependencies)
    if not items or not relation_attributes:
        return list(items)

    target_attrs = set(relation_attributes)
    functional_dependencies = [
        {"text": text, "index": index, "dep": dep}
        for index, text in enumerate(items)
        for dep in [functional_dependency_parts(text, relation_attributes)]
        if dep and is_subset([*dep["lhs"], *dep["rhs"]], target_attrs)
    ]
    if not functional_dependencies:
        return list(items)

    parsed_fds = [item["dep"] for item in functional_dependencies]
    key_groups: dict[str, dict[str, Any]] = {}
    fd_groups: dict[str, dict[str, Any]] = {}

    for item in functional_dependencies:
        dep = item["dep"]
        key = canonical_attributes(dep["lhs"])
        if is_subset(relation_attributes, closure(dep["lhs"], parsed_fds)):
            key_groups.setdefault(key, {"lhs": dep["lhs"], "indexes": set()})
            key_groups[key]["indexes"].add(item["index"])
            continue

        group = fd_groups.setdefault(
            key,
            {"lhs": dep["lhs"], "rhs": [], "indexes": set()},
        )
        group["indexes"].add(item["index"])
        for attr in dep["rhs"]:
            if attr not in group["rhs"]:
                group["rhs"].append(attr)

    fd_groups = {
        key: group
        for key, group in fd_groups.items()
        if len(group["indexes"]) >= 2
    }
    if not key_groups and not fd_groups:
        return list(items)

    index_to_group: dict[int, tuple[str, str]] = {}
    for key, group in key_groups.items():
        for index in group["indexes"]:
            index_to_group[index] = ("key", key)
    for key, group in fd_groups.items():
        for index in group["indexes"]:
            index_to_group[index] = ("fd", key)

    displayed: list[str] = []
    emitted_groups: set[tuple[str, str]] = set()
    for index, item in enumerate(items):
        group_ref = index_to_group.get(index)
        if not group_ref:
            displayed.append(str(item))
            continue
        if group_ref in emitted_groups:
            continue

        kind, key = group_ref
        if kind == "key":
            group = key_groups[key]
            name = relation_name or relation_name_for(relation_attributes)
            displayed.append(f"{fmt_set(group['lhs'])} -> att({name})")
        else:
            group = fd_groups[key]
            displayed.append(f"{fmt_set(group['lhs'])} -> {fmt_set(group['rhs'])}")
        emitted_groups.add(group_ref)

    return [str(item) for item in unique_dependencies(displayed)]


def rename_attribute_for_relation(attribute: str, relation_name: str) -> str:
    match = re.search(r"#(\d+)$", str(relation_name or ""))
    return f"{attribute}#{match.group(1)}" if match else attribute


def mapped_inclusion(dep: Mapping[str, Any], origin: Mapping[str, Any]) -> dict[str, Any]:
    relation_name = str(origin.get("perRelation", {}).get("sql_null_relation_name", ""))
    sources = [
        [
            rename_attribute_for_relation(str(attr), relation_name)
            for attr in source
        ]
        for source in inclusion_sources(dep)
    ]
    target = [
        rename_attribute_for_relation(str(attr), relation_name)
        for attr in inclusion_target(dep)
    ]
    return {
        "sources": sources,
        "target": target,
        "lhs": sources[0] if sources else [],
        "rhs": target,
    }


def real_target_relations(target_relations: Iterable[Mapping[str, Any]]) -> list[Mapping[str, Any]]:
    return [
        relation
        for relation in target_relations or []
        if not relation.get("generated_target_relation")
    ]


def target_numbered_suffix_groups(target_relations: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    by_prefix: dict[str, dict[str, Any]] = {}
    for relation in real_target_relations(target_relations):
        for attribute in relation.get("attributes", []):
            match = re.match(r"^(.*)#(\d+)$", str(attribute))
            if match and match.group(1):
                group = by_prefix.setdefault(
                    match.group(1),
                    {"attributes": {}, "base_attribute": None},
                )
                group["attributes"][int(match.group(2))] = str(attribute)
                continue

            attribute_name = str(attribute)
            if attribute_name:
                group = by_prefix.setdefault(
                    attribute_name,
                    {"attributes": {}, "base_attribute": None},
                )
                group["base_attribute"] = attribute_name

    groups = [
        {
            "prefix": prefix,
            "attributes": [
                attribute
                for _, attribute in sorted(group["attributes"].items())
            ],
            "base_attribute": group["base_attribute"],
        }
        for prefix, group in by_prefix.items()
    ]
    return sorted(
        [group for group in groups if group["attributes"]],
        key=lambda group: natural_key(group["prefix"]),
    )


def build_target_relations(analysis: Mapping[str, Any]) -> list[dict[str, Any]]:
    by_key: dict[str, dict[str, Any]] = {}

    for attributes in analysis.get("final_decomposition", []) or []:
        key = canonical_attributes(attributes)
        by_key[key] = {
            "name": relation_name_for(attributes),
            "attributes": sorted(attributes, key=natural_key),
            "origins": [],
        }

    for input_item in analysis.get("per_input_relation", []) or []:
        for per_relation in input_item.get("per_relation_4nf", []) or []:
            for attributes in per_relation.get("four_nf_decomposition", []) or []:
                key = canonical_attributes(attributes)
                if key not in by_key:
                    by_key[key] = {
                        "name": relation_name_for(attributes),
                        "attributes": sorted(attributes, key=natural_key),
                        "origins": [],
                    }
                by_key[key]["origins"].append(
                    {
                        "inputItem": input_item,
                        "perRelation": per_relation,
                        "sourceAttributes": set(input_item.get("attributes", []) or []),
                        "sqlNullAttributes": set(per_relation.get("sql_null_relation", []) or []),
                    }
                )

    relations = list(by_key.values())

    return sorted(
        relations,
        key=lambda relation: (
            relation_postfix_number(relation.get("attributes", [])),
            natural_key(str(relation.get("name", ""))),
        ),
    )


def target_base_relation_dependencies(target: Mapping[str, Any], analysis: Mapping[str, Any]) -> list[str]:
    target_attrs = set(target.get("attributes", []) or [])
    dependencies: list[str] = []

    for origin in target.get("origins", []) or []:
        per_relation = origin.get("perRelation", {})
        for dep in per_relation.get("applicable_fds", []) or []:
            if is_subset(dependency_attributes(dep, target.get("attributes", [])), target_attrs):
                dependencies.append(str(dep))

        for dep in unique_inclusion_dependencies(analysis.get("inclusion_dependencies", []) or []):
            dep_attrs = inclusion_attributes(dep)
            if not is_subset(dep_attrs, origin.get("sourceAttributes", set())):
                continue
            mapped = mapped_inclusion(dep, origin)
            if is_subset(inclusion_attributes(mapped), target_attrs):
                dependencies.append(
                    inclusion_text({**mapped, "kind": dep.get("kind"), "symbol": inclusion_symbol(dep)})
                )

    return [str(dep) for dep in unique_dependencies(dependencies)]


def target_relation_dependencies(target: Mapping[str, Any], analysis: Mapping[str, Any]) -> list[str]:
    return [
        str(dep)
        for dep in unique_dependencies(
            [
                *target_base_relation_dependencies(target, analysis),
                *numbered_suffix_inclusion_duplicates_for_relation(target, analysis),
            ]
        )
    ]


def hash_free_source_inclusion_dependencies(
    analysis: Mapping[str, Any],
) -> list[Mapping[str, Any]]:
    dependencies: list[Mapping[str, Any]] = []
    for dep in unique_inclusion_dependencies(analysis.get("inclusion_dependencies", []) or []):
        attributes = inclusion_attributes(dep)
        if not attributes:
            continue
        if any(attr_postfix_suffix(attribute) for attribute in attributes):
            continue
        dependencies.append(dep)
    return dependencies


def matching_relation_suffixes_for_inclusion(
    relation: Mapping[str, Any],
    dep: Mapping[str, Any],
) -> list[str]:
    relation_attrs = set(str(attribute) for attribute in relation.get("attributes", []) or [])
    dep_attrs = list(dict.fromkeys(str(attribute) for attribute in inclusion_attributes(dep)))
    if not dep_attrs:
        return []

    common_suffixes: set[str] | None = None
    for attribute in dep_attrs:
        suffixes: set[str] = set()
        for relation_attribute in relation_attrs:
            match = re.match(r"^(.*)#(\d+)$", relation_attribute)
            if match and match.group(1) == attribute:
                suffixes.add(match.group(2))
        common_suffixes = suffixes if common_suffixes is None else common_suffixes & suffixes
        if not common_suffixes:
            return []

    return sorted(common_suffixes, key=lambda value: int(value))


def suffixed_inclusion_dependency(dep: Mapping[str, Any], suffix: str) -> dict[str, Any]:
    sources = [
        [f"{attribute}#{suffix}" for attribute in source]
        for source in inclusion_sources(dep)
    ]
    target = [f"{attribute}#{suffix}" for attribute in inclusion_target(dep)]
    return {
        "kind": dep.get("kind"),
        "symbol": inclusion_symbol(dep),
        "sources": sources,
        "target": target,
        "lhs": sources[0] if sources else [],
        "rhs": target,
    }


def numbered_suffix_inclusion_duplicates_for_relation(
    relation: Mapping[str, Any],
    analysis: Mapping[str, Any],
) -> list[str]:
    dependencies: list[str] = []
    for dep in hash_free_source_inclusion_dependencies(analysis):
        for suffix in matching_relation_suffixes_for_inclusion(relation, dep):
            dependencies.append(inclusion_text(suffixed_inclusion_dependency(dep, suffix)))
    return [str(dep) for dep in unique_dependencies(dependencies)]


def target_functional_dependencies_for_relation(
    relation: Mapping[str, Any],
    analysis: Mapping[str, Any],
) -> list[dict[str, list[str]]]:
    relation_attrs = set(relation.get("attributes", []) or [])
    return [
        dep
        for text in target_base_relation_dependencies(relation, analysis)
        for dep in [functional_dependency_parts(text, relation.get("attributes", []) or [])]
        if dep and is_subset([*dep["lhs"], *dep["rhs"]], relation_attrs)
    ]


def target_attribute_is_key(
    attribute: str,
    target_relations: Iterable[Mapping[str, Any]],
    analysis: Mapping[str, Any],
) -> bool:
    for relation in real_target_relations(target_relations):
        relation_attrs = set(relation.get("attributes", []) or [])
        if attribute not in relation_attrs:
            continue
        closure_attrs = closure(
            [attribute],
            target_functional_dependencies_for_relation(relation, analysis),
        )
        if is_subset(relation.get("attributes", []) or [], closure_attrs):
            return True
    return False


def target_qualifying_numbered_suffix_groups(
    target_relations: Iterable[Mapping[str, Any]],
    analysis: Mapping[str, Any],
) -> list[dict[str, Any]]:
    return [
        group
        for group in target_numbered_suffix_groups(target_relations)
        if all(
            target_attribute_is_key(attribute, target_relations, analysis)
            for attribute in group["attributes"]
        )
    ]


def target_generated_numbered_suffix_inclusions(
    target_relations: Iterable[Mapping[str, Any]],
    analysis: Mapping[str, Any],
) -> list[str]:
    return []


def all_target_attributes(target_relations: Iterable[Mapping[str, Any]]) -> set[str]:
    return {
        str(attribute)
        for relation in target_relations or []
        for attribute in relation.get("attributes", []) or []
    }


def source_inclusions_for_target_cross_relations(
    analysis: Mapping[str, Any],
    target_relations: Iterable[Mapping[str, Any]],
) -> list[str]:
    targets = list(target_relations or [])
    target_attrs = all_target_attributes(targets)
    dependencies: list[str] = []

    for dep in unique_inclusion_dependencies(analysis.get("inclusion_dependencies", []) or []):
        dep_attrs = inclusion_attributes(dep)
        mapped_to_origin = False

        for target in targets:
            for origin in target.get("origins", []) or []:
                if not is_subset(dep_attrs, origin.get("sqlNullAttributes", set())):
                    continue
                mapped_to_origin = True
                mapped = mapped_inclusion(dep, origin)
                mapped_attrs = inclusion_attributes(mapped)
                if not is_subset(mapped_attrs, target_attrs):
                    continue
                if is_local_inclusion_for_any_relation(mapped, targets):
                    continue
                dependencies.append(
                    inclusion_text({**mapped, "kind": dep.get("kind"), "symbol": inclusion_symbol(dep)})
                )

        if not mapped_to_origin:
            dependencies.append(inclusion_text(dep))

    return [str(dep) for dep in unique_dependencies(dependencies)]


def source_relations(analysis: Mapping[str, Any]) -> list[dict[str, Any]]:
    relations: list[dict[str, Any]] = []
    for database in analysis.get("database_schemas", []) or []:
        for relation in database.get("relations", []) or []:
            relations.append({**relation, "database_schema": database.get("name", "")})
    if relations:
        return relations
    return [
        {**relation, "database_schema": ""}
        for relation in analysis.get("input_relations", []) or []
    ]


def is_local_inclusion_for_attributes(dep: Mapping[str, Any], attributes: Iterable[str]) -> bool:
    return is_subset(inclusion_attributes(dep), set(attributes or []))


def is_local_inclusion_for_any_relation(
    dep: Mapping[str, Any],
    relations: Iterable[Mapping[str, Any]],
) -> bool:
    return any(
        is_local_inclusion_for_attributes(dep, relation.get("attributes", []) or [])
        for relation in relations or []
    )


def cross_inclusion_texts_for_relations(
    inclusions: Iterable[Mapping[str, Any]],
    relations: Iterable[Mapping[str, Any]],
) -> list[str]:
    return [
        str(dep)
        for dep in unique_dependencies(
            inclusion_text(dep)
            for dep in unique_inclusion_dependencies(inclusions)
            if not is_local_inclusion_for_any_relation(dep, relations)
        )
    ]


def target_cross_inclusion_texts(
    analysis: Mapping[str, Any],
    target_relations: Iterable[Mapping[str, Any]],
) -> list[str]:
    targets = list(target_relations or [])
    return [
        str(dep)
        for dep in unique_dependencies(
            [
                *source_inclusions_for_target_cross_relations(analysis, targets),
                *target_generated_numbered_suffix_inclusions(targets, analysis),
            ]
        )
    ]

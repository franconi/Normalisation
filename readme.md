# SQL-null + 4NF Decomposer

Launch the frontend with:

``python3 combined_null_4nf_frontend.py --host 127.0.0.1 --port 8767``

The frontend is found at:

``http://127.0.0.1:8767``

Input format:

```
attributes: A B C D
AB -> C
A ->> D
```

With multiple input relations:

```
database schema registry:
relation R1: A B C D E
nullable: B C D
B -N-> C
B ->N<- D
B -> C

relation R2: A D E
nullable: D
A ->> D
A => A
```

If no database schema is declared, the input is treated as one default database
schema. Database schemas and relations are named globally. Attributes are
represented on each relation with a nullable flag; attributes are non-nullable
unless a `nullable:` declaration or structured JSON attribute marks them
nullable.

For each relation, the SQL-null stage first filters the powerset of the
nullable attributes. It then adds the non-nullable attributes back to each
surviving nullable set and names the resulting relations with the source
relation name plus a progressive suffix, for example `R1#1`, `R1#2`.
When nullable attributes exist, all SQL-null decomposition relations are
generated with a `#` suffix; no additional un-suffixed relation containing only
the non-nullable attributes is added.
In the displayed SQL-null decomposition, generated relations also suffix each
attribute with the same number, for example `R1#2: A#2, B#2`.
The 4NF stage uses the same displayed names for each generated relation, so
dependencies, decomposition steps, and final 4NF relations for `R1#2` are shown
with attributes such as `A#2`, `B#2`, and `C#2`.
If a relation has no nullable attributes, the SQL-null stage leaves it unchanged
and does not create a generated `#1` relation.

Dependency syntax:

- functional dependencies: `A B -> C`
- key-style functional dependencies: `A -> att(R)`
- multivalued dependencies: `A B ->> C`
- implies SQL-null dependencies: `A -N-> B`
- jointly SQL-null dependencies: `A <-N-> B`
- alternative SQL-null dependencies: `A ->N<- B`
- inclusion dependencies: `A B => C D`
- equality inclusion dependencies: `A B == C D`
- covering inclusion dependencies: `A B o=> C D`
- disjoint inclusion dependencies: `A B x=> C D`

Join dependencies (FDs and MVDs) and SQL-null dependencies must be contained in
one relation. For inclusion dependencies, the left side must be contained in one
relation, the right side must be contained in one relation, and both sides must
have the same arity. Inclusion dependencies are currently parsed, validated, and
reported; they do not change the SQL-null plus 4NF decomposition behavior.

SQL-null dependencies are evaluated on each candidate subset of nullable
attributes before the non-nullable attributes are added back:

- `A -N-> B` removes a subset when it contains `B` but not `A`.
- `A <-N-> B` removes a subset when it contains exactly one of `A` and `B`.
- `A ->N<- B` removes a subset when it contains both `A` and `B`, or neither
  of them. Equivalently, surviving subsets must contain exactly one of `A`
  and `B`.

For multi-character attribute names, declare them first:

```
attributes: Customer Order Product
Customer -> Order
Customer ->> Product
```

The CLI accepts .txt files directly:

```
python3 combined_null_4nf_decomposer.py sample_combined_null_4nf_schema.txt
```

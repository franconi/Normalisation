# PostgreSQL-to-PostgreSQL native logical replication


For PostgreSQL-to-PostgreSQL, this is a good fit for **native logical replication**, assuming PostgreSQL 16+ so you can use `origin = none` to avoid replication loops.

The shape is:

```text
Postgres A publishes INSERT/DELETE  ->  Postgres B subscribes
Postgres B publishes INSERT/DELETE  ->  Postgres A subscribes
```

On both sides, create publications that exclude `UPDATE` and `TRUNCATE`:

```sql
CREATE PUBLICATION pub_ins_del
FOR TABLE public.my_table
WITH (publish = 'insert, delete');
```

Then create the cross-subscriptions. On **B**, subscribing to **A**:

```sql
CREATE SUBSCRIPTION sub_from_a
CONNECTION 'host=a.example.com dbname=mydb user=repl password=secret'
PUBLICATION pub_ins_del
WITH (
  copy_data = false,
  origin = none
);
```

On **A**, subscribing to **B**:

```sql
CREATE SUBSCRIPTION sub_from_b
CONNECTION 'host=b.example.com dbname=mydb user=repl password=secret'
PUBLICATION pub_ins_del
WITH (
  copy_data = false,
  origin = none
);
```

The important part is:

```sql
origin = none
```

Without that, a row inserted on A could replicate to B, then B could publish it back to A. `origin = none` tells each subscription to receive only changes that originated locally on the publisher, not changes that the publisher itself received from another subscription.

A few practical requirements:

- Use PostgreSQL 16+ for this native loop-prevention model.
- Every replicated table should have a primary key, especially because you replicate `DELETE`.
- Avoid sequence collisions if both sides can insert. Use UUIDs, composite keys with a node/source column, or disjoint sequences.
- If you want to forbid local `UPDATE`, enforce it with privileges or triggers. `publish = 'insert, delete'` only means updates are not replicated; it does not prevent someone from updating locally.
- DDL/schema changes are not replicated by native logical replication. Keep schemas compatible manually.
- If data already exists on both sides, use `copy_data = false` and verify they are already aligned. If one side is authoritative initially, do one controlled initial copy first, then enable the reverse subscription.

So: **yes, native bidirectional logical replication can do this**, and your external lock policy removes the hardest part: conflict resolution. The remaining design risks are loop prevention, key generation, and making sure unreplicated local `UPDATE`s cannot silently diverge the two databases.

Relevant PostgreSQL docs: [`CREATE PUBLICATION`](https://www.postgresql.org/docs/current/sql-createpublication.html), [`CREATE SUBSCRIPTION`](https://www.postgresql.org/docs/current/sql-createsubscription.html), [logical replication restrictions](https://www.postgresql.org/docs/current/logical-replication-restrictions.html).

----

Then include `update` in the publication:

```sql
CREATE PUBLICATION pub_ins_upd_del
FOR TABLE public.my_table
WITH (publish = 'insert, update, delete');
```

And keep the bidirectional subscriptions with loop prevention:

```sql
CREATE SUBSCRIPTION sub_from_a
CONNECTION 'host=a.example.com dbname=mydb user=repl password=secret'
PUBLICATION pub_ins_upd_del
WITH (
  copy_data = false,
  origin = none
);
```

Same in the other direction.

The extra requirement for `UPDATE` is **replica identity**. PostgreSQL must know how to find the target row on the subscriber. Usually this means every replicated table should have a primary key:

```sql
CREATE TABLE public.my_table (
  id uuid PRIMARY KEY,
  ...
);
```

If there is no primary key, you can define another replica identity:

```sql
ALTER TABLE public.my_table
REPLICA IDENTITY USING INDEX my_unique_index;
```

or, as a fallback:

```sql
ALTER TABLE public.my_table
REPLICA IDENTITY FULL;
```

But `REPLICA IDENTITY FULL` is usually worse for performance, because PostgreSQL may need to compare whole rows to find the row to update/delete.

With your external lock policy, this can work well, but you still need to handle these cases:

- If an incoming `UPDATE` cannot find the row, PostgreSQL treats it as an `update_missing` conflict and skips it.
- If an incoming `UPDATE` violates a unique constraint, replication stops until manually fixed.
- If both sides generate primary keys, use UUIDs or disjoint key ranges.
- Do not update primary keys unless you really need to; it complicates replication and foreign keys.
- Use PostgreSQL 16+ for `origin = none`; without it, bidirectional native logical replication can echo changes back.

So the bidirectional setup becomes:

```text
A publishes INSERT/UPDATE/DELETE -> B subscribes with origin = none
B publishes INSERT/UPDATE/DELETE -> A subscribes with origin = none
```

Docs: [publication operation filtering](https://www.postgresql.org/docs/current/logical-replication-publication.html), [`CREATE PUBLICATION`](https://www.postgresql.org/docs/current/sql-createpublication.html), [`CREATE SUBSCRIPTION`](https://www.postgresql.org/docs/current/sql-createsubscription.html), [conflicts](https://www.postgresql.org/docs/current/logical-replication-conflicts.html).
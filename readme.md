# The Relational Database Normaliser

#### Declarations:

- database schema declaration: `database schema DBNAME`
- relation declaration: `relation RNAME: A B`
- SQL nullable attributes declaration: nullable: A B

If no database schema is declared, the input is treated as the default database
schema. 
Database schemas, relations, and attributes are named globally. 
Attributes may be nullable.

#### Dependency syntax:

- functional dependencies: `A B -> C D`
- key-style functional dependencies: `A B -> att(RNAME)`
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
have the same arity.

#### Example:

```
   database schema Registry:
   relation T: ssn empid name hdate phone email dept manager
   nullable: empid hdate dept manager
   empid -N-> dept
   dept <-N-> manager
   empid <-N-> hdate
   ssn -> name
   ssn ->> phone
   ssn ->> email
   ssn -> empid
   empid -> ssn
   empid -> hdate
   empid -> dept
   dept -> manager
   manager => empid
```

#### Frontend:

Launch the frontend with:

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;``python3 combined_null_4nf_frontend.py --host 127.0.0.1 --port 8767``

The frontend is found at:

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;``http://127.0.0.1:8767``

The CLI accepts .txt files directly:

```
python3 combined_null_4nf_decomposer.py sample_combined_null_4nf_schema.txt
```

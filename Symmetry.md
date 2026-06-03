Yes — and here’s a clean proof.

The claim

No set Σ of fifth-normal-form constraints, keys, and unary inclusion dependencies (UIDs) over any schema containing a binary relation R(A, B) logically implies the symmetry constraint

sym(R): ∀x, y : R(x, y) → R(y, x).

Why 5NF doesn’t help

Fifth Normal Form is a schema design criterion: every join dependency (JD) on a relation must be implied by its candidate keys. It restricts how data should be decomposed, but it imposes no constraint on which pairs of values co-occur. So the 5NF condition contributes nothing to the expressive question below, and we need only show that keys + UIDs cannot imply symmetry.

What keys and UIDs can express

	•	A key K on R is a uniqueness constraint: no two distinct tuples agree on K. This can eliminate tuples (by merging) but cannot generate a specific new pair.
	•	A unary UID R[A] ⊆ S[B] says: every value appearing in column A of R also appears in column B of S. It is “column-level”: it tracks which values appear somewhere, not which pairs appear together.

The symmetry constraint is fundamentally pair-level: knowing that the pair (a, b) is in R must force the pair (b, a) into R. This pairing cannot be expressed by looking at columns in isolation.

The counterexample

Consider the directed 3-cycle over three distinct constants a, b, c:

I : \quad R = {(a,b),\ (b,c),\ (c,a)}

R is not symmetric — it contains (a, b) but not (b, a).

I satisfies every key on R. The A-values {a, b, c} are all distinct, as are the B-values {b, c, a}, so every possible key (on A, on B, or on {A,B}) is satisfied.

I satisfies every unary UID involving R. Observe

R[A] = {a, b, c} = R[B],

so R[A] ⊆ R[B] and R[B] ⊆ R[A] both hold trivially.

What about UIDs linking R to other relations? Suppose Σ also involves auxiliary relations S₁, …, Sₖ. Start with all Sᵢ = ∅ and run the chase of Σ on I:

	•	UIDs of the form R[A] ⊆ Sᵢ[X] force each value in {a, b, c} to appear in Sᵢ[X]; the chase adds tuples to Sᵢ using fresh labeled nulls for the other column.
	•	UIDs of the form Sᵢ[X] ⊆ R[Y] may then force those labeled nulls back into R[A] or R[B]. But a labeled null is a new value, never equal to a, b, or c; adding it to R adds a tuple like (η, m) or (m, η), never (b, a).
	•	Keys may merge tuples that agree on a key column, but since the fresh nulls are new, no merging collapses η onto an existing constant.

In every round of the chase, the pair (b, a) is never generated in R. The chase terminates (UIDs are weakly acyclic in the unary case) or, if it does not terminate, the core of the result still omits (b, a). Either way, the resulting instance satisfies Σ but violates sym(R).

Why this is unavoidable

The argument generalises: for any n > 2 the directed n-cycle {(1,2), (2,3), …, (n-1, n), (n, 1)} satisfies

	•	all keys (all A-values and B-values are distinct),
	•	all UIDs R[A] ⊆ R[B] and R[B] ⊆ R[A] (both projections equal {1, …, n}),
	•	and any UIDs to/from auxiliary relations (handled by fresh-null witnesses as above),

yet is never symmetric. So no Σ can force sym(R).

The root cause is information-theoretic: deriving (b, a) from (a, b) requires knowing both components simultaneously and reversing them. Unary UIDs are blind to co-occurrence; they see only the marginal distributions of values in each column.

Conclusion

|Constraint type             |What it “sees”                |Can it enforce sym(R)?                                                   |
|----------------------------|------------------------------|-------------------------------------------------------------------------|
|Key on R                    |Uniqueness within a column    |No — only removes duplicates                                             |
|UID R[A] ⊆ S[B]             |Value membership in a column  |No — column-level, not pair-level                                        |
|5NF (JDs from keys)         |Schema decomposition soundness|No — schema design, not data content                                     |
|Symmetry ∀x,y: R(x,y)→R(y,x)|Pair co-occurrence            |Yes, but this is a *binary* full dependency, outside the allowed language|

Therefore, the symmetry of a binary relation cannot be expressed — and we have proved it cannot — within a 5NF schema constrained only by keys and unary inclusion dependencies.
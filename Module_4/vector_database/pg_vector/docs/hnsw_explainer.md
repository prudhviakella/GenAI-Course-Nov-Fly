# HNSW — The Graph-Based Vector Index
### How pgvector Searches Millions of Vectors Using Hierarchical Navigable Small Worlds

---

## Reading Guide

This document builds HNSW from the ground up — starting with why brute-force search fails, then explaining how HNSW is structured, how it gets built, and finally how a query actually travels through it. Each section depends on the one before it, so the order matters.

```
Part 1 — The Problem     : Why brute-force search fails at scale
Part 2 — The Structure   : What the multi-layer graph looks like
Part 3 — Building        : How vectors get inserted and connected (m, ef_construction)
                           Includes: how ef_construction selects candidates from 1000 vectors
Part 4 — Searching       : How a query travels through the graph (ef_search)
                           Includes: one global entry point (not one per layer)
                                     what a greedy hop actually is
                                     the exact stop condition (no threshold)
                                     local minimum trap and why it is acceptable
Part 5 — Measuring       : What recall means and why < 1.0 is acceptable
Part 6 — Configuration   : Operator classes, end-to-end example, summary
```

---

## Part 1 — The Problem: Why Brute-Force Search Fails

After loading your embeddings into pgvector, every RAG query boils down to one operation:

> *"Given this query vector, find the K chunks whose vectors are closest to it."*

This is called **K-Nearest Neighbour (KNN) search**. The naive approach — compare the query against every single vector in the table — is called **exact search** or **brute-force search**. It is perfectly accurate. It is also painfully slow at scale. Understanding exactly *why* it is slow motivates everything that HNSW does to fix it.

### How the Operation Count Is Calculated

Each brute-force query compares the query vector against **every row**, and each comparison costs one multiply-add per dimension. Cosine similarity is computed as:

```
similarity = Σ (query[i] × chunk[i]) for i in range(dimensions)
```

So for every row you perform `dimensions` multiplications and `dimensions` additions:

```
Row 1: [0.12, -0.34, 0.88, ..., 0.41] ← 384 multiply-adds
Row 2: [0.21, 0.11, 0.55, ..., 0.09] ← 384 multiply-adds
...
Row 1000: [...]                        ← 384 multiply-adds

Total = 1,000 × 384 = 384,000 multiply-add operations
```

| Rows | Dimensions | Dominant cost (rows × dims) | What the table shows |
|---|---|---|---|
| 1,000 | 384 | 384,000 operations | dot products only |
| 100,000 | 384 | 38,400,000 operations | dot products only |
| 10,000,000 | 1536 | 15,360,000,000 operations | dot products only |

> **Note:** These numbers are actually understated. Each query also computes two magnitude values (for cosine normalisation), `rows` division operations, and `rows` comparisons to track the top-K result set. The real operation count is roughly 2× the table — the table shows only the dominant term.

### Three Compounding Factors That Make It Slow

The raw operation count is only part of the problem. Three factors compound on each other to make brute-force truly unworkable at scale.

**1. Memory bandwidth — the real bottleneck**

All vectors must be loaded from RAM into CPU cache *before* any arithmetic happens. The CPU cannot compute similarity on data it hasn't read yet:

```
1,000,000 rows × 1536 dimensions × 4 bytes per float = 6 GB of data
that must move through memory for every single query

Memory bandwidth ≈ 50 GB/s on a typical server
→ 6 GB / 50 GB/s = 0.12 seconds just reading the data
  (before a single multiply-add is done)
```

This means even if all arithmetic were instantaneous, a million-vector query would still take 120ms — just from data movement.

**2. Concurrent queries**

A production RAG system handles many users simultaneously. If 100 users query at once and each query needs 15 billion operations, the database is attempting 1.5 trillion operations per second — no hardware handles that without queuing.

**3. Latency budget**

A typical RAG query has a 200ms end-to-end budget (embed + retrieve + LLM generation). Brute-force at scale consumes the entire budget on retrieval alone before the LLM has started.

### The Real-World Viability Threshold

Combining operation count, memory bandwidth, and latency, the practical limits are:

```
< 10,000 rows     → brute-force is fine, no index needed
10,000–100,000    → borderline, depends on query volume
> 100,000 rows    → index required
```

At a million documents, a brute-force search takes seconds per query. A RAG system needs results in milliseconds. The gap is too large to close with faster hardware alone. The solution is to avoid scanning all vectors entirely — which is exactly what an **Approximate Nearest Neighbour (ANN) index** does.

---

## Part 2 — The Structure: How HNSW Organises Vectors

ANN indexes trade a small amount of accuracy for a massive speedup by only searching a *carefully chosen subset* of vectors. HNSW does this using a navigable graph — and to understand how it searches, you first need to understand what it builds.

### The Social Network Intuition

Think about how information spreads in a social network. If you want to reach someone you don't know, you don't message every person on the platform. You message a friend, who knows someone, who knows someone else — and within a few hops you reach the target. This is the "six degrees of separation" idea.

HNSW builds the same kind of navigable network — not of people, but of vectors. Each vector is a node. Each node is connected by edges to its nearest neighbours. To find the vector closest to a query, you start somewhere in the network and hop to closer and closer nodes until you converge on the answer.

The full name — **Hierarchical Navigable Small World** — describes this structure precisely: it is a graph (*navigable small world*) organised in layers (*hierarchical*).

### The Multi-Layer Graph

The key word in the name is *hierarchical*. HNSW doesn't build one flat graph — it builds **multiple layers**, each covering vectors at different levels of density. Picture it like a map at different zoom levels:

```
Layer 2 (highway network — very few nodes, long-range connections):
  v1 ————————————————— v500 ————————————————— v9000

Layer 1 (main roads — more nodes, shorter connections):
  v1 ——— v50 ——— v200 ——— v500 ——— v700 ——— v9000

Layer 0 (local streets — ALL nodes, shortest connections):
  v1 — v3 — v8 — v12 — ... — v500 — v501 — ... — v9000
```

The top layers act like a highway — they cover large distances quickly with few nodes. Layer 0 is the precision layer — it holds every single vector and is where the final answer is found. A query starts at the top (fast, coarse navigation) and descends to layer 0 (slow, precise search).

Two questions immediately arise: *which vectors end up in the upper layers?* and *how many edges does each vector get?* Part 3 answers both — they are both decided at insert time.

---

## Part 3 — Building the Index: Insertion, Layer Assignment, and Connections

When a new vector is inserted into HNSW, three things happen in sequence:
1. A random number decides which layers the vector lives in
2. At each of those layers, the vector finds its nearest neighbours using its actual content
3. Edges are created to those neighbours

Understanding each step explains why the index behaves the way it does at query time.

### Step 1 — Layer Assignment: One Random Number

When vector `v` arrives to be inserted, the code runs exactly this:

```python
import math, random

r = random.random()                     # Step 1: random float between 0.0 and 1.0
mL = 1.0 / math.log(m)                 # Step 2: normalisation factor derived from m
layer_max = int(-math.log(r) * mL)     # Step 3: the highest layer this vector will live in
```

That single integer `layer_max` determines which layers the vector is inserted into:

```
layer_max = 0 → vector lives in layer 0 only
layer_max = 1 → vector lives in layer 0 AND layer 1
layer_max = 2 → vector lives in layer 0, layer 1, AND layer 2
```

**Every vector always lands in layer 0. No exceptions.** Only some get promoted higher — purely by chance.

### What `r` Is — and What It Is Not

`r = random.random()` is a plain random float. It knows **nothing** about the vector's content. It does not look at the vector's 384 numbers. It does not care what the vector means. It does not prefer "important" or "central" vectors.

`r` is purely a **probabilistic gate** — its only job is to answer: *does this vector get promoted to a higher layer, yes or no?*

The vector's actual content plays **zero role** in deciding which layer it goes to. Content is only used *after* the layer is decided — when finding which neighbours to connect to:

```
New vector v = [0.12, -0.34, 0.88, ..., 0.41]  (384 numbers)

Step 1: r = random() → layer_max = 1   ← content NOT used here
                                           purely random gate

Step 2: insert into layer 1
        → compare v's 384 numbers against existing layer 1 vectors
        → find the m nearest by cosine similarity
        → create edges                 ← content IS used here

Step 3: insert into layer 0
        → compare v's 384 numbers against existing layer 0 vectors
        → find the m nearest by cosine similarity
        → create edges                 ← content IS used here
```

### Why `-ln(r)` Produces the Right Distribution

The formula produces an exponential distribution — most vectors land only in layer 0, very few reach higher layers. Here is the math made visible:

```
r value   -ln(r)   layer_max (m=16, mL=0.36)
─────────  ──────   ───────────────────────────
0.99       0.01     0  ← int(0.004) = 0
0.90       0.11     0  ← int(0.040) = 0
0.50       0.69     0  ← int(0.250) = 0
0.10       2.30     0  ← int(0.830) = 0
0.05       3.00     1  ← int(1.080) = 1  ✓ promoted to layer 1
0.01       4.61     1  ← int(1.660) = 1  ✓ promoted to layer 1
0.002      6.22     2  ← int(2.237) = 2  ✓ promoted to layer 2
0.00005    9.90     3  ← int(3.564) = 3  ✓ promoted to layer 3
```

The `-ln` function stretches small values of `r` into large numbers and compresses large values into small ones. Combined with `int()` truncation, the result is an exponential probability drop-off across layers:

```
For m=16, across 10,000 vectors:
  Layer 0 : all 10,000  (100%)   ← every single vector
  Layer 1 : ~630        (~6.3%)  ← only r < 0.063 produce layer_max ≥ 1
  Layer 2 : ~40         (~0.4%)  ← only r < 0.004 produce layer_max ≥ 2
  Layer 3 : ~2          (~0.02%) ← extremely rare
```

This sparse pyramid is intentional. Upper layers need to be sparse so that each hop covers a large distance. If every vector reached layer 2, the "highway" would just be another dense local graph with no navigational advantage.

### Walking Through 10 Insertions

To make the formula concrete, here is what actually happens as 10 vectors arrive one by one:

```
m = 16, mL = 0.36

Vector  r value   -ln(r)  × mL    int   layer_max  Lives in
──────  ───────   ──────  ──────   ───   ─────────  ────────────────────
v1      0.82      0.20    0.07      0    0          L0
v2      0.67      0.40    0.14      0    0          L0
v3      0.91      0.09    0.03      0    0          L0
v4      0.04      3.22    1.16      1    1          L0, L1
v5      0.55      0.60    0.22      0    0          L0
v6      0.78      0.25    0.09      0    0          L0
v7      0.002     6.21    2.24      2    2          L0, L1, L2
v8      0.44      0.82    0.29      0    0          L0
v9      0.33      1.11    0.40      0    0          L0
v10     0.06      2.81    1.01      1    1          L0, L1

Result after 10 insertions:
  Layer 2: v7            (1 vector)
  Layer 1: v4, v7, v10  (3 vectors)
  Layer 0: v1–v10        (all 10)
```

v7 happened to draw `r = 0.002` — a rare small value — so it was promoted all the way to layer 2. v7 is now the **entry point** for all searches: every future query starts at v7 in layer 2. v7 has no special meaning in terms of content. It just got lucky with the random draw. This entry point role becomes important in Part 4.

### Why Random Assignment Works Better Than Semantic Selection

The random selection feels counterintuitive — surely "important" or "central" vectors should be in the upper layers? Random actually works *better* for a geometric reason.

The upper layers exist purely as **navigation shortcuts** — they let search skip large distances quickly. For shortcuts to work well, upper-layer nodes need to be **evenly spread** across the entire vector space so that any neighbourhood can be reached from any direction:

```
Good upper layer (random — evenly spread):
  ·   ·   ·   ·
    ·   ·   ·
  ·   ·   ·   ·
→ Can navigate to any corner of the space in few hops

Bad upper layer (semantic — most common topics dominate):
  · · · · · · ·  ← all clustered in the dense middle
  · · · · · · ·
→ Edges of the space are poorly connected
```

Random selection naturally gives uniform spatial coverage. Any hand-picked semantic selection would over-represent the most common topics and leave rare regions poorly connected. The randomness is a feature, not a compromise.

### Step 2 — Connections: The `m` Parameter

Once a vector's layers are decided, it needs to be *connected* to its neighbours at each layer. This is where `m` comes in.

`m` controls **how many edges each vector gets at each layer it lives in**. It has nothing to do with the random number `r` — it is a fixed configuration parameter set when the index is created:

```sql
CREATE INDEX ON document_chunks USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);
```

The trade-off is straightforward:

```
m = 4  → 4 edges per node  → sparse graph, fewer hops possible → lower recall, very low memory
m = 16 → 16 edges per node → well-connected graph              ← sweet spot (default)
m = 64 → 64 edges per node → very dense graph                  → excellent recall, 4× more memory
```

The default `m=16` comes from the original HNSW research paper — the authors benchmarked across many datasets and found it sits at the sweet spot of speed, recall, and memory for most real workloads.

After inserting v_new with m=16, it connects to its 16 nearest neighbours at each layer. Crucially, connections are **bidirectional** — v_new gets 16 edges out, and each of those 16 neighbours gains an edge back to v_new:

```
Layer 0 after inserting v_new:

  v_003 ←──┐
  v_007 ←──┤
  v_012 ←──┼── v_new  (16 edges total, each to a nearby vector)
  v_019 ←──┤
  v_891 ←──┘  ...
  v_003 also gets an edge pointing back to v_new
```

> **Layer 0 special case:** pgvector doubles the connection count at the base layer to `2m` (so 32 edges for m=16). Layer 0 holds every vector and is where the final precision search happens — the extra connections ensure it stays densely navigable even as the dataset grows.

**Rule of thumb for choosing m:**

| Dataset size | Recommended m |
|---|---|
| < 100K rows | 8 – 16 |
| 100K – 1M rows | 16 – 32 |
| > 1M rows | 32 – 64 |

For a typical document RAG pipeline (tens of thousands of chunks), `m=16` is correct.

### Step 3 — Connection Quality: The `ef_construction` Parameter

Once you know a vector will have `m=16` edges at a given layer, the next question is: *which* 16 neighbours does it connect to? Ideally, the true 16 nearest vectors — but finding them requires a search, and `ef_construction` controls how thorough that search is.

`ef_construction` sets **how many candidates are evaluated before the final `m` neighbours are chosen**. A higher value means a more thorough search — the `m` edges created will be higher quality, producing a better graph that gives higher recall at query time:

```
ef_construction = 32  → considers 32 candidates → picks best 16
                        fast to build, but edges may not be the true nearest
                        lower quality graph → lower recall at query time

ef_construction = 64  → considers 64 candidates → picks best 16  (default)
                        good balance of build speed and edge quality

ef_construction = 200 → considers 200 candidates → picks best 16
                        slow to build, but edges are almost certainly the true nearest
                        highest quality graph → best recall at query time
```

You only pay the build cost once. A higher `ef_construction` is worth it for production indexes.

**Hard rule:** `ef_construction` must always be ≥ `m`. Never set it lower — you'd be asking the algorithm to pick 16 neighbours from fewer than 16 candidates, which is impossible.

### How `ef_construction` Actually Selects Its Candidates

A natural question here: if 1000 vectors already exist when `v_new` arrives, how does `ef_construction=64` pick 64 of them? Does it randomly sample 64 from the 1000?

**No — random sampling would be terrible.** With 1000 vectors and 64 random samples, you would have a 93.6% chance of missing the true nearest neighbour entirely. Instead, `ef_construction` runs a **localised beam search** — starting from wherever the layer above dropped you, and expanding outward through edges until the beam converges. It never sees all 1000 vectors. It only visits the ones reachable by following edges from the starting point. The exact journey that produces that starting point is shown step by step below.

### The Two Lists: Candidate List vs Result Set

The beam maintains two separate lists that are easy to conflate but do completely different jobs:

```
candidate list  → nodes still to be explored       (the frontier — shrinks and grows)
result set      → best nodes found so far           (the answer pool — capped at ef_construction)
```

A node can be in both lists at the same time. The candidate list drives the search forward. The result set accumulates the best discoveries. They are not the same list.

### How v671 Became the Layer 0 Starting Point

Before showing the layer 0 beam search, it is essential to understand how we arrived at v671 — because the starting point is not chosen arbitrarily. It is the direct output of the layer 1 beam search.

`v_new` has `layer_max = 1`, so it lives in layers 0 and 1. The global entry point is `v7` at layer 2. Here is the complete journey from v7 down to the point where the layer 0 beam search begins:

```
═══════════════════════════════════════════════════════════
STEP A — LAYER 2  (v_new does NOT live here — navigate only)
═══════════════════════════════════════════════════════════

Start at v7  ← global entry point, stored in index metadata
              every insertion begins here, just like every query

Greedy hop toward v_new's position:
  examine v7's neighbours: v1, v500, v9000
    v1    distance to v_new : 0.82  ← farther
    v500  distance to v_new : 0.31  ← closer → move
    v9000 distance to v_new : 0.74  ← farther

  now at v500  (current distance to v_new = 0.31 ← this is the new baseline)
  examine v500's neighbours: v7, v9000
    v7    : 0.71  →  0.71 > 0.31  ← farther than current position → do NOT move
    v9000 : 0.74  →  0.74 > 0.31  ← farther than current position → do NOT move
    no neighbour beats 0.31 → STOP at v500
    (0.71 and 0.74 look large, but the question is only:
     are they less than 0.31? they are not → stop)

↓ drop into layer 1 at v500

═══════════════════════════════════════════════════════════
STEP B — LAYER 1  (v_new LIVES here — run beam search)
         starting point: v500  ← where layer 2 greedy stopped
═══════════════════════════════════════════════════════════

ef_construction beam search starts at v500
ef_construction = 64, m = 16

────────────────────────────────────────────────
INITIALISE
────────────────────────────────────────────────
  candidate list : [v500]
  result set     : [v500(0.31)]    ← 1 of 64 slots used, 63 still empty
                                      current worst = 0.31
                                      (when slots are empty, worst = ∞)

THE SINGLE RULE (applies at every iteration):
  add neighbour N if:  distance(N) < current worst in result set
                       OR result set has empty slots
  which is equivalent to:
  add N if:  distance(N) < worst_in_result_set
  where worst starts at ∞ when set is empty and tightens as it fills

────────────────────────────────────────────────
EXPAND (same mechanics as layer 0 — both lists, same rules)
────────────────────────────────────────────────

Iteration 1:
  Take closest from candidate list → C = v500  (0.31)
  result set has 1 of 64 slots used → current worst = 0.31, 63 empty slots
  Examine v500's layer-1 neighbours, compute distance(v_new, each):
    v50  : 0.44  →  0.44 < ∞  (63 empty slots, worst effectively ∞) → add to BOTH
    v200 : 0.28  →  0.28 < ∞  (62 empty slots)                      → add to BOTH
    v700 : 0.18  →  0.18 < ∞  (61 empty slots)                      → add to BOTH
    v4   : 0.39  →  0.39 < ∞  (60 empty slots)                      → add to BOTH
    v10  : 0.52  →  0.52 < ∞  (59 empty slots)                      → add to BOTH
  Mark v500 visited

  Note: v10 (0.52) is added NOT because 0.52 < 0.31, but because
        the result set still has empty slots — no node needs to be
        displaced yet. v10 is a placeholder that will be evicted later
        when better nodes are found and the set is full.

  After iteration 1:
    candidate list : [v700(0.18), v200(0.28), v4(0.39), v50(0.44), v10(0.52)]
    result set     : [v700(0.18), v200(0.28), v500(0.31), v4(0.39), v50(0.44), v10(0.52)]
                      ← 6 of 64 slots used, current worst = v10 at 0.52

Iteration 2:
  Take closest from candidate list → C = v700  (0.18 — closest unvisited)
  result set has 6 of 64 slots → current worst = v10 at 0.52, 58 empty slots
  Examine v700's layer-1 neighbours:
    v680 : 0.14  →  0.14 < 0.52  → add to BOTH
    v720 : 0.16  →  0.16 < 0.52  → add to BOTH
    v650 : 0.22  →  0.22 < 0.52  → add to BOTH
    v389 : 0.33  →  0.33 < 0.52  → add to BOTH  (still empty slots)
    v410 : 0.41  →  0.41 < 0.52  → add to BOTH  (still empty slots)
  Mark v700 visited

  After iteration 2:
    candidate list : [v680(0.14), v720(0.16), v200(0.28), v650(0.22), ...]
    result set     : [v680(0.14), v720(0.16), v700(0.18), v650(0.22),
                      v200(0.28), v500(0.31), v389(0.33), v4(0.39),
                      v50(0.44), v410(0.41), v10(0.52), ...]
                      ← 11 of 64 slots used, current worst = v10 at 0.52

 Iteration 3:
  Take closest from candidate list → C = v680  (0.14)
  result set has 11 of 64 slots → current worst = v10 at 0.52, 53 empty slots
  Examine v680's layer-1 neighbours:
    v671 : 0.11  →  0.11 < 0.52  → add to BOTH
    v690 : 0.13  →  0.13 < 0.52  → add to BOTH
    v660 : 0.19  →  0.19 < 0.52  → add to BOTH
    v700 : 0.18  → already visited → skip
  Mark v680 visited

  candidate list : [v671(0.11), v690(0.13), v720(0.16), v660(0.19), ...]
  result set     : [v671(0.11), v690(0.13), v680(0.14), v720(0.16),
                    v700(0.18), v660(0.19), v650(0.22), v200(0.28), ...]
                    ← 14 of 64 slots, current worst = v10 at 0.52

 Iteration 4:
  Take closest from candidate list → C = v671  (0.11 — closest unvisited)
  result set has 14 of 64 slots → current worst = v10 at 0.52, 50 empty slots
  Examine v671's layer-1 neighbours:
    v672 : 0.12  →  0.12 < 0.52  → add to BOTH
    v670 : 0.13  →  0.13 < 0.52  → add to BOTH
    v680 : 0.14  → already visited → skip
  Mark v671 visited

  Note: v671 is now marked visited (EXPANDED).
        It was rank 1 in the result set, but once expanded and marked visited,
        the beam moves on to the next closest unvisited candidate.

  candidate list : [v690(0.13), v670(0.13), v720(0.16), ...]
  result set     : [v671(0.11), v672(0.12), v690(0.13), v670(0.13),
                    v680(0.14), v720(0.16), v700(0.18), v660(0.19), ...]
                    ← 17 of 64 slots

... beam keeps expanding through many more iterations ...
... result set fills all 64 slots, worst tightens from 0.52 toward ~0.42 ...
... eventually the beam exhausts all candidates that can improve the result set ...

Final iterations (result set now FULL at 64 nodes, worst = 0.42):
  C = some_node  (last useful candidate in the frontier)
  All its neighbours : 0.44, 0.47, 0.51  → all > 0.42 → SKIP all
  Mark visited

CONVERGE:
  Closest remaining in candidate list : 0.45
  64th-best in result set             : 0.42
  0.45 > 0.42 → no remaining candidate can improve the result set → STOP

  The LAST NODE EXPANDED before the stop condition fired = the convergence point.
  The convergence point does not determine the drop-down node.
  The drop-down node is always rank 1 of the result set = v671.


────────────────────────────────────────────────
RESULT SET: 64 best layer-1 candidates found
────────────────────────────────────────────────
  Rank  Node   Distance to v_new
    1   v671   0.11   ← closest found in layer 1
    2   v690   0.13
    3   v680   0.14
    4   v720   0.16
    5   v700   0.18   ← v700 is rank 5, still in top 16
    ...
   16   v200   0.28   ← 16th closest ← CUT HERE  (m = 16)
  ──────────────────────────────────── cutoff
   17   v500   0.31   ← discarded
   ...
   64   v999   0.87   ← discarded

Picks top 16 → wires v_new's layer-1 edges to those 16

DROP-DOWN RULE:
  After the layer 1 beam search converges, take rank 1 from the result set —
  the single closest node found — and use it as the entry point for layer 0.

  result set rank 1 = v671  (distance 0.11 — closest node found in layer 1)
  → drop into layer 0 at v671

  This is the rule at every layer transition:
    beam search converges → take closest from result set → enter next layer there

↓ drop into layer 0 at v671

═══════════════════════════════════════════════════════════
STEP C — LAYER 0  (v_new LIVES here — run beam search)
         starting point: v671  ← rank 1 from layer 1 result set
═══════════════════════════════════════════════════════════
```

Now v671 makes complete sense as the layer 0 starting point. After the layer 1 beam search converges, rank 1 of the result set — the closest node found — becomes the entry point for the layer below. v671 (distance 0.11) was the closest node found in layer 1, so it is where the layer 0 beam search begins.

```
v7    → global entry point (stored, same for every insertion and query)
v500  → layer 2 greedy stop → becomes layer 1 beam search start
v671  → rank 1 of layer 1 result set (closest found) → becomes layer 0 beam search start
```

With that established, here is the layer 0 beam search in full detail:

### Step-by-Step With Both Lists Visible

```
INSERT v_new into layer 0
ef_construction = 64, m = 16
Starting point: v671  ← arrived here via: v7 → layer2 greedy → v500 → layer1 beam → rank1=v671

────────────────────────────────────────────────
STEP 1 — Initialise
────────────────────────────────────────────────
  candidate list : [v671]
  result set     : [v671(0.11)]   ← 1 of 64 slots used, 63 empty
                                     current worst = 0.11

THE SINGLE ADD RULE (same at every iteration):
  add N if: distance(N) < current worst in result set
  when result set has empty slots, worst is effectively ∞
  → every neighbour qualifies until the set is full
  → once full, only nodes that displace the worst get in

────────────────────────────────────────────────
STEP 2 — Expand (repeat until candidate list empty or converged)
────────────────────────────────────────────────

Iteration 1:
  result set: 1 of 64 slots used → current worst = 0.21, 63 empty slots
  Take closest from candidate list → C = v671  (distance 0.11 from v_new)
  Examine v671's 32 neighbours, compute distance(v_new, each):
    v672 : 0.08  →  0.08 < 0.11  → add to BOTH lists
    v670 : 0.09  →  0.09 < 0.11  → add to BOTH lists
    v680 : 0.14  →  0.14 > 0.11  but 63 empty slots → add to BOTH lists
    v690 : 0.13  →  0.13 > 0.11  but 62 empty slots → add to BOTH lists
    v660 : 0.19  →  0.19 > 0.11  but 61 empty slots → add to BOTH lists
  Mark v671 visited

  Note: v680 (0.14), v690 (0.13), v660 (0.19) are added despite being farther
        than v671 (0.11) because the result set still has empty slots.
        They are placeholders — they will be evicted if better nodes arrive.

  After iteration 1:
    candidate list : [v672(0.08), v670(0.09), v690(0.13), v680(0.14), v660(0.19)]
    result set     : [v672(0.08), v670(0.09), v671(0.11), v690(0.13), v680(0.14), v660(0.19)]
                      ← 6 of 64 slots, current worst = v660 at 0.19

Iteration 2:
  result set: 6 of 64 slots → current worst = v467 at 0.31, 58 empty slots
  Take closest from candidate list → C = v512  (0.09 — closest unvisited)
  Examine v512's 32 neighbours:
    v511 : 0.07  →  0.07 < 0.31  → add to BOTH
    v513 : 0.08  →  0.08 < 0.31  → add to BOTH
    v042 : 0.08  →  0.08 < 0.31  → add to BOTH
    v498 : 0.11  →  0.11 < 0.31  → add to BOTH
    v387 : 0.44  →  0.44 > 0.31  but still 54 empty slots → add to BOTH
  Mark v512 visited

  After iteration 2: 11 of 64 slots used, current worst = v387 at 0.44

Iteration 3:
  result set: 11 of 64 slots → current worst = v387 at 0.44
  Take closest from candidate list → C = v511  (0.07)
  Examine v511's 32 neighbours:
    v510 : 0.06  →  0.06 < 0.44  → add to BOTH
    v334 : 0.08  →  0.08 < 0.44  → add to BOTH
    ...
  Mark v511 visited

... beam keeps expanding, result set fills all 64 slots ...

Iteration N  (result set is now FULL at 64 nodes):
  current worst = e.g. v387 at 0.44 (no more empty slots)
  Take closest from candidate list → C = some_node
  Examine its neighbours:
    n1 : 0.04  →  0.04 < 0.44  → add to BOTH, DROP v387 from result set
                                   current worst tightens to next worst
    n2 : 0.95  →  0.95 > 0.44  → SKIP — cannot displace anything
    n3 : 0.88  →  0.88 > 0.44  → SKIP
  Mark C as visited

────────────────────────────────────────────────
STEP 3 — Converge
────────────────────────────────────────────────
  Stop condition fires when:
    closest node remaining in candidate list
    is FARTHER than the worst (64th) node in result set

  Meaning: even if we explored every remaining candidate,
           none of them could displace anything already in result set
           → result set is stable → stop searching

  Example:
    result set 64th-best : distance 0.42
    candidate list closest: distance 0.45
    → 0.45 > 0.42 → no point exploring further → STOP

  result set now holds the 64 best nodes found
```

### Step 4 — Picking the 16 Edges From the 64 Candidates

After convergence, the result set contains 64 nodes ranked by distance to `v_new`. The algorithm simply takes the top 16:

```
Result set — 64 nodes ranked by distance to v_new:

Rank  Node    Distance
  1   v510    0.06   ← closest
  2   v511    0.07
  3   v513    0.08
  4   v042    0.08
  5   v512    0.09
  6   v498    0.11
  7   v389    0.12
  8   v107    0.13
  9   v334    0.14
 10   v601    0.15
 11   v720    0.16
 12   v815    0.17
 13   v042b   0.18
 14   v499    0.19
 15   v503    0.20
 16   v700    0.14   ← 16th closest ← CUT HERE  (m = 16)
──────────────────────────────────────────────── cutoff
 17   v488    0.16   ← discarded — too far
 18   v467    0.18   ← discarded
 ...
 64   v999    0.52   ← discarded
```

Ranks 1–16 become `v_new`'s permanent edges. Ranks 17–64 are discarded — they were useful during the search (they helped the beam navigate outward to better nodes) but `v_new` does not connect to them.

```
v_new gets edges to:
  v675, v673, v672, v670, v671, v674, v510, v690,
  v680, v660, v650, v600, v598, v597, v596, v700

Each of those 16 ALSO gets an edge back to v_new → bidirectional
```

### Why Keep 64 But Only Wire 16?

The 64-candidate pool exists to make sure the 16 you pick are the *true* 16 nearest — not just the first 16 the beam happened to find. The extra candidates are scaffolding for the search, not permanent connections.

```
ef_construction = 16  (= m, minimum allowed)
  → beam finds 16 candidates, picks all 16 as edges
  → but those 16 may not be the true nearest — the beam barely explored
  → poor quality edges → lower recall at query time

ef_construction = 64  (default, 4× m)
  → beam finds 64 candidates, picks the best 16
  → much higher confidence those 16 are the true nearest
  → high quality edges → good recall at query time

ef_construction = 200  (12× m)
  → beam finds 200 candidates, picks the best 16
  → near-certain those 16 are the true nearest
  → best quality edges → highest recall, slow build
```

The ratio `ef_construction / m` is the real quality knob. A ratio of 4× (the default 64/16) is the standard starting point for production.

### Why the Beam Never Needs to See All 1000 Vectors

The beam starts near `v_new`'s neighbourhood (Phase 1 navigation placed it there) and expands only through edges. Because edges were wired to true nearest neighbours at build time, following them reliably stays within the relevant region. Vectors in completely unrelated parts of the graph are never reached — and never need to be.

```
Vectors actually examined during ef_construction=64 beam search:
  ≈ ef_construction × avg neighbours per node
  = 64 × 32
  = ~2,048 distance computations
  (out of 1,000 vectors × 32 edges = 32,000 possible)

Vectors never touched: those in unrelated regions of the graph
```

`ef_construction` controls *how far* the beam expands before committing to its best 64 — not *which* 1000 vectors to randomly sample. A larger beam finds better candidates. A smaller beam is faster but settles for whatever it reached first.

### The Complete Insertion Journey — v7 to v500 to v671

This is the section that ties everything together. Every node named in the beam search examples above has a specific origin — here is where each one comes from and why.

The example uses `v_new` with `layer_max = 1` (lives in layers 0 and 1). The global entry point is `v7` at layer 2. `ef_construction = 64`, `m = 16`.

```
v_new arrives  (layer_max = 1)
Global entry point = v7  (top of layer 2)

═══════════════════════════════════════════════════════
LAYER 2  — traverse only, v_new does NOT live here
           purpose: navigate to a good starting point
═══════════════════════════════════════════════════════

Start at v7  ← this is the GLOBAL entry point, the true beginning
              of every insertion and every query

Greedy hop:
  examine v7's neighbours: v1, v500, v9000
  v1    distance to v_new: 0.82
  v500  distance to v_new: 0.31  ← closest → move
  v9000 distance to v_new: 0.74

  now at v500  (distance to v_new = 0.31 ← new baseline)
  examine v500's neighbours: v7, v9000
    v7    : 0.71  →  0.71 > 0.31  ← farther than current position → do NOT move
    v9000 : 0.74  →  0.74 > 0.31  ← farther than current position → do NOT move
  no neighbour beats 0.31 → STOP at v500

↓ drop into layer 1 at v500

═══════════════════════════════════════════════════════
LAYER 1  — v_new LIVES here → run ef_construction beam search
           starting point: v500  (where layer 2 greedy stopped)
═══════════════════════════════════════════════════════

Beam search starts at v500, ef_construction = 64, m = 16

INITIALISE:
  candidate list : [v500]
  result set     : [v500(0.31)]    ← 1 of 64 slots used, 63 still empty
                                      current worst = ∞ (empty slots mean every neighbour qualifies)

THE SINGLE RULE (same at every iteration, every layer):
  add N if:  distance(N) < current worst in result set
  with empty slots → worst = ∞ → everything qualifies
  once full → only nodes that beat the 64th-best get in

EXPAND — same two-list mechanics as layer 0:

  Iteration 1:
    result set: 1 of 64 slots used → current worst = ∞, 63 empty slots
    C = v500  (0.31 — only candidate)
    Examine v500's layer-1 neighbours:
      v50  : 0.44  →  0.44 < ∞  (63 empty slots) → add to BOTH
      v200 : 0.28  →  0.28 < ∞  (62 empty slots) → add to BOTH
      v700 : 0.18  →  0.18 < ∞  (61 empty slots) → add to BOTH
      v4   : 0.39  →  0.39 < ∞  (60 empty slots) → add to BOTH
      v10  : 0.52  →  0.52 < ∞  (59 empty slots) → add to BOTH
    Mark v500 visited

    v10 (0.52) is added NOT because 0.52 < 0.31 — it is not.
    It is added because 59 empty slots remain — nothing needs displacing yet.
    v10 is a placeholder that will be evicted later once better nodes
    arrive and all 64 slots are occupied.

    candidate list : [v700(0.18), v200(0.28), v4(0.39), v50(0.44), v10(0.52)]
    result set     : [v700(0.18), v200(0.28), v500(0.31), v4(0.39), v50(0.44), v10(0.52)]
                      ← 6 of 64 slots, current worst = v10 at 0.52

  Iteration 2:
    result set: 6 of 64 slots → current worst = v10 at 0.52, 58 empty slots
    C = v700  (0.18 — closest unvisited)
    Examine v700's layer-1 neighbours:
      v680 : 0.14  →  0.14 < 0.52  → add to BOTH
      v720 : 0.16  →  0.16 < 0.52  → add to BOTH
      v650 : 0.22  →  0.22 < 0.52  → add to BOTH
      v389 : 0.33  →  0.33 < 0.52  → add to BOTH  (58 empty slots)
    Mark v700 visited

    candidate list : [v680(0.14), v720(0.16), v200(0.28), v650(0.22), ...]
    result set     : [v680(0.14), v720(0.16), v700(0.18), v650(0.22),
                      v200(0.28), v500(0.31), v389(0.33), v4(0.39), v50(0.44), v10(0.52)]
                      ← 10 of 64 slots, current worst = v10 at 0.52

  Iteration 3:
    result set: 10 of 64 slots → current worst = v10 at 0.52, 54 empty slots
    C = v680  (0.14 — closest unvisited)
    Examine v680's layer-1 neighbours:
      v671 : 0.11  →  0.11 < 0.52  → add to BOTH
      v690 : 0.13  →  0.13 < 0.52  → add to BOTH
      v660 : 0.19  →  0.19 < 0.52  → add to BOTH
    Mark v680 visited

    candidate list : [v671(0.11), v690(0.13), v720(0.16), v660(0.19), ...]
    result set     : [v671(0.11), v690(0.13), v680(0.14), v720(0.16),
                      v700(0.18), v660(0.19), v650(0.22), v200(0.28), v500(0.31), ...]
                      ← 13 of 64 slots, current worst = v10 at 0.52

  Iteration 4:
    result set: 13 of 64 slots → current worst = v10 at 0.52, 51 empty slots
    C = v671  (0.11 — closest unvisited)
    Examine v671's layer-1 neighbours:
      v672 : 0.12  →  0.12 < 0.52  → add to BOTH
      v670 : 0.13  →  0.13 < 0.52  → add to BOTH
      v680 : 0.14  → already visited → skip
    Mark v671 visited

    candidate list : [v690(0.13), v670(0.13), v720(0.16), ...]
    result set     : [v671(0.11), v672(0.12), v690(0.13), v670(0.13),
                      v680(0.14), v720(0.16), v700(0.18), v660(0.19), ...]
                      ← 16 of 64 slots, current worst still v10 at 0.52

  ... beam keeps expanding through many more iterations ...
  ... result set fills all 64 slots, worst tightens from 0.52 toward ~0.42 ...
  ... eventually only nodes near v700's region remain in the candidate list ...

  Final iteration before convergence:
    C = v700_neighbour  (some node at ~0.20, last useful candidate)
    All its neighbours are farther than current result set worst (0.42)
    → nothing added → mark visited

  CONVERGENCE CHECK:
    Closest remaining in candidate list : 0.45
    64th-best in result set             : 0.42
    0.45 > 0.42 → stop condition fires → STOP

  The last node EXPANDED (taken from candidate list and explored) before
  convergence fired is the convergence point → that is the drop-down node.
  In this example: v700  (the beam converged in v700's region of the graph)

  once FULL: any new neighbour farther than the 64th-best is SKIPPED entirely

CONVERGE:
  closest in candidate list (e.g. 0.45) > 64th-best in result set (e.g. 0.42)
  → no remaining candidate can improve the result set → STOP

RESULT SET: 64 best layer-1 nodes ranked by distance to v_new:
  Rank  Node   Distance
    1   v671   0.11   ← closest found in layer 1
    2   v690   0.13
    3   v680   0.14
    4   v720   0.16
    5   v700   0.18
    ...
   16   v200   0.28   ← CUT HERE  (m = 16)
  ──────────────────────────────── cutoff
   17   v500   0.31   ← discarded
   ...
   64   v999   0.87   ← discarded

Picks top 16 → wires v_new's layer-1 edges (bidirectional)

DROP-DOWN RULE:
  After the beam search converges, take rank 1 from the result set —
  the closest node found — and use it as the entry point for the layer below.

  Layer 1 result set rank 1 = v671  (distance 0.11 — closest found)
  → drop into layer 0 at v671

  This is the rule at every layer transition:
    beam converges → rank 1 of result set → entry point for next layer

↓ drop into layer 0 at v671

═══════════════════════════════════════════════════════
LAYER 0  — v_new LIVES here → run ef_construction beam search
           starting point: v671  ← rank 1 of layer 1 result set
═══════════════════════════════════════════════════════

Beam search starts at v671, ef_construction = 64, m = 16
(full iteration detail shown in the "Step-by-Step With Both Lists Visible"
section above — same mechanics, same two lists, same convergence rule)

RESULT SET after convergence: 64 best layer-0 nodes
  picks top 2m = 32  (base layer gets double edges)
  wires v_new's layer-0 edges (bidirectional)

═══════════════════════════════════════════════════════
Done — v_new is permanently wired into the graph
  Layer 1: 16 bidirectional edges
  Layer 0: 32 bidirectional edges
═══════════════════════════════════════════════════════
```

**The three key nodes and exactly where each comes from:**

```
v7    → global entry point stored in index metadata
         every insertion and every query begins here
         (the node that drew r = 0.002 during its own insertion)

v500  → where the layer 2 greedy hop stopped
         becomes the starting point for the layer 1 beam search
         computed fresh every time — not stored anywhere

v700  → where the layer 1 beam search converged
         becomes the starting point for the layer 0 beam search
         computed fresh every time — not stored anywhere
```

**Insertion and search follow the exact same traversal pattern.** This is not a coincidence — it is the same algorithm applied in two contexts:

```
INSERTION of v_new:                    SEARCH for query q:

Start at v7 (global entry point)       Start at v7 (global entry point)
      │                                       │
Greedy hop through layer 2             Greedy hop through layer 2
Stop at v500                           Stop at v500
      │                                       │
ef_construction beam search            Greedy hop through layer 1
in layer 1, starting at v500           Stop at v700
Stop/converge at v700                         │
      │                                ef_search beam search
ef_construction beam search            in layer 0, starting at v700
in layer 0, starting at v700           Converge → return top K
Wire edges from result set
```

The only differences are:
- **Insertion** runs a beam search at every layer v_new lives in and wires edges from the result sets
- **Search** runs greedy hops (not beam search) in upper layers to navigate fast, then one beam search in layer 0 to find the answer
- **Insertion** uses `ef_construction` to size the beam; **search** uses `ef_search`

The traversal mechanics — start at v7, greedy hop down, beam search at the target layer — are identical. Students who understand insertion understand search, and vice versa.

The index is now built — every vector is placed, every connection is wired. The question that remains: when a query arrives, how does it actually travel through this structure to find the nearest vectors?

---

## Part 4 — Searching: How a Query Travels Through the Graph

A query does not scan all vectors — that would be brute-force again. Instead it exploits the same layered structure that was built during insertion. The search has two distinct phases that mirror the two-role design of the graph: fast coarse navigation in the upper layers, then precise local search in layer 0.

### The Entry Point — One Global Node, Not One Per Layer

Every query begins at the **same fixed entry point** — the node sitting at the top of the highest layer. From the 10-insertion example in Part 3, that is `v7` in layer 2 — the vector that happened to draw `r = 0.002`.

```
Current state of the index:

Layer 2:  v7  ←──── THE entry point  (one node, stored in index metadata)
           |
Layer 1:  v4 ── v7 ── v10
           |
Layer 0:  v1 ─ v2 ─ v3 ─ v4 ─ v5 ─ v6 ─ v7 ─ v8 ─ v9 ─ v10
```

There is **no stored entry point for layer 1 or layer 0**. There is only one entry point: `v7` at layer 2. Lower layers are not entered directly — you reach them by traversing down through the layer above.

**How you get into lower layers:** you navigate through each layer using greedy hops, and wherever you stop at layer N becomes your starting position when you drop into layer N-1. That landing node is computed fresh every query — nothing is stored for it.

```
Query arrives
      │
      ▼
Start at v7  (layer 2 — the one global entry point)
Greedy hop to nearest reachable node at layer 2
Stop when no improvement possible
      │
      ▼  drop into layer 1 at the node you stopped at
Start at that node  (NOT a stored entry point — just where you landed)
Greedy hop to nearest reachable node at layer 1
Stop when no improvement possible
      │
      ▼  drop into layer 0 at the node you stopped at
Start at that node  (again, just where you landed)
Run beam search with ef_search candidates
```

Think of it like a building with one front door at the top floor. You always enter through that door, walk to the nearest staircase, go down one floor, walk to the nearest staircase again, and so on. There is no separate door for each floor — there is one door, and the path downward is discovered as you walk.

**When does the entry point change?** Only when a new insertion produces a `layer_max` higher than the current top layer:

```
Current state: top layer = 2, entry point = v7

New vector v_new arrives with layer_max = 3  (very rare)
  → v_new inserted into layers 3, 2, 1, 0
  → layer 3 is brand new — v_new is its only node
  → v_new becomes the new global entry point

Updated state: top layer = 3, entry point = v_new
```

With `m=16` across 10,000 vectors, a layer 3 node appears only ~2 times. The entry point is essentially stable once the index has a few thousand vectors.

Two things follow from having one fixed global entry point:

- All queries start at the same place — the search is deterministic in starting position
- The entry point has no special semantic meaning — it reached the top layer purely by chance, which as we saw in Part 3, is actually desirable for navigational coverage

### Phase 1 — Greedy Descent Through Upper Layers (Fast Navigation)

In every layer **above layer 0**, the algorithm uses a simple greedy rule: look at all neighbours of the current node, move to whichever is closest to the query, stop when no neighbour is closer than the current position.

```
current_node = entry_node  (e.g. v7 at layer 2)

repeat:
    examine all m=16 neighbours of current_node
    find the neighbour closest to the query vector
    if that neighbour is closer → move to it
    if no neighbour is closer  → stop (local minimum)

descend one layer, repeat from the stopping node
```

The goal of Phase 1 is **not** to find the answer — it is to arrive at a good neighbourhood in layer 0 as quickly as possible. Because upper layers are sparse (only ~40 nodes at layer 2 for 10,000 vectors), each hop covers enormous distances. A few hops get us close with very little work.

### What a Greedy Hop Actually Is

When you are standing at a node, you can only see that node's **direct neighbours** — the nodes it has edges to. You have no global view of the layer. You cannot see any other nodes.

A single hop is:

```
1. Look at all neighbours of the current node
2. Compute distance(query, each_neighbour)
3. If any neighbour is closer than the current node → move to the closest one
4. If none is closer → stop
```

Each distance computation is a full cosine distance between two vectors:

```
distance(q, v500) = 1 - cosine_similarity(q, v500)
                  = 1 - (q · v500) / (|q| × |v500|)
                  = 1 - Σ(q[i] × v500[i]) / (|q| × |v500|)
```

For 1536 dimensions, that is 1536 multiplications + 1536 additions — one full dot product per neighbour examined. This is why upper layers being sparse matters: fewer nodes means fewer neighbours per node means fewer dot products per hop.

### The Exact Stop Condition — No Threshold

The stop condition is exact and binary. There is no tolerance, no margin, no "close enough":

```python
if best_neighbour_distance < current_node_distance:
    move to best_neighbour
else:
    stop
```

If even one neighbour is closer by any amount — even `0.0001` — you move. If not a single neighbour strictly beats the current node's distance, you stop immediately.

```
Current node: v500  distance to query = 0.3100

Neighbours:
  v9000: distance = 0.3101  ← 0.0001 farther → do NOT move
  v1:    distance = 0.3099  ← 0.0001 closer  → MOVE

Same node, different neighbours:
  v9000: distance = 0.3101  ← farther
  v1:    distance = 0.3100  ← exactly equal  → do NOT move (not strictly less than)

Another case:
  v9000: distance = 0.9900  ← much farther
  v1:    distance = 0.3099  ← only 0.0001 closer → still MOVE
```

The algorithm does not care about the magnitude of improvement. Any strictly smaller distance triggers a move.

### What Causes the Stop

The stop happens purely because of **how edges were wired at build time**. When `v500` was inserted, its `m=16` edges were connected to its nearest neighbours in that layer — vectors close to `v500` in space, not necessarily close to an arbitrary query `q`.

If query `q` happens to be in a different direction than all of `v500`'s neighbours, none of them will beat `v500`'s distance, and the algorithm stops:

```
Layer 2 graph:

  v1 ──── v500 ──── v9000   ← v500's neighbours: v1 and v9000

                q  is directly "below" v500 in vector space
                   v500 is the closest node to q in this layer
                   → correct stop, descend to layer 1
```

This is the correct behaviour — it means v500 is already in the right region and descending gives layer 1 the chance to refine further.

### When the Stop Is Wrong — Local Minimum Trap

The stop can also fire when you are *not* at the true closest node in the layer — you are just at a node whose immediate neighbours all happen to point the wrong way:

```
Layer 2:

  v1 ──── v500 ──── v9000
                       │
                     v_closer  ← genuinely closer to q than v500
                                  but v500 has no edge to v_closer
                                  → condition never fires for it
                                  → stop at v500 even though v500 is wrong
```

This is a genuine local minimum trap. The greedy algorithm accepts it and moves on. This is not treated as a critical failure for two reasons:

**1. Upper layers are navigation only.** A slightly wrong stopping point at layer 2 just means you enter layer 1 from a slightly off position. Layer 1 has more nodes and more edges — giving you another chance to correct course. Layer 0 then runs a full beam search that explores `ef_search` candidates simultaneously, largely recovering from any poor upper-layer navigation.

**2. The trap is rare.** Because edges point to true nearest neighbours, following them almost always moves toward the query's region. And recall — which we measure in Part 5 — directly captures how often the final answer is still correct despite any navigation imprecision.

### Why Greedy Works Despite Being Blind

The greedy hop looks blind — you only see immediate neighbours, no map. But it works reliably because of how edges were wired during insertion. When `v500` was inserted, its edges were connected to its `m=16` nearest neighbours. So `v500`'s neighbour list is not random — it is a curated set of the closest vectors to `v500` in the space.

```
Why greedy works:
  v500's neighbours ≈ vectors near v500 in space
  Query q is near v700 in space
  v700 is near v500 → v700 appears in v500's neighbour list
  → greedy correctly moves v500 → v700

The graph's structure does the navigation.
The greedy rule just follows it.
```

### The Concrete Walk-Through

```
Query: [0.12, -0.34, 0.88, ...]

Layer 2 graph (edges wired at build time):
  v7 ──── v500
  │          │
  v1       v9000

─────────────────────────────────────
Position: v7  (distance to query = 0.71)

Examine v7's neighbours:
  v500: distance = 0.31  ← closer than 0.71 → candidate to move
  v1:   distance = 0.82  ← farther than 0.71

Best neighbour v500 (0.31) < current v7 (0.71) → MOVE to v500

─────────────────────────────────────
Position: v500  (distance to query = 0.31 ← this is now the baseline)

Examine v500's neighbours:
  v7:    distance = 0.71  →  0.71 > 0.31  ← farther than current position → do NOT move
  v9000: distance = 0.74  →  0.74 > 0.31  ← farther than current position → do NOT move

No neighbour beats 0.31 → STOP
(the question is never "is 0.71 large?" — it is only "is 0.71 < 0.31?" — it is not)

Drop into layer 1 at v500
─────────────────────────────────────

Layer 1:
Position: v500  (distance to query = 0.31 ← baseline resets again)

Examine v500's neighbours: v50, v200, v700, v4, v10
  v50:  0.44  →  0.44 > 0.31  ← farther
  v200: 0.28  →  0.28 < 0.31  ← closer → candidate
  v700: 0.18  →  0.18 < 0.31  ← closest → best candidate
  v4:   0.39  →  0.39 > 0.31  ← farther
  v10:  0.52  →  0.52 > 0.31  ← farther

Best neighbour v700 (0.18) < current v500 (0.31) → MOVE to v700

─────────────────────────────────────
Position: v700  (distance to query = 0.18 ← new baseline)

Examine v700's neighbours: v500, v650, v720, v389
  v500: 0.31  →  0.31 > 0.18  ← farther
  v650: 0.22  →  0.22 > 0.18  ← farther
  v720: 0.19  →  0.19 > 0.18  ← farther
  v389: 0.20  →  0.20 > 0.18  ← farther

No neighbour beats 0.18 → STOP

Drop into layer 0 at v700
─────────────────────────────────────
```

Two layers, ~10 distance computations total. Phase 1 is done. Layer 0 beam search begins from v700.

### Phase 2 — Beam Search in Layer 0 (Precise Search)

Layer 0 is where all vectors live and where precision is needed. The greedy single-node approach used in Phase 1 would get stuck at local minima here — it could miss the true nearest neighbour because a slightly farther node leads to much better results if explored further.

Instead, Phase 2 uses **beam search**: rather than tracking a single current node, it tracks a list of the best `ef_search` candidates simultaneously and expands them all:

```
ef_search = 40  (default — configured with: SET hnsw.ef_search = 40)

Enter layer 0 at v700
Initialise candidate list : [v700]
Initialise result set      : [v700]

while candidate list is not empty:
    take the closest unvisited candidate → call it C
    examine all 2m=32 neighbours of C in layer 0
    for each neighbour N:
        if N is closer than the furthest node in result set:
            add N to candidate list
            add N to result set
            if result set size > ef_search: drop the furthest
    mark C as visited

When no candidate can improve the result set → stop
Return the top K from the result set
```

The beam expands outward from v700, pulling in closer and closer nodes, pruning anything that falls outside the top `ef_search` at each step. It converges naturally — once the frontier of candidates cannot beat the worst node already in the result set, the search terminates.

```
ef_search = 40 means:
  → tracking 40 best candidates simultaneously
  → exploring each candidate's 32 neighbours
  → continuously pruning anything outside the top 40

Final result set holds the 40 best nodes found
Return the top K from those 40  (e.g. LIMIT 5 → return the 5 closest)
```

### Why Phase 1 is Greedy but Phase 2 is Beam Search

The two phases use different strategies for the same underlying reason: the structure of each layer demands it.

| Phase | Layer | Strategy | Why |
|---|---|---|---|
| Phase 1 | Upper layers (≥1) | Greedy, single-node | Very few nodes — any path gets close quickly, precision not needed |
| Phase 2 | Layer 0 | Beam search, `ef_search` candidates | All vectors present — greedy gets stuck, must explore multiple paths |

The handoff between them — the entry point into layer 0 — is what makes the overall search efficient. Phase 1 delivers a starting point that is already in the right neighbourhood; Phase 2 does the careful local work from there rather than from a random position.

### The `ef_search` Parameter: Tuning the Trade-off

`ef_search` is the only search parameter that can be changed without rebuilding the index — it is a session-level setting:

```sql
SET hnsw.ef_search = 40;    -- default
SET hnsw.ef_search = 10;    -- faster, lower recall
SET hnsw.ef_search = 200;   -- slower, higher recall
```

What it controls is the size of the beam in Phase 2 — how many candidates are tracked simultaneously in layer 0:

```
ef_search = 10
  → beam tracks 10 candidates → small neighbourhood explored
  → fast, but may miss true nearest neighbours → lower recall

ef_search = 40  (default)
  → beam tracks 40 candidates → good balance of coverage and speed

ef_search = 200
  → beam tracks 200 candidates → very thorough local search
  → near-brute-force quality in the neighbourhood → high recall, slower
```

One hard rule: **`ef_search` must always be ≥ K** (the number of results you are requesting). If you run `LIMIT 5` but `ef_search = 3`, the beam only ever tracked 3 candidates — it cannot produce 5 meaningful results.

Because `ef_search` is per-session, you can tune it per query type without touching the index:

```sql
-- High-stakes query: maximise recall
SET hnsw.ef_search = 100;
SELECT content FROM document_chunks
ORDER BY embedding <=> $query LIMIT 5;

-- Real-time query: minimise latency
SET hnsw.ef_search = 20;
SELECT content FROM document_chunks
ORDER BY embedding <=> $query LIMIT 5;
```

### Full Query Trace: Both Phases Together

```
Query vector q = [0.12, -0.34, 0.88, ...]
K = 5  (LIMIT 5),  ef_search = 40

───────────────────────────────────────────────────
PHASE 1  ·  Navigate upper layers  ·  Fast
───────────────────────────────────────────────────

Layer 2:  start at v7 (entry point)
          check v7's 16 neighbours → closest is v500
          move to v500
          check v500's 16 neighbours → no improvement
          stop at v500

Layer 1:  enter at v500
          check v500's 16 neighbours → closest is v700
          move to v700
          check v700's 16 neighbours → no improvement
          stop at v700

          → v700 handed off to Phase 2

───────────────────────────────────────────────────
PHASE 2  ·  Beam search in layer 0  ·  Precise
───────────────────────────────────────────────────

Enter at v700, ef_search = 40
Expand frontier, track top-40 candidates
Explore neighbours of neighbours, prune continuously
Converge when no candidate can improve the result set

Result set (top 40 found in the neighbourhood):
  v512  distance 0.06  ← closest
  v389  distance 0.09
  v107  distance 0.12
  v042  distance 0.15
  v601  distance 0.17  ← 5th closest
  v891  distance 0.18
  ...  (35 more explored but outside final top 5)

───────────────────────────────────────────────────
Return top 5:  v512, v389, v107, v042, v601
───────────────────────────────────────────────────
```

### Why This Is Fast: The Complexity Picture

```
Phase 1 (upper layers):
  O(log N) hops × m=16 comparisons per hop → very cheap

Phase 2 (layer 0):
  ef_search candidates × 2m=32 neighbours each
  → cost is bounded by ef_search, not by N

Total per query:
  O(log N × m  +  ef_search × m)

Compare to brute-force:
  O(N × dimensions)
```

For 1,000,000 vectors with m=16, ef_search=40, 1536 dimensions:

```
HNSW:        (20 × 16) + (40 × 32) × 1536 ≈ 2,000,000 operations
Brute-force: 1,000,000 × 1536             ≈ 1,500,000,000 operations
```

That is a **750× reduction in work** per query — which is why a brute-force query taking seconds becomes a sub-10ms query with HNSW.

The logarithmic behaviour of Phase 1 comes from the "small world" property introduced in Part 2: because upper-layer membership is random and exponentially sparse, any node can be reached from any other in O(log N) hops. This is the formal guarantee that makes HNSW scale to millions of vectors without degrading.

---

## Part 5 — Measuring: What "Recall" Actually Means

HNSW is fast precisely because it skips most vectors. The cost of that skip is that it might occasionally miss one of the true nearest neighbours — returning the 6th-closest result instead of the 5th. Recall is the metric that quantifies how often this happens.

### The Definition

> **Recall** = the fraction of the true nearest neighbours that the approximate index actually returns.

"True nearest neighbours" means what a perfect brute-force search would have returned. Recall is measured by comparing HNSW's output against that ground truth:

```
           results returned that were in the true top-K
Recall@K = ───────────────────────────────────────────
                               K
```

### A Concrete Example

Say you query for the top-5 most similar chunks. Brute-force would return:

```
Exact top-5 (ground truth):
  Rank 1: chunk_042  similarity=0.94
  Rank 2: chunk_107  similarity=0.91
  Rank 3: chunk_389  similarity=0.88
  Rank 4: chunk_012  similarity=0.85
  Rank 5: chunk_601  similarity=0.83
```

Your HNSW index returns:

```
Approximate top-5:
  chunk_042  ✓  (rank 1 — correct)
  chunk_107  ✓  (rank 2 — correct)
  chunk_389  ✓  (rank 3 — correct)
  chunk_012  ✓  (rank 4 — correct)
  chunk_891  ✗  (not in ground truth — missed chunk_601)

Recall@5 = 4 correct out of 5 = 0.80  (80%)
```

### The @K Notation

| Notation | Meaning |
|---|---|
| Recall@1 | Did the index return the single closest vector? |
| Recall@5 | Of the 5 results returned, how many were in the true top-5? |
| Recall@10 | Of the 10 results returned, how many were in the true top-10? |

Higher K is usually easier to achieve — more slots means fewer misses matter. Recall@10 is almost always higher than Recall@1 for the same index settings.

### Typical Values in Practice

| Index | Typical Recall@10 |
|---|---|
| Brute-force (exact) | 1.00 — always perfect |
| HNSW (default settings) | 0.95 – 0.99 |
| HNSW (low `ef_search`) | 0.85 – 0.92 |

### Why Recall < 1.0 Is Acceptable for RAG

In the example above, HNSW missed `chunk_601` (similarity 0.83) and returned `chunk_891` (similarity ~0.82) instead — the two are nearly identical in relevance. An LLM generating an answer from these 5 chunks will produce the same response either way.

**The scenario where low recall actually hurts** is when the only chunk containing the answer falls outside what `ef_search` can reach in Phase 2. If the answer lives in `chunk_601` (rank 5) and `ef_search` is too low to find it, you will miss it entirely. This connects directly back to Part 4: increasing `ef_search` expands the beam in Phase 2, which raises recall at the cost of more comparisons. The two knobs — speed and accuracy — are one and the same knob.

### The Speed–Recall Trade-off

```
High recall
  ↑
  │  ● Brute-force (always 1.0, always slow)
  │
  │  ● HNSW ef_search=200
  │
  │  ● HNSW ef_search=40 (default)
  │
  │  ● HNSW ef_search=10
  │
  └──────────────────────────────→ High speed
```

For most RAG pipelines, **Recall@10 ≥ 0.90** with query latency under 50ms is the practical target. Default settings (`m=16, ef_construction=64, ef_search=40`) typically deliver Recall@10 ≈ 0.97 at well under 10ms for datasets up to a few million rows.

---

## Part 6 — Configuration and Putting It All Together

### The `vector_cosine_ops` Operator Class

When creating the index, you specify which distance function HNSW uses for all comparisons — both at build time (connecting neighbours) and at query time (traversing the graph):

```sql
CREATE INDEX ON document_chunks USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);
```

| Operator class | Distance metric | Use when |
|---|---|---|
| `vector_cosine_ops` | Cosine distance (1 − cosine similarity) | Embeddings (normalised or unnormalised) |
| `vector_l2_ops` | Euclidean distance (straight-line) | Raw feature vectors |
| `vector_ip_ops` | Inner product (negative dot product) | Normalised embeddings only |

For embedding-based RAG, `vector_cosine_ops` is the right choice. The query operator must match the index operator class or the index will not be used:

```sql
embedding <=> query_vector  -- cosine distance     → use with vector_cosine_ops
embedding <-> query_vector  -- euclidean distance  → use with vector_l2_ops
embedding <#> query_vector  -- negative dot product → use with vector_ip_ops
```

If your embeddings are L2-normalised (`normalize=True`), cosine similarity equals dot product — so `vector_cosine_ops` and `vector_ip_ops` give identical results. `vector_cosine_ops` is the safer default because it works correctly even when vectors are not normalised.

### HNSW vs Other Indexes: When to Use It

```
Build time  : Slower (more time + memory than IVFFlat)
Memory      : Higher (full graph must fit in RAM for best performance)
Query speed : Faster than IVFFlat
Recall      : Higher than IVFFlat at the same speed setting
Inserts     : Handled natively — no reindex needed
Best for    : Production RAG, quality-critical retrieval, growing datasets
```

The main reason to choose HNSW over alternatives is that it handles **new inserts natively** — each new vector is wired into the existing graph at insert time without rebuilding anything. IVFFlat requires periodic reindexing as new data arrives, making it awkward for datasets that grow continuously, which is most production RAG pipelines.

### End-to-End RAG Query Example

Everything from Parts 1–6 comes together in a single query:

```
User: "What was the revenue growth in Q3?"

Step 1 — Embed the query
  query_vector = model.encode("What was the revenue growth in Q3?")
  → [0.12, -0.34, 0.88, ..., 0.41]

Step 2 — Search pgvector
  SELECT content, 1 - (embedding <=> query_vector::vector) AS similarity
  FROM public.document_chunks
  ORDER BY embedding <=> query_vector::vector
  LIMIT 5;

  What HNSW does internally:

  Phase 1: Enter graph at v7 (top-layer entry point, set at index build time)
           Greedy hop through layer 2 → layer 1
           Arrive at v700 as layer 0 entry point
           (~32 comparisons total)

  Phase 2: Beam search in layer 0 from v700
           Track top ef_search=40 candidates
           Expand frontier, prune continuously
           Converge on the nearest neighbourhood
           (~1,280 comparisons total)

  Total work: ~1,300 comparisons vs 1.5 billion for brute-force

Step 3 — Retrieved chunks (with similarity scores)
  0.94  "Q3 revenue grew 12% year-on-year, driven by Asia-Pacific..."
  0.91  "Asia-Pacific segment contributed $2.3B in Q3, up from..."
  0.88  "Revenue targets for Q3 were set at $8.1B globally..."
  0.72  "Quarterly earnings call transcript, Q3 2024..."
  0.69  "FY2024 guidance revised upward following Q3 results..."

Step 4 — LLM generates answer from retrieved context
  "Revenue grew 12% year-on-year in Q3, driven by strong Asia-Pacific
   performance which contributed $2.3B..."
```

---

## Summary

### Parameter Quick Reference

| Parameter | Set at | Controls | Rule of thumb |
|---|---|---|---|
| `m` | Index creation | Edges per node per layer | 16 for most RAG pipelines; raise for >1M rows |
| `ef_construction` | Index creation | Candidates considered when wiring edges | Always ≥ m; 64 default, 200 for production |
| `ef_search` | Query time | Candidates tracked in layer 0 beam search | Always ≥ K; raise for high-stakes queries |

### Concept Reference

| Concept | One-line explanation |
|---|---|
| **KNN search** | Find the K vectors closest in meaning to a query vector |
| **Brute-force** | Compare query against every vector — exact but O(N × dims), too slow at scale |
| **ANN search** | Find *close enough* results fast by trading a little accuracy for a lot of speed |
| **HNSW** | Multi-layer navigable graph — descend from coarse to precise to find nearest neighbours |
| **Layer 0** | Every vector, always — the dense precision layer where the final beam search runs |
| **Layer 1+** | Random sparse subset — highway layers traversed by greedy hops |
| **`r`** | Random float at insert time; decides layer promotion — knows nothing about vector content |
| **`layer_max`** | Highest layer a vector lives in — computed as `int(-ln(r) × mL)` |
| **Entry point** | One global node at the top of the highest layer — fixed start for every query AND every insertion; not one per layer |
| **Greedy hop** | Look at current node's direct neighbours only, move to the closest one, stop if none is closer |
| **Stop condition** | Exact binary — stop when no neighbour's distance is strictly less than current; no threshold |
| **Local minimum** | A stop before the true nearest node — acceptable because the beam search at the next layer recovers |
| **Per-layer starting point** | The node where the layer above's traversal stopped — computed fresh each time, never stored |
| **Insertion = Search** | Both start at v7, greedy hop through upper layers, beam search at target layer — same traversal mechanics |
| **v7 → v500 → v700** | v7 = global entry point; v500 = where layer 2 greedy stopped; v700 = where layer 1 beam ended — each feeds the next |
| **ef_construction candidates** | Found via localised beam search from the per-layer starting point — never random sampling from all N vectors |
| **Why 64 but wire 16** | 64-candidate pool ensures the 16 picked are the true nearest; ranks 17–64 scaffolded the search only |
| **Phase 1 (search)** | Greedy single-node descent through upper layers — fast coarse navigation to a good neighbourhood |
| **Phase 2 (search)** | Beam search with `ef_search` candidates in layer 0 — thorough local search for the final answer |
| **Recall@K** | Fraction of true top-K nearest neighbours the index actually returned |
| **`vector_cosine_ops`** | Use cosine distance — correct choice for L2-normalised embeddings |
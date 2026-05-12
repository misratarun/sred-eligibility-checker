# SR&ED Sample Test Queries

Five realistic queries designed to exercise different classification outcomes.

---

## 1. ELIGIBLE — Systematic ML Model Uncertainty

```
We spent 14 months developing a novel graph neural network architecture for
predicting cascade failures in power grid topology. Existing GNN models
performed well on static graphs but failed under dynamic edge-weight conditions
that reflect real-time load balancing. No published architecture addressed this
combination of constraints. We ran over 200 controlled experiments, varying
message-passing depth, attention heads, and temporal encoding strategies,
maintaining hypothesis logs, experiment tracking via MLflow, and systematic
ablation studies. The final architecture outperformed baselines by 31% on held-
out grid simulation data, and the methodology was submitted to a peer-reviewed
venue.
```

**Expected classification:** ELIGIBLE
**Why:** Clearly documents technological uncertainty (no existing solution), systematic
investigation (controlled experiments, logs, ablation studies), and technological
advancement (novel architecture with measurable improvement submitted for peer review).

---

## 2. LIKELY ELIGIBLE — Custom Tooling With Uncertainty

```
Our team built a custom distributed tracing framework for microservices written
in Rust. Existing solutions like Jaeger and Zipkin introduced unacceptable
latency overhead (>8ms per traced request) in our high-frequency trading
environment where end-to-end latency budgets are under 2ms. We investigated
whether lock-free ring buffers combined with asynchronous batch flushing could
meet our constraints. After 3 months of prototype iterations and benchmarking,
we developed a working solution that operates within budget. Some design choices
were informed by published systems research papers.
```

**Expected classification:** LIKELY ELIGIBLE
**Why:** Genuine technological uncertainty exists (known tools failed the constraint),
and a systematic investigation was conducted. However, the approach drew heavily from
existing published research, which slightly reduces the "advancement" claim. Minor
documentation gaps around hypothesis formulation could weaken the file.

---

## 3. BORDERLINE — Optimization Work, Unclear Advancement

```
We optimized our PostgreSQL query planner by rewriting several critical analytical
queries using window functions and materialized CTEs. We benchmarked before and
after, reducing average query time from 4.2 seconds to 0.6 seconds on our largest
tables. We also tuned memory allocation settings and created custom indexes based
on query explain plans. Most of this was standard database tuning practice, but one
query required a non-obvious join reordering that we had not encountered in
documentation.
```

**Expected classification:** BORDERLINE
**Why:** Primarily routine database optimization using well-documented techniques.
The one novel join reordering is insufficient on its own. The work lacks evidence of
systematic investigation beyond ad hoc tuning and does not clearly advance general
technological knowledge.

---

## 4. NOT ELIGIBLE — Routine Software Development

```
We built a REST API using FastAPI to expose our internal customer data to a new
mobile app. The API handles CRUD operations for user profiles, order history, and
preferences. We used standard JWT authentication, rate limiting with Redis, and
deployed to AWS ECS with auto-scaling. The project took 6 weeks and involved three
engineers. We followed well-established architectural patterns throughout.
```

**Expected classification:** NOT ELIGIBLE
**Why:** This describes standard software development using established frameworks,
patterns, and services. There is no technological uncertainty — the engineering
challenge is one of execution, not knowledge advancement. No new scientific or
technological knowledge was generated.

---

## 5. EDGE CASE — Porting Existing Algorithms to a New Domain

```
We adapted the DBSCAN clustering algorithm, originally designed for spatial data,
to detect anomalous behavior patterns in time-series network traffic logs. The core
algorithm was well understood, but applying it to high-dimensional, non-Euclidean
event sequences required us to define a custom distance metric based on edit
distance and temporal weighting. We experimented with four distance function
variants over two months, with mixed results. The adapted approach worked for our
dataset but we are uncertain whether the distance metric generalizes beyond our
specific traffic patterns.
```

**Expected classification:** LIKELY ELIGIBLE or BORDERLINE
**Why:** This is a genuine edge case. The base algorithm is known, but the domain
adaptation required novel problem-solving (custom distance metric). The uncertainty
about generalizability cuts both ways — it suggests genuine technological uncertainty,
but also means the advancement claim is weaker. The CRA would likely ask for more
documentation on the experimental protocol and whether the uncertainty was
technological (not just domain-specific configuration).

# Abstract Sketch

Graph-structured world models often score imagined futures using only the constraints encoded in the learned graph. We study a controlled failure mode for inference-time Best-of-N selection: as the number of sampled futures grows, the selected future can move into a high-score tail that exploits missing graph constraints, improving imagined physics score while reducing executed utility. We give a finite tie-aware Best-of-N law for scored candidate pools, validate it empirically, and test lightweight graph-energy and constraint-probe repairs in a CPU-only synthetic mass-spring setting. The evidence is intentionally scoped to toy graph physics and does not claim real-robot or broad benchmark validation.


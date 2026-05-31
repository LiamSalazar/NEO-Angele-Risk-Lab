# Frontend Product Refinement

The frontend is organized as an analytical observatory rather than a generic pipeline monitor. The visible navigation is:

- Control Panel
- Risk Ranking
- Object Profile
- Score Simulation
- Orbital Simulation
- Orbital Graph
- Findings
- Methodology

The removed navigation items, Domain Explorer and Pipeline Monitor, are intentionally absent from the final product surface. Their backend capabilities can remain available for engineering use, but the user-facing app focuses on object risk analysis, simulations, graph context, and conclusions.

## Product Roles

- Control Panel: operational summary of dataset, risk, simulations, graph, and model evidence.
- Risk Ranking: sortable review queue with PHA filter, score threshold, drivers, and model evidence.
- Object Profile: single-object context with score components, simulation evidence, graph neighbors, and model evidence.
- Score Simulation: Monte Carlo stability of the Risk Priority Score.
- Orbital Simulation: approximate orbital clone scenarios and distance bands.
- Orbital Graph: orbital-neighborhood graph, enriched nearest neighbors, and graph model evidence.
- Findings: narrative conclusions grouped by analytical source.
- Methodology: transparent explanation of data sources, scoring, simulation, graph, and model caveats.

---
theme: alex
colorSchema: light
transition: none
canvasWidth: 1920
aspectRatio: '16/9'
copyright: © Alexandra Institute
date: 2026-11-19
title: GridFM Demo
layout: modern-cover
variant: generic
subtitle: Federated training of a power grid foundation model on HPC
---

---
layout: modern-content
title: Agenda
---

1. Background
   - Why a foundation model for the grid
   - Why federated learning
   - Why HPC
2. The demo
   - The clients and their data
   - The three models and the results
3. Next steps

---
layout: modern-section
title: Background
---

---
layout: modern-blue-box
title: A foundation model for the grid
---

- Renewables and electrification make the grid harder to operate, with more
  scenarios to consider than today's solvers can handle
- <img src="/logos/opengridfm.png" class="h-16" />GridFM: one model, pre-trained on many grids, that adapts to new grids and tasks
- <img src="/logos/datakit.png" class="h-16" />gridfm-datakit makes the data
- <img src="/logos/graphkit.png" class="h-16" />gridfm-graphkit trains the models

---
layout: modern-blue-box
title: Why federated learning?
---

### The problem

- GridFM needs real data from many grids
- Operators cannot share data: security, regulation, competition

### The idea

- Each operator trains on its own data, and only updates to model weights are shared with an orchestrator
- <img src="/logos/flower-mark.png" class="h-16" />Flower: open-source federated learning framework

---
layout: modern-blue-box
title: How federated learning works
---

<img src="/images/federation.png" class="w-full" />

---
layout: modern-blue-box
title: Why this needs HPC
---

- Generating synthetic data is computationally heavy
- Clients may not have enough compute to train the model themselves

---
layout: modern-section
title: The demo
---

---
layout: modern-blue-box
title: The clients
---

Each client has its own synthetic grid data (made with gridfm-datakit).

- Client 1 has a grid with 500 nodes
- Client 2 has a grid with 588 nodes
- Each has 2,000 scenarios
  - 500 demand scenarios
  - 4 network variants with one line or generator switched off in each variant
- A third grid with 300 nodes is used only for testing

<img src="/images/grids.png" class="w-full mt-4" />

---
layout: modern-blue-box
title: The results
---

Error in the predicted voltage level, on data held out from training. Lower is better.

<table class="results">
  <thead>
    <tr><th>Model</th><th>500-node grid</th><th>588-node grid</th><th>300-node grid</th></tr>
  </thead>
  <tbody>
    <tr><td>Federated</td><td class="seen">2.7 × 10<sup>−4</sup></td><td class="seen">3.8 × 10<sup>−4</sup></td><td class="unseen">3.0 × 10<sup>−3</sup></td></tr>
    <tr><td>Isolated 1</td><td class="seen">1.4 × 10<sup>−4</sup></td><td class="unseen">1.1 × 10<sup>−3</sup></td><td class="unseen">2.1 × 10<sup>−3</sup></td></tr>
    <tr><td>Isolated 2</td><td class="unseen">6.7 × 10<sup>−4</sup></td><td class="seen">5.2 × 10<sup>−4</sup></td><td class="unseen">3.5 × 10<sup>−3</sup></td></tr>
  </tbody>
</table>

<span class="chip seen"></span> train
<span class="chip unseen"></span> unseen

- The federated model is the only one that does well on both clients' grids
- On the unseen 300-node grid all are 7 to 15 times worse, and seeing both grids did
  not clearly help
- One training run per model

All experiments use the same model size and early-stopping criteria.

---
layout: modern-contact
title: Get in touch
---

Michael Iversen

michael.iversen@alexandra.dk

::right::

Etienne Bourbeau

etienne.bourbeau@alexandra.dk

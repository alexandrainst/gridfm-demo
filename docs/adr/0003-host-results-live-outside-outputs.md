---
status: accepted
date: 2026-10-08
---

# Only the Federation Writes `outputs/`; Results Made on the Host Go Elsewhere

## Context and Problem Statement

The ServerApp container writes each run's outputs to
`outputs/<federation>/<experiment>/<timestamp>/`, which is mounted from the host. The
container runs as root, so the run folders belong to root and the host user cannot write
into them. Where do results that the host computes from a run, such as predictions, go?

## Considered Options

- Write them to a separate tree on the host that mirrors `outputs/`, such as
  `predictions/<federation>/<experiment>/<timestamp>/`.
- Run the ServerApp as the host user, so that run folders are writable on the host.

## Decision Outcome

Chosen option: "A separate tree that mirrors `outputs/`", because it needs no change to
the federation and works for every existing run. Running the ServerApp as the host user
would need the user's IDs in every Compose file and would leave existing runs
unwritable.

Only the federation writes to `outputs/`. Every result the host makes from a run goes to
its own top-level folder with the same `<federation>/<experiment>/<timestamp>/` layout.

### Consequences

- Good, because a run's outputs are never changed after the run, so they always show
  what the federation produced.
- Good, because host results can be deleted and recomputed without touching the runs.
- Bad, because a run's results are spread over two folders that tools must join by path.

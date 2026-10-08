# Architectural Decision Records

This folder records the architectural decisions of the project, one decision per file,
in the [MADR](https://adr.github.io/madr/) format.

## Writing a Record

1. Copy `template.md` to `NNNN-title-with-dashes.md`, where `NNNN` is the next free
   number, e.g., `0001-keep-experiment-config-in-python.md`.
2. Fill in the sections and set `status` to `proposed`.
3. Set `status` to `accepted` once the decision is agreed on.

Records are not edited after they are accepted. To change a decision, write a new record
and set the `status` of the old one to `superseded by NNNN`.

OpenSpec reads these records before it writes a change, as configured in
`openspec/config.yaml`.

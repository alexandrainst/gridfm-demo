# Architecture

The architecture documentation follows [arc42](https://arc42.org/overview), with one
file per section. The project uses the sections below and leaves out the others.

| Section                                                   | Question It Answers                              |
| --------------------------------------------------------- | ------------------------------------------------ |
| [1. Introduction and Goals](01-introduction-and-goals.md) | What the demo does and which qualities matter    |
| [4. Solution Strategy](04-solution-strategy.md)           | The technologies and the split into parts        |
| [5. Building Block View](05-building-block-view.md)       | The folders, what each is for and its invariants |
| [6. Runtime View](06-runtime-view.md)                     | What happens during a run and a prediction       |
| [7. Deployment View](07-deployment-view.md)               | Which container runs what                        |
| [8. Cross-cutting Concepts](08-crosscutting-concepts.md)  | Configuration, reproducibility, outputs, tests   |
| [9. Architecture Decisions](09-architecture-decisions.md) | The decision records                             |
| [12. Glossary](12-glossary.md)                            | The project's terms                              |

Diagrams are Mermaid code blocks inside the sections. Every rule a diagram shows is also
stated in the text.

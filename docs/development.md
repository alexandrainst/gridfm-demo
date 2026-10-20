# Development

[`docs/architecture/`](architecture/README.md) describes how the project works, from its
goals and building blocks to its decision records and glossary. The how-to guides
describe how to extend it:

- [How to Add an Experiment](how-to/add-experiment.md)
- [How to Add a Federation](how-to/add-federation.md)

## Tools

The development tools are
[tree](https://oldmanprogrammer.net/source.php?dir=projects/tree),
[Prettier](https://prettier.io/) and
[markdownlint-cli2](https://github.com/DavidAnson/markdownlint-cli2). For users of
[Nix](https://nixos.org/), `flake.nix` provides uv and the development tools, but not
Docker. Start its shell with `nix develop`.

Set up the environment, then run the formatters, linters and type checkers, the tests
and the Markdown formatter:

```bash
make install
source .venv/bin/activate
make check
make test
make format-markdown
```

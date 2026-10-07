"""Client settings read from the SuperNode node config.

The node config is set with `--node-config` in `federations/*/compose.yml`. Flower
only allows scalar values in it, so lists are comma-separated strings.
"""

from pathlib import Path

from flwr.app import Context

from .interface import ClientDataset

NODE_CONFIG_KEYS: tuple[str, ...] = ("client-id", "data-dir", "networks", "scenarios")


def client_dataset(context: Context) -> ClientDataset:
    """Return the dataset of this client.

    Args:
        context:
          Context of the ClientApp. Its node config holds `"client-id"` (an integer),
          `"data-dir"`, `"networks"` (comma-separated network names) and
          `"scenarios"` (comma-separated scenario counts, one per network).

    Returns:
        The client's dataset.

    Raises:
        KeyError:
          If the node config lacks one of the keys.
        ValueError:
          If the client ID or a scenario count is not an integer, or the lists are
          invalid as
          described in `ClientDataset`.
    """
    missing = [key for key in NODE_CONFIG_KEYS if key not in context.node_config]
    if missing:
        raise KeyError(
            f"The node config has no {', '.join(map(repr, missing))}. Set it with the "
            "SuperNode's `--node-config`."
        )
    client_id = context.node_config["client-id"]
    if not isinstance(client_id, int):
        raise ValueError(
            f"The node config 'client-id' must be an integer, got {client_id!r}."
        )
    data_dir = str(context.node_config["data-dir"])
    networks = _split(value=str(context.node_config["networks"]))
    scenarios = _split(value=str(context.node_config["scenarios"]))
    try:
        scenario_counts = tuple(int(count) for count in scenarios)
    except ValueError as err:
        raise ValueError(
            f"The node config 'scenarios' must be comma-separated integers, got "
            f"{','.join(scenarios)!r}."
        ) from err
    return ClientDataset(
        client_id=client_id,
        data_dir=Path(data_dir),
        networks=tuple(networks),
        scenarios=scenario_counts,
    )


def _split(value: str) -> list[str]:
    """Split a comma-separated value into its stripped, non-empty items.

    Args:
        value:
          Comma-separated value.

    Returns:
        The items in order.
    """
    return [item.strip() for item in value.split(",") if item.strip()]

"""Client datasets of a federation, as its SuperNodes' node configs describe them."""

from dataclasses import dataclass
from pathlib import Path

import yaml
from flwr.common.config import parse_config_args

from .paths import federation_dir


@dataclass(frozen=True)
class ClientData:
    """Dataset of one client, as its SuperNode's node config describes it.

    Attributes:
        client_id:
          ID of the client.
        data_dir:
          Folder on the host with one subfolder per network.
        networks:
          Names of the networks the client uses.
        scenarios:
          Number of scenarios the client uses per network, in the order of
          `networks`.
    """

    client_id: int
    data_dir: Path
    networks: tuple[str, ...]
    scenarios: tuple[int, ...]


def read_clients(federation: str) -> list[ClientData]:
    """Return the client datasets set in a federation's `compose.yml`.

    Args:
        federation:
          Name of the federation.

    Returns:
        One `ClientData` per service with a `--node-config` argument, sorted by
        client ID.

    Raises:
        ValueError:
          If a node config's `data-dir` is not mounted into any service.
    """
    directory = federation_dir(federation=federation)
    compose = yaml.safe_load((directory / "compose.yml").read_text())
    services = compose["services"].values()
    # The node config gives the data folder inside the ClientApp container, which
    # mounts it from the host.
    mounts = {
        container: (directory / host).resolve()
        for service in services
        for host, container, *_ in (
            volume.split(":") for volume in service.get("volumes", [])
        )
    }
    clients = []
    for service in services:
        command = service.get("command", [])
        if "--node-config" not in command:
            continue
        node_config = parse_config_args(
            config=[command[command.index("--node-config") + 1]]
        )
        data_dir = str(node_config["data-dir"])
        if data_dir not in mounts:
            raise ValueError(
                f"No service of {federation} mounts the data folder {data_dir!r}."
            )
        clients.append(
            ClientData(
                client_id=int(node_config["client-id"]),
                data_dir=mounts[data_dir],
                networks=tuple(_split(value=str(node_config["networks"]))),
                scenarios=tuple(
                    int(count) for count in _split(value=str(node_config["scenarios"]))
                ),
            )
        )
    return sorted(clients, key=lambda client: client.client_id)


def _split(value: str) -> list[str]:
    """Split a comma-separated node config value.

    Args:
        value:
          The value, such as `"case14_ieee,case30_ieee"`.

    Returns:
        The stripped, non-empty items.
    """
    # The same format as `flower_app/node_config.py`, which `gridfm_cli` must not
    # import.
    return [item.strip() for item in value.split(",") if item.strip()]

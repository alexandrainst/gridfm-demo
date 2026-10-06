"""Tests for the `gridfm_demo.node_config` module."""

from pathlib import Path

import pytest
from flwr.app import Context, RecordDict
from flwr.common.typing import UserConfig

from gridfm_demo.interface import ClientDataset
from gridfm_demo.node_config import client_dataset


def test_client_dataset_reads_single_network() -> None:
    """A single network and an integer scenario count are parsed."""
    context = _context(
        node_config={
            "data-dir": "/data/client_0",
            "networks": "case14_ieee",
            "scenarios": 40,
        }
    )
    assert client_dataset(context=context) == ClientDataset(
        data_dir=Path("/data/client_0"), networks=("case14_ieee",), scenarios=(40,)
    )


def test_client_dataset_reads_comma_separated_lists() -> None:
    """Comma-separated networks and scenario counts are split and stripped."""
    context = _context(
        node_config={
            "data-dir": "/data/client_0",
            "networks": "case14_ieee, case30_ieee",
            "scenarios": "40,20",
        }
    )
    dataset = client_dataset(context=context)
    assert dataset.networks == ("case14_ieee", "case30_ieee")
    assert dataset.scenarios == (40, 20)


@pytest.mark.parametrize("missing_key", ["data-dir", "networks", "scenarios"])
def test_client_dataset_rejects_missing_key(missing_key: str) -> None:
    """A missing node config key raises a `KeyError` naming the key."""
    node_config: UserConfig = {
        "data-dir": "/data/client_0",
        "networks": "case14_ieee",
        "scenarios": "40",
    }
    del node_config[missing_key]
    with pytest.raises(KeyError, match=missing_key):
        client_dataset(context=_context(node_config=node_config))


def test_client_dataset_rejects_non_integer_scenarios() -> None:
    """A scenario count that is not an integer raises a `ValueError`."""
    context = _context(
        node_config={
            "data-dir": "/data",
            "networks": "case14_ieee",
            "scenarios": "many",
        }
    )
    with pytest.raises(ValueError, match="integers"):
        client_dataset(context=context)


def test_client_dataset_rejects_length_mismatch() -> None:
    """Different numbers of networks and scenario counts raise a `ValueError`."""
    context = _context(
        node_config={
            "data-dir": "/data",
            "networks": "case14_ieee,case30_ieee",
            "scenarios": "40",
        }
    )
    with pytest.raises(ValueError, match="one scenario count per network"):
        client_dataset(context=context)


def test_client_dataset_rejects_empty_networks() -> None:
    """An empty network list raises a `ValueError`."""
    context = _context(
        node_config={"data-dir": "/data", "networks": "", "scenarios": ""}
    )
    with pytest.raises(ValueError, match="at least one network"):
        client_dataset(context=context)


def _context(node_config: UserConfig) -> Context:
    """Return a ClientApp context with `node_config` and an empty run config.

    Args:
        node_config:
          Node config of the context.

    Returns:
        The context.
    """
    return Context(
        run_id=0, node_id=0, node_config=node_config, state=RecordDict(), run_config={}
    )

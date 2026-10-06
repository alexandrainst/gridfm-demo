"""Graphkit task, data, model, optimizer and training configuration of FedAvg."""

import typing as t

# A Python literal rather than YAML because Flower's app bundle only includes `*.py`,
# `*.toml` and `*.md` files.
# `data.networks` and `data.scenarios` describe the client's dataset and are set from
# its `ClientDataset`.
GRAPHKIT_CONFIG: dict[str, t.Any] = {
    "task": {"task_name": "PowerFlow"},
    "data": {
        "mask_value": 0.0,
        "normalization": "HeteroDataMVANormalizer",
        "test_ratio": 0.1,
        "val_ratio": 0.1,
        "workers": 0,
        "split_by_load_scenario_idx": True,
    },
    "model": {
        "attention_head": 4,
        "edge_dim": 10,
        "hidden_size": 32,
        "input_bus_dim": 15,
        "input_gen_dim": 6,
        "output_bus_dim": 2,
        "output_gen_dim": 1,
        "num_layers": 3,
        "type": "GNS_heterogeneous",
    },
    "optimizer": {
        "beta1": 0.9,
        "beta2": 0.999,
        "learning_rate": 0.0005,
        "lr_decay": 0.7,
        "lr_patience": 5,
    },
    "training": {
        "batch_size": 4,
        "epochs": 1,
        "loss_weights": [1.0],
        "losses": ["MaskedBusMSE"],
        "loss_args": [{}],
        "accelerator": "cpu",
        "devices": 1,
        "strategy": "auto",
    },
    "seed": 0,
    "verbose": False,
    "callbacks": {"patience": 100, "tol": 0},
}

#!/usr/bin/env python3
"""
Run a 30-day hourly pandapower time series on every PtX siting scenario.

For each scenario (P location s1..s6) the same 5-bus net is driven by the
three profiles from make_profiles.py:

  consumption -> load 'scaling' of DSO nodes A and B  (P & Q scale together)
  ptx         -> bus P power [MW]:  ptx>=0 -> +ptx*54 MW (electrolyzer load)
                                    ptx<0  -> -|ptx|*304 MW (solar injection)
  generator   -> gas plant G output:  generator * 800 MW

Results are written per scenario to data/networks/ptx/scenario_<name>/ :
  res_bus.vm_pu.csv, res_line.loading_percent.csv, ... (pandapower OutputWriter)
  inputs.csv      -- the applied MW set-points per element
A combined summary.csv is written alongside.
"""

import os
import warnings

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
import pandapower as pp
from pandapower.timeseries import DFData, OutputWriter
from pandapower.timeseries.run_time_series import run_timeseries
from pandapower.control import ConstControl

from build_ptx_cases import (
    SCENARIOS,
    COMP_FRACTION,
    COMP_SCENARIOS,
    build_net,
    A_PD,
    B_PD,
    G_PG,
    P_ELYS_MW,
    P_SOLAR_MW,
)

LOG = [
    ("res_bus", "vm_pu"),
    ("res_bus", "va_degree"),
    ("res_line", "loading_percent"),
    ("res_line", "pl_mw"),
    ("res_ext_grid", "p_mw"),
    ("res_ext_grid", "q_mvar"),
    ("res_gen", "p_mw"),
    ("res_gen", "q_mvar"),
]


def find_root():
    root = os.path.dirname(os.path.abspath(__file__))
    while root != os.path.dirname(root) and not os.path.exists(
        os.path.join(root, "pyproject.toml")
    ):
        root = os.path.dirname(root)
    return root


def run_scenario(name, p_coord, prof, outdir):
    cf = COMP_FRACTION if name in COMP_SCENARIOS else 0.0
    net, _, _, _ = build_net(p_coord, comp_fraction=cf)

    idx = lambda tbl, nm: int(net[tbl].index[net[tbl].name == nm][0])
    a, b, p = idx("load", "A"), idx("load", "B"), idx("load", "P")
    g = idx("gen", "G")

    # applied set-points (same across scenarios; saved per folder for self-containment)
    load_p = np.where(
        prof["ptx"] >= 0, prof["ptx"] * P_ELYS_MW, prof["ptx"] * P_SOLAR_MW
    )
    df = pd.DataFrame(
        {"cons": prof["consumption"], "loadP": load_p, "genG": prof["generator"] * G_PG}
    )
    ds = DFData(df)
    n = len(df)

    ConstControl(
        net,
        "load",
        "scaling",
        element_index=[a, b],
        data_source=ds,
        profile_name=["cons", "cons"],
    )
    ConstControl(
        net, "load", "p_mw", element_index=[p], data_source=ds, profile_name="loadP"
    )
    ConstControl(
        net, "gen", "p_mw", element_index=[g], data_source=ds, profile_name="genG"
    )

    os.makedirs(outdir, exist_ok=True)
    pd.DataFrame(
        {
            "hour": np.arange(n),
            "A_mw": prof["consumption"] * A_PD,
            "B_mw": prof["consumption"] * B_PD,
            "P_mw": load_p,
            "G_mw": prof["generator"] * G_PG,
        }
    ).to_csv(os.path.join(outdir, "inputs.csv"), index=False)

    ow = OutputWriter(
        net, time_steps=range(n), output_path=outdir, output_file_type=".csv"
    )
    for tbl, var in LOG:
        ow.log_variable(tbl, var)

    run_timeseries(net, time_steps=range(n), continue_on_divergence=True, verbose=False)

    vm = ow.output["res_bus.vm_pu"]
    load = ow.output["res_line.loading_percent"]
    slack = ow.output["res_ext_grid.p_mw"]
    diverged = int(vm.isna().any(axis=1).sum())
    return dict(
        scenario=name,
        steps=n,
        diverged=diverged,
        vm_min=np.nanmin(vm.values),
        vm_max=np.nanmax(vm.values),
        max_line_load=np.nanmax(load.values),
        slack_min_mw=np.nanmin(slack.values),
        slack_max_mw=np.nanmax(slack.values),
    )


def main():
    root = find_root()
    npz = np.load(os.path.join(root, "data", "profiles", "profiles_30day.npz"))
    prof = {k: npz[k] for k in ("consumption", "ptx", "generator")}
    base = os.path.join(root, "data", "networks", "ptx")

    rows = []
    for name, pc in SCENARIOS.items():
        outdir = os.path.join(base, "scenario_%s" % name)
        s = run_scenario(name, pc, prof, outdir)
        rows.append(s)
        print(
            "%s  diverged %3d/%d  Vm[%.3f,%.3f]  maxLine %4.0f%%  slack[%+.0f,%+.0f] MW"
            % (
                s["scenario"],
                s["diverged"],
                s["steps"],
                s["vm_min"],
                s["vm_max"],
                s["max_line_load"],
                s["slack_min_mw"],
                s["slack_max_mw"],
            )
        )

    summ = pd.DataFrame(rows)
    summ.to_csv(os.path.join(base, "timeseries_summary.csv"), index=False)
    print("\nwrote", os.path.join(base, "timeseries_summary.csv"))


if __name__ == "__main__":
    main()

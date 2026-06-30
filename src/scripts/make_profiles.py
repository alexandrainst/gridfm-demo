#!/usr/bin/env python3
"""
Build 30-day, 1-hour time-series profiles for the simple 5-bus PtX network.

Three normalised profiles (one value per hour, 720 steps):

  consumption  DSO load factor = seasonal winter envelope (peaks mid-month)
               x daily shape with morning (08:00) and evening (17:00) peaks.
               Applied as a multiplier to each DSO node's nominal load.

  ptx          PtX electrolyzer setpoint, in fraction of rated consumption:
               ramp 0->100%, ~2.5 d at 100%, abrupt drop to 50%, one day of
               PRODUCTION (electrolyzer off, solar exports -> negative), ramp
               back up, then 100% for the rest.  + = consumption, - = production.

  generator    gas plant output: 100% for the first 15 days, 75% thereafter.

Saved to data/profiles/ as .npz and .csv; also plotted to .png.
"""
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# ------------------------------------------------------------------ config ---
DAYS = 30
DT_H = 1
N = DAYS * 24 // DT_H                      # 720 hourly steps
t_h = np.arange(N) * DT_H                  # hours
t_d = t_h / 24.0                           # days (float)

# --- consumption: seasonal envelope x daily shape ---------------------------
SEASON_AMP = 0.15                          # winter hump amplitude
MORN_H, EVE_H = 8.0, 17.0                  # daily peak hours
MORN_W, EVE_W = 1.8, 2.0                   # peak widths (h)
MORN_A, EVE_A = 0.40, 0.55                 # peak heights (evening higher)
DAILY_BASE = 0.45                          # overnight base

# --- PtX profile as contiguous segments: (start_day, end_day, v0, v1) -------
# value = fraction of rated electrolyzer load; + = consumption, - = production.
PROD_LEVEL = -1.0        # full production (solar export; rescale to MW later)
PTX_SEGMENTS = [
    (0.00, 0.75, 0.0, 1.0),               # ramp up
    (0.75, 3.00, 1.0, 1.0),               # 100%  (~2.25 d)
    (3.00, 4.00, 0.5, 0.5),               # 50%   (1 d)
    (4.00, 5.00, PROD_LEVEL, PROD_LEVEL),  # production / off (1 d)
    (5.00, 5.75, PROD_LEVEL, 1.0),         # ramp back up
    (5.75, 14.00, 1.0, 1.0),              # 100% until day 14
    (14.00, 14.75, 1.0, 0.4),             # ramp down to 40% at day 14
    (14.75, 20.00, 0.4, 0.4),             # 40% until day 20
    (20.00, 22.00, 0.4, PROD_LEVEL),       # drop down to full production
    (22.00, 25.00, PROD_LEVEL, PROD_LEVEL),  # production days 22, 23, 24
    (25.00, 26.00, PROD_LEVEL, 1.0),       # ramp back up
    (26.00, 30.00, 1.0, 1.0),             # 100% for the rest
]

# --- generator --------------------------------------------------------------
GEN_STEP_DAY = 15
GEN_HI, GEN_LO = 1.00, 0.75


def consumption_profile():
    h = t_h % 24
    morning = MORN_A * np.exp(-((h - MORN_H) ** 2) / (2 * MORN_W ** 2))
    evening = EVE_A * np.exp(-((h - EVE_H) ** 2) / (2 * EVE_W ** 2))
    daily = DAILY_BASE + morning + evening
    daily /= daily.max()                              # peak -> 1.0
    # seasonal hump: half-cosine over the window, peaking mid-month (winter)
    seasonal = 1.0 + SEASON_AMP * np.cos(2 * np.pi * (t_d - DAYS / 2) / (2 * DAYS))
    return seasonal * daily, seasonal


def ptx_profile():
    p = np.zeros(N)
    for d0, d1, v0, v1 in PTX_SEGMENTS:
        i0 = int(round(d0 * 24 / DT_H))
        i1 = int(round(d1 * 24 / DT_H))
        p[i0:i1] = np.linspace(v0, v1, i1 - i0, endpoint=False)
    return p


def generator_profile():
    g = np.full(N, GEN_HI)
    g[GEN_STEP_DAY * 24 // DT_H:] = GEN_LO
    return g


def build():
    cons, seasonal = consumption_profile()
    return dict(t_h=t_h, t_d=t_d, consumption=cons, seasonal=seasonal,
                ptx=ptx_profile(), generator=generator_profile())


def save(prof, outdir):
    np.savez(os.path.join(outdir, "profiles_30day.npz"),
             t_h=prof["t_h"], consumption=prof["consumption"],
             ptx=prof["ptx"], generator=prof["generator"])
    rows = np.column_stack([prof["t_h"], prof["t_d"], prof["consumption"],
                            prof["ptx"], prof["generator"]])
    np.savetxt(os.path.join(outdir, "profiles_30day.csv"), rows, delimiter=",",
               header="hour,day,consumption,ptx,generator", comments="")


def plot(prof, outpng):
    td = prof["t_d"]
    fig, ax = plt.subplots(3, 1, figsize=(13, 9), sharex=True)

    ax[0].plot(td, prof["consumption"], color="#4C72B0", lw=1.0)
    ax[0].plot(td, prof["seasonal"], color="#C44E52", lw=1.6, ls="--",
               label="seasonal envelope")
    ax[0].set_ylabel("DSO load\n(× nominal)")
    ax[0].set_title("Consumption — winter seasonal envelope × daily shape "
                    "(peaks 08:00 & 17:00)")
    ax[0].legend(loc="upper right", fontsize=8)

    ax[1].axhline(0, color="0.6", lw=0.8)
    ax[1].plot(td, prof["ptx"], color="#9467BD", lw=1.4)
    ax[1].fill_between(td, prof["ptx"], 0, where=prof["ptx"] >= 0,
                       color="#9467BD", alpha=0.15, label="consumption")
    ax[1].fill_between(td, prof["ptx"], 0, where=prof["ptx"] < 0,
                       color="#2a9d3a", alpha=0.25, label="production")
    ax[1].set_ylabel("PtX setpoint\n(× rated)")
    ax[1].set_title("PtX — ramp ▸ 100% ▸ 50% ▸ prod ▸ 100% ▸ 40% ▸ prod ▸ 100%")
    ax[1].legend(loc="lower right", fontsize=8)
    for x, y, lab in [(0.4, 1.12, "ramp"), (1.9, 1.12, "100%"), (3.5, 0.6, "50%"),
                      (4.5, -0.9, "prod"), (10, 1.12, "100%"), (17.3, 0.5, "40%"),
                      (23, -0.9, "prod"), (28, 1.12, "100%")]:
        ax[1].annotate(lab, (x, y), fontsize=7, color="#5a3a85", ha="center")

    ax[2].plot(td, prof["generator"], color="#55A868", lw=1.6)
    ax[2].fill_between(td, prof["generator"], 0, color="#55A868", alpha=0.15)
    ax[2].set_ylabel("Gas plant\n(× rated)")
    ax[2].set_ylim(0, 1.1)
    ax[2].set_title("Generator — 100% for 15 days, then 75%")

    for a in ax:
        a.grid(True, ls=":", alpha=0.4)
        a.set_xlim(0, DAYS)
    ax[2].set_xlabel("time [days]")
    ax[2].set_xticks(range(0, DAYS + 1, 2))
    fig.suptitle("30-day hourly profiles — simple 5-bus PtX network",
                 fontsize=14, fontweight="bold")
    fig.tight_layout(rect=(0, 0, 1, 0.98))
    fig.savefig(outpng, dpi=120, bbox_inches="tight")
    print("wrote", outpng)


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    root = here
    while root != os.path.dirname(root) and not os.path.exists(
            os.path.join(root, "pyproject.toml")):
        root = os.path.dirname(root)
    outdir = os.path.join(root, "data", "profiles")
    os.makedirs(outdir, exist_ok=True)

    prof = build()
    save(prof, outdir)
    plot(prof, os.path.join(outdir, "profiles_30day.png"))
    print("arrays: %d steps each | consumption[min,max]=[%.2f,%.2f] "
          "ptx[min,max]=[%.2f,%.2f] gen∈{%.2f,%.2f}"
          % (N, prof["consumption"].min(), prof["consumption"].max(),
             prof["ptx"].min(), prof["ptx"].max(), GEN_LO, GEN_HI))


if __name__ == "__main__":
    main()

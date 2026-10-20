"""Jio coverage at launch by State: share of the 2016 population within 5 km of a Jio cell.

Usage:
    python scripts/jio_coverage.py TOWERS POP_TIF ADM1_GEOJSON
        TOWERS        OpenCellID cells for India (MCC 404/405), CSV; the 10 March 2017 OpenCellID dump
                      on archive.org (item opencellid_cell_towers.csv), filtered to India
        POP_TIF       WorldPop 2016 population, 1 km, UN-adjusted (ind_ppp_2016_1km_Aggregated_UNadj.tif)
        ADM1_GEOJSON  geoBoundaries India ADM1 (gbOpen, simplified)
    Writes data/external/jio/jio_cells_india.csv.gz (Jio cells only) and data/analysis/state_jio.csv.

Follows "Mobile Internet and Collective Action: Evidence from India's Jio Shock" (SSRN 6959526):
coverage = population within 5 km of any Jio cell active at launch / total population (WorldPop 2016).
Jio cells: MCC 405, MNC 840 and 854-874. "Active at launch" = first seen by OpenCellID by 30 September
2016 (Jio launched 5 September 2016). Alternatives: 7 km radius; cells seen by 31 December 2016 and by
March 2017 (the end of the dump).
OpenCellID is crowd-sourced, so it is more complete where smartphone users were already dense; the
State fixed effects absorb level differences, but coverage partly tracks existing connectivity.
"""
import os, sys

import numpy as np
import pandas as pd
import geopandas as gpd
import rasterio
from rasterio.features import rasterize
from scipy.spatial import cKDTree

R_EARTH = 6371.0
JIO_MNC = [840] + list(range(854, 875))
CUTOFFS = {"sep2016": "2016-09-30 23:59:59", "dec2016": "2016-12-31 23:59:59", "mar2017": "2017-03-31"}
NAME = {"Andaman and Nicobar Islands": "A&N Islands", "Dādra and Nagar Haveli and Damān and Diu": "D&N Haveli and Daman & Diu",
        "Ladākh": "Jammu & Kashmir", "Jammu and Kashmīr": "Jammu & Kashmir"}


def unit(name):
    import unicodedata
    n = NAME.get(name, name)
    n = unicodedata.normalize("NFKD", n).encode("ascii", "ignore").decode()
    return NAME.get(n, n)


def xyz(lon, lat):
    lon, lat = np.radians(lon), np.radians(lat)
    return np.c_[np.cos(lat) * np.cos(lon), np.cos(lat) * np.sin(lon), np.sin(lat)]


def main(towers, pop_tif, adm1):
    t = pd.read_csv(towers)
    jio = t[(t.mcc == 405) & t.net.isin(JIO_MNC)].copy()
    jio["created_at"] = pd.to_datetime(jio.created, unit="s")
    os.makedirs("data/external/jio", exist_ok=True)
    jio.drop(columns="created_at").to_csv("data/external/jio/jio_cells_india.csv.gz", index=False)

    with rasterio.open(pop_tif) as r:
        pop = r.read(1).astype("float64")
        pop[pop < 0] = 0
        tr, shape = r.transform, r.shape
    states = gpd.read_file(adm1).to_crs("EPSG:4326")
    states["unit"] = states.shapeName.map(unit)
    codes = {u: i + 1 for i, u in enumerate(sorted(states.unit.unique()))}
    lab = rasterize(((g, codes[u]) for g, u in zip(states.geometry, states.unit)), out_shape=shape, transform=tr, fill=0)

    rows, cols = np.nonzero((pop > 0) & (lab > 0))
    lon, lat = rasterio.transform.xy(tr, rows, cols)
    pts = xyz(np.asarray(lon), np.asarray(lat))
    w, s = pop[rows, cols], lab[rows, cols]
    inv = {v: k for k, v in codes.items()}
    out = pd.DataFrame({"state": [inv[i] for i in range(1, len(codes) + 1)]}).set_index("state")
    out["pop2016_mn"] = pd.Series(np.bincount(s, weights=w, minlength=len(codes) + 1)[1:] / 1e6, index=out.index)

    for cname, cut in CUTOFFS.items():
        c = jio[jio.created_at <= cut]
        tree = cKDTree(xyz(c.lon.values, c.lat.values))
        d, _ = tree.query(pts, k=1)
        km = 2 * R_EARTH * np.arcsin(np.clip(d / 2, 0, 1))
        for rad in (5, 7):
            cov = np.bincount(s, weights=w * (km <= rad), minlength=len(codes) + 1)[1:]
            out[f"jio_cov{rad}km_{cname}"] = (cov / 1e6 / out.pop2016_mn).round(4).values
    # Jio cells per State at launch (cells, not people), for reference
    g = gpd.GeoDataFrame(jio, geometry=gpd.points_from_xy(jio.lon, jio.lat), crs="EPSG:4326")
    g = gpd.sjoin(g.drop(columns="unit"), states[["unit", "geometry"]].rename(columns={"unit": "st_unit"}), predicate="within")
    for cname, cut in CUTOFFS.items():
        out[f"jio_cells_{cname}"] = g[g.created_at <= cut].groupby("st_unit").size().reindex(out.index).fillna(0).astype(int)
    out = out.round({"pop2016_mn": 3})
    out.to_csv("data/analysis/state_jio.csv")
    print(out.sort_values("jio_cov5km_sep2016").to_string())


if __name__ == "__main__":
    main(*sys.argv[1:4])

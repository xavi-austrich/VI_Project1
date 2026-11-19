"""Shared comarca boundaries, projections, areas, and Altair base layer."""

import json
from math import log, pi, radians, tan
from pathlib import Path

import altair as alt
import numpy as np
import pandas as pd


DATA_DIR = Path(__file__).resolve().parent / "dades"
EARTH_RADIUS_METRES = 6_371_007.18
STANDARD_PARALLEL = np.radians(41.5)


def mercator(longitude, latitude):
    """Project longitude and latitude in degrees to planar Mercator coordinates."""
    return [radians(longitude), log(tan(pi / 4 + radians(latitude) / 2))]


def equal_area(longitude, latitude):
    """Project longitude and latitude in degrees to equal-area metres for Q1."""
    longitude, latitude = np.radians([longitude, latitude])
    x = EARTH_RADIUS_METRES * longitude * np.cos(STANDARD_PARALLEL)
    y = EARTH_RADIUS_METRES * np.sin(latitude) / np.cos(STANDARD_PARALLEL)
    return [x, y]


def _project_coordinates(coordinates, project):
    if isinstance(coordinates[0], (int, float)):
        return project(*coordinates[:2])
    return [_project_coordinates(part, project) for part in coordinates]


def load_comarca_boundaries(project):
    """Load the boundary features and keep the source bbox in longitude/latitude."""
    with (DATA_DIR / "comarques.geojson").open(encoding="utf-8-sig") as file:
        boundaries = json.load(file)

    for feature in boundaries["features"]:
        geometry = feature["geometry"]
        geometry["coordinates"] = _project_coordinates(geometry["coordinates"], project)
    return boundaries


def comarca_areas_hectares(boundaries):
    """Return the published 2024 comarca areas in hectares, keyed by code."""
    areas = pd.read_csv(
        DATA_DIR / "superficie_comarques_idescat_2024.csv", sep=";", skiprows=6, index_col=0,
    )["Superfície km²"].rename(index={"Aran": "Val d'Aran"}) * 100

    return {
        properties["CODICOMAR"]: areas.loc[properties["NOMCOMAR"]]
        for properties in (feature["properties"] for feature in boundaries["features"])
    }


def comarca_base_map(boundaries, *, stroke_width=0.6):
    """Build a boundary layer that can be layered or concatenated."""
    return alt.Chart(alt.Data(values=boundaries["features"])).mark_geoshape(
        stroke="white", strokeWidth=stroke_width,
    )

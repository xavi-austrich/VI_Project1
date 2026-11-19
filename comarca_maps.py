"""Shared comarca boundaries, projections, areas, and Altair base layer."""

import json
from math import cos, log, pi, radians, sin, tan
from pathlib import Path

import altair as alt
import pandas as pd


DATA_DIR = Path(__file__).resolve().parent / "dades"
EARTH_RADIUS_METRES = 6_371_007.18
STANDARD_PARALLEL = radians(41.5)


def mercator(longitude, latitude):
    """Project longitude and latitude in degrees to planar Mercator coordinates."""
    return [radians(longitude), log(tan(pi / 4 + radians(latitude) / 2))]


def equal_area(longitude, latitude):
    """Project longitude and latitude in degrees to equal-area metres for Q1."""
    longitude = radians(longitude)
    latitude = radians(latitude)
    x = EARTH_RADIUS_METRES * longitude * cos(STANDARD_PARALLEL)
    y = EARTH_RADIUS_METRES * sin(latitude) / cos(STANDARD_PARALLEL)
    return [x, y]


def _project_coordinates(coordinates, project):
    # GeoJSON nests points inside rings, polygons, and multipolygons.
    if isinstance(coordinates[0], (int, float)):
        return project(*coordinates[:2])
    return [_project_coordinates(part, project) for part in coordinates]


def load_comarca_boundaries(project=mercator):
    """Load the boundary features and keep the source bbox in longitude/latitude."""
    with (DATA_DIR / "comarques.geojson").open(encoding="utf-8-sig") as file:
        boundaries = json.load(file)

    for feature in boundaries["features"]:
        geometry = feature["geometry"]
        geometry["coordinates"] = _project_coordinates(geometry["coordinates"], project)
    return boundaries


def comarca_areas_hectares(boundaries):
    """Return the published 2024 comarca areas in hectares, keyed by code."""
    table = pd.read_csv(
        DATA_DIR / "superficie_comarques_idescat_2024.csv", sep=";", skiprows=6, index_col=0,
    )
    # Match the boundary names and convert square kilometres to hectares.
    areas = table["Superfície km²"].rename(index={"Aran": "Val d'Aran"}) * 100

    hectares_by_code = {}
    for feature in boundaries["features"]:
        comarca = feature["properties"]
        hectares_by_code[comarca["CODICOMAR"]] = areas.loc[comarca["NOMCOMAR"]]
    return hectares_by_code


def comarca_base_map(boundaries, *, stroke_width=0.6):
    """Build a boundary layer that can be layered or concatenated."""
    return alt.Chart(alt.Data(values=boundaries["features"])).mark_geoshape(
        stroke="white", strokeWidth=stroke_width,
    )

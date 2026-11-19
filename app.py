"""An explanatory dashboard built from the notebooks' exported Altair charts."""

from copy import deepcopy
import json
from pathlib import Path

import streamlit as st


VIEWS_DIR = Path(__file__).resolve().parent / "final_views"


def load_view(question):
    path = VIEWS_DIR / f"{question}.json"
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        st.error(f"Could not load {path.name}. {error}")
        st.stop()


def extract_chart(export, chart):
    """Carry shared datasets into an independently rendered child chart."""
    spec = deepcopy(chart)
    for key in ("$schema", "datasets", "config"):
        if key in export:
            spec[key] = deepcopy(export[key])
    spec["background"] = "white"
    config = spec.setdefault("config", {})
    config.update(
        title={"fontSize": 15, "subtitleFontSize": 12, "anchor": "start"},
        axis={"titleFontSize": 13, "labelFontSize": 12},
        legend={"titleFontSize": 12, "labelFontSize": 12},
        view={"stroke": None},
    )
    return spec


def show_chart(spec, title, height, caption=None):
    spec.update(width="container", height=height, title=title)
    st.vega_lite_chart(spec=spec, theme=None, width="stretch")
    if caption:
        st.caption(caption)


def main():
    st.set_page_config(page_title="Wildfires in Catalonia", layout="wide")
    st.title("Wildfires in Catalonia")
    st.caption("1998–2024 · GovEsp + GenCat · Hover over a mark for details. Coverage in 2023–2024 is GenCat only.")

    q1, q2, q3, q4 = [load_view(f"q{i}") for i in range(1, 5)]
    municipality = extract_chart(q1, q1["hconcat"][0])
    municipality["layer"][0]["mark"]["tooltip"] = None
    density = extract_chart(q1, q1["hconcat"][1])
    change = extract_chart(q3, q3["vconcat"][0])

    size = municipality["layer"][1]["encoding"]["size"]
    size["scale"]["range"] = [0, 180]
    size["title"] = "Fires per municipality"
    size["legend"].update(orient="bottom", direction="horizontal")
    municipality["layer"][1]["mark"].update(opacity=0.55, stroke="white", strokeWidth=0.25)
    density["layer"][0]["encoding"]["color"]["legend"].update(orient="bottom", gradientLength=180)
    density["layer"][1]["encoding"]["stroke"]["legend"].update(
        orient="bottom", title="Largest fires", labelLimit=260,
    )
    change["encoding"]["color"]["legend"].update(
        orient="bottom", gradientLength=180, title="Change in fires/year per 10,000 ha",
    )

    left, middle, right = st.columns(3, gap="large")
    with left:
        show_chart(municipality, "Q1 · Where fires occur", 300,
                   "Circle area shows fire count. Terrassa has the most among mapped municipalities (245).")
    with middle:
        show_chart(density, "Q1 · Density and largest fires", 300,
                   "Outlined circles show equivalent burned area for the 10 largest located fires. Circle area is proportional to hectares.")
    with right:
        show_chart(change, "Q3 · Change in annual fire density", 300,
                   "2016–2024 minus 1998–2006. Density decreased in 34 of 43 comarques.")

    causes = extract_chart(q2, q2)
    # Reserve space inside the chart for endpoint labels, beyond the 2021 axis.
    for layer in causes["layer"][:2]:
        layer["encoding"]["x"]["scale"]["range"] = [0, {"expr": "max(100, width - 195)"}]
    causes["layer"][-1]["mark"]["fontSize"] = 12
    province = extract_chart(q3, q3["vconcat"][1])
    province["encoding"]["color"]["legend"] = {"orient": "bottom", "columns": 4}
    left, right = st.columns([3, 2], gap="large")
    with left:
        show_chart(causes, "Q2 · How causes changed", 290,
                   "Centered three-year averages of annual shares, 1999–2021. Thin connectors lead to labels beyond the 2021 axis.")
    with right:
        show_chart(province, "Q3 · Annual fires by province", 290,
                   "Annual recorded counts, 1998–2024.")

    periods = extract_chart(q4, q4["vconcat"][0])
    periods["title"] = "Q4 · Changing geographical distribution"
    periods["spacing"] = 8
    for chart in periods["hconcat"]:
        chart.update(width=175, height=190)
        chart["encoding"]["color"]["legend"].update(gradientLength=200)
    heatmap = extract_chart(q4, q4["vconcat"][1])
    # Put time horizontally to align with the trend charts above.
    heatmap["encoding"]["x"] = {
        "field": "year", "type": "ordinal", "title": "Year",
        "axis": {"labelAngle": 0, "values": [1998, 2004, 2010, 2016, 2024]},
    }
    heatmap["encoding"]["y"] = {
        "field": "month", "type": "ordinal", "title": None,
        "sort": "ascending",
        "scale": {"domain": list(range(1, 13)), "paddingInner": 0.06},
        "axis": {
            "labelExpr": "['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'][datum.value - 1]",
            "labelAngle": 0, "labelPadding": 8, "labelOverlap": False,
            "ticks": False, "domain": False,
        },
    }
    heatmap["encoding"]["color"]["legend"].update(orient="bottom", title="Share of annual fires")
    left, right = st.columns([3, 2], gap="large")
    with left:
        st.vega_lite_chart(spec=periods, theme=None, width="content")
        st.caption("Shared scale across three nine-year periods. Each comarca’s share of all period fires is divided by its area.")
    with right:
        show_chart(heatmap, "Q4 · Changing seasonality", {"step": 25},
                   "Each year totals 100%. July had the most recorded fires across the full period.")

    st.caption("Authors · Xavi Diaz and Jordi Ferre Garcia")


if __name__ == "__main__":
    main()

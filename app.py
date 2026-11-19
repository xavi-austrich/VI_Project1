"""Display the project's four exported Altair views in Streamlit."""

import json
from pathlib import Path

import streamlit as st


VIEWS_DIR = Path(__file__).resolve().parent / "final_views"
VIEWS = (
    ("Q1 · Fire locations and size", "q1.json"),
    ("Q2 · Fire causes over time", "q2.json"),
    ("Q3 · Changes in fire frequency", "q3.json"),
    ("Q4 · Fire density and seasonality", "q4.json"),
)


def main():
    st.set_page_config(page_title="Wildfires in Catalonia", layout="wide")
    st.title("Wildfires in Catalonia")

    for heading, filename in VIEWS:
        st.header(heading)
        path = VIEWS_DIR / filename
        try:
            spec = json.loads(path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            st.warning(f"Missing export `final_views/{filename}`.")
            continue
        except (OSError, UnicodeError, json.JSONDecodeError) as error:
            st.error(f"Could not read `final_views/{filename}`. {error}")
            continue

        st.vega_lite_chart(spec=spec, theme=None, width="content")


if __name__ == "__main__":
    main()

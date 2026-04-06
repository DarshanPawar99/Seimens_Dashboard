"""
layout.py

Dash application layout definition.

Imports initial state from state.py (computed once at startup)
and assembles the full page layout using component builders.
"""

from __future__ import annotations

from dash import dcc, html

from aggregations import (
    build_alt_city_cards,
    build_alt_donut_data,
    build_alt_pivot_groups,
    build_alt_type_summary,
    build_alternative_client_summary,
    build_alternative_vendor_summary,
    build_city_donut_data,
    build_city_vendor_summary,
    build_client_pivot_groups,
    build_client_worst_risk_summary,
    build_overall_client_summary,
    build_overall_vendor_summary,
    build_region_cards,
    build_vendor_risk_summary,
)
from components import (
    build_alt_city_card_grid,
    build_alt_pivot_table,
    build_alt_type_cards,
    build_city_pivot_table,
    build_dashboard_header,
    build_executive_cards,
    build_executive_donut,
    build_kpi_section,
    build_region_card_grid,
    build_section_tabs,
)
from config import (
    APP_SUBTITLE,
    APP_TITLE,
    DEFAULT_SELECTED_DATE,
    DEFAULT_SELECTED_RISK,
    SECTION_TAB_LABEL,
)
from state import get_city_options, initial_rows

# ---------------------------------------------------------------------------
# Derive initial UI state from pre-computed rows
# ---------------------------------------------------------------------------
_initial_cities = get_city_options(initial_rows)
_initial_city = _initial_cities[0] if _initial_cities else ""

_initial_overall_vendor = build_overall_vendor_summary(initial_rows)
_initial_overall_client = build_overall_client_summary(initial_rows)
_initial_lpg_vendor = build_vendor_risk_summary(initial_rows)
_initial_lpg_client = build_client_worst_risk_summary(initial_rows)
_initial_alt_vendor = build_alternative_vendor_summary(initial_rows)
_initial_alt_client = build_alternative_client_summary(initial_rows)
_initial_region_cards = build_region_cards(initial_rows)
_initial_city_summary = build_city_vendor_summary(initial_rows, _initial_city)
_initial_city_donut = build_city_donut_data(initial_rows, _initial_city)
_initial_alt_city_cards = build_alt_city_cards(initial_rows)
_initial_alt_type_summary = build_alt_type_summary(initial_rows, _initial_city)
_initial_alt_donut = build_alt_donut_data(initial_rows, _initial_city)
_initial_lpg_pivot_groups = build_client_pivot_groups(initial_rows, _initial_city, "", "")
_initial_alt_pivot_groups = build_alt_pivot_groups(initial_rows, _initial_city, "", "")


# ---------------------------------------------------------------------------
# Layout builder
# ---------------------------------------------------------------------------
def build_layout() -> html.Div:
    return html.Div(
        className="page-shell",
        children=[
            # ---- stores: LPG view ----
            dcc.Store(id="store-enriched-rows", data=initial_rows),
            dcc.Store(id="store-selected-city", data=_initial_city),
            dcc.Store(id="store-selected-risk", data=DEFAULT_SELECTED_RISK),
            dcc.Store(id="store-search-text", data=""),
            dcc.Store(id="store-city-options", data=_initial_cities),
            # ---- stores: alt view ----
            dcc.Store(id="store-alt-view-open", data=False),
            dcc.Store(id="store-alt-selected-type", data=""),
            dcc.Store(id="store-alt-search", data=""),
            # ---- stores: combined view ----
            dcc.Store(id="store-combined-view", data=False),
            dcc.Store(id="store-combined-search", data=""),

            build_dashboard_header(
                title=APP_TITLE,
                subtitle=APP_SUBTITLE,
                selected_date=DEFAULT_SELECTED_DATE,
            ),

            html.Div(
                className="dashboard-body",
                children=[
                    html.Div(
                        id="kpi-section",
                        children=build_kpi_section(
                            overall_vendor=_initial_overall_vendor,
                            overall_client=_initial_overall_client,
                            lpg_vendor=_initial_lpg_vendor,
                            lpg_client=_initial_lpg_client,
                            alt_vendor=_initial_alt_vendor,
                            alt_client=_initial_alt_client,
                            alt_view_open=False,
                        ),
                    ),

                    # LPG region cards (hidden when alt view is open)
                    html.Div(
                        id="region-card-grid",
                        className="region-card-grid-wrapper",
                        children=build_region_card_grid(
                            region_cards=_initial_region_cards,
                            selected_city=_initial_city,
                        ),
                    ),

                    # Alt city cards (shown only when alt view is open)
                    html.Div(
                        id="alt-city-grid",
                        className="region-card-grid-wrapper",
                        style={"display": "none"},
                        children=build_alt_city_card_grid(
                            alt_city_cards=_initial_alt_city_cards,
                            selected_city=_initial_city,
                        ),
                    ),

                    build_section_tabs(active_label=SECTION_TAB_LABEL),

                    # LPG executive view
                    html.Div(
                        id="lpg-executive-view",
                        className="executive-view-section",
                        children=[
                            html.Div(
                                className="executive-view-header",
                                children=[
                                    html.H2("Executive View", className="section-title"),
                                    html.P(
                                        id="selected-city-label",
                                        className="section-subtitle",
                                        children=f"{_initial_city} · Vendor Risk Breakdown" if _initial_city else "Vendor Risk Breakdown",
                                    ),
                                ],
                            ),
                            html.Div(
                                className="executive-view-card",
                                children=[
                                    html.Div(
                                        id="executive-donut-container",
                                        className="executive-donut-container",
                                        children=build_executive_donut(
                                            donut_data=_initial_city_donut,
                                            total_vendors=_initial_city_summary["total_vendors"],
                                        ),
                                    ),
                                    html.Div(
                                        id="executive-cards-container",
                                        className="executive-cards-container",
                                        children=build_executive_cards(
                                            city_summary=_initial_city_summary,
                                            selected_risk=DEFAULT_SELECTED_RISK,
                                        ),
                                    ),
                                ],
                            ),
                        ],
                    ),

                    # Alternative coverage view
                    html.Div(
                        id="alt-executive-view",
                        className="executive-view-section",
                        style={"display": "none"},
                        children=[
                            html.Div(
                                className="executive-view-header",
                                children=[
                                    html.H2("Alternative Coverage", className="section-title"),
                                    html.P(
                                        id="alt-city-label",
                                        className="section-subtitle",
                                        children=f"{_initial_city} · Backup Availability Breakdown" if _initial_city else "Backup Availability Breakdown",
                                    ),
                                ],
                            ),
                            html.Div(
                                className="executive-view-card",
                                children=[
                                    html.Div(
                                        id="alt-donut-container",
                                        className="executive-donut-container",
                                        children=build_executive_donut(
                                            donut_data=_initial_alt_donut,
                                            total_vendors=_initial_alt_type_summary["total_vendors"],
                                        ),
                                    ),
                                    html.Div(
                                        id="alt-type-cards-container",
                                        className="executive-cards-container",
                                        children=build_alt_type_cards(
                                            type_summary=_initial_alt_type_summary,
                                            selected_type="",
                                        ),
                                    ),
                                ],
                            ),
                        ],
                    ),

                    # LPG pivot
                    html.Div(
                        id="pivot-section-wrapper",
                        className="pivot-section-wrapper",
                        children=build_city_pivot_table(
                            selected_city=_initial_city,
                            selected_risk=DEFAULT_SELECTED_RISK,
                            pivot_groups=_initial_lpg_pivot_groups,
                            search_text="",
                            combined_on=False,
                            toggle_btn_id={"type": "combined-toggle", "index": "lpg"},
                        ),
                    ),

                    # Alt pivot
                    html.Div(
                        id="alt-pivot-wrapper",
                        className="pivot-section-wrapper",
                        style={"display": "none"},
                        children=build_alt_pivot_table(
                            selected_city=_initial_city,
                            selected_type="",
                            pivot_groups=_initial_alt_pivot_groups,
                            search_text="",
                            combined_on=False,
                            toggle_btn_id={"type": "combined-toggle", "index": "alt"},
                        ),
                    ),
                ],
            ),
        ],
    )

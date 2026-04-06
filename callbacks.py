"""
callbacks.py

All Dash callback functions for the LPG Stock Tracker Dashboard.

Imported by app.py after the Dash app instance is created so that
the @callback decorators are registered against the running app.

Dependency chain (no circular imports):
  config ← stock_logic ← aggregations ←┐
  config ← logger ← data_loader        ├─ callbacks ← app
  config ← components ←────────────────┘
  state (RAW_DF, initial_rows) ← callbacks
"""

from __future__ import annotations

from datetime import date
from typing import Any

import dash
from dash import Input, Output, State, callback
from dash.exceptions import PreventUpdate

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
    build_combined_pivot_groups,
    build_overall_client_summary,
    build_overall_vendor_summary,
    build_region_cards,
    build_vendor_risk_summary,
    enrich_dashboard_rows,
)
from components import (
    build_alt_city_card_grid,
    build_alt_pivot_table,
    build_alt_type_cards,
    build_city_pivot_table,
    build_combined_pivot_table,
    build_executive_cards,
    build_executive_donut,
    build_kpi_section,
    build_region_card_grid,
)
from config import DEFAULT_SELECTED_DATE, DEFAULT_SELECTED_RISK
from logger import setup_logger
from state import RAW_DF, get_city_options

logger = setup_logger(__name__)


# ---------------------------------------------------------------------------
# Shared helper — eliminates duplicate KPI computation across two callbacks
# ---------------------------------------------------------------------------
def _collect_kpi_summaries(enriched_rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Compute all six KPI summary dicts in one place."""
    return {
        "overall_vendor": build_overall_vendor_summary(enriched_rows),
        "overall_client": build_overall_client_summary(enriched_rows),
        "lpg_vendor":     build_vendor_risk_summary(enriched_rows),
        "lpg_client":     build_client_worst_risk_summary(enriched_rows),
        "alt_vendor":     build_alternative_vendor_summary(enriched_rows),
        "alt_client":     build_alternative_client_summary(enriched_rows),
    }


# ==========================================================================
# DATE CALLBACK
# ==========================================================================

@callback(
    Output("store-enriched-rows", "data"),
    Output("store-city-options", "data"),
    Output("store-selected-city", "data"),
    Output("store-selected-risk", "data"),
    Input("selected-date-input", "value"),
    State("store-selected-city", "data"),
)
def refresh_dashboard_for_date(
    selected_date_str: str | None,
    current_city: str | None,
) -> tuple[list[dict[str, Any]], list[str], str, str]:
    logger.info("Refreshing dashboard for selected date: %s", selected_date_str)
    selected_date = date.fromisoformat(selected_date_str) if selected_date_str else DEFAULT_SELECTED_DATE
    enriched_rows = enrich_dashboard_rows(RAW_DF, selected_date)
    city_options = get_city_options(enriched_rows)

    city_value = (
        current_city
        if current_city and current_city in city_options
        else (city_options[0] if city_options else "")
    )

    return enriched_rows, city_options, city_value, ""


# ==========================================================================
# LPG VIEW CALLBACKS
# ==========================================================================

@callback(
    Output("kpi-section", "children"),
    Output("region-card-grid", "children"),
    Output("selected-city-label", "children"),
    Output("executive-donut-container", "children"),
    Output("executive-cards-container", "children"),
    Input("store-enriched-rows", "data"),
    Input("store-selected-city", "data"),
    Input("store-selected-risk", "data"),
    State("store-alt-view-open", "data"),
)
def refresh_top_sections(
    enriched_rows: list[dict[str, Any]],
    selected_city: str,
    selected_risk: str,
    alt_view_open: bool,
):
    kpi = _collect_kpi_summaries(enriched_rows)
    region_cards = build_region_cards(enriched_rows)
    city_summary = build_city_vendor_summary(enriched_rows, selected_city)
    city_donut = build_city_donut_data(enriched_rows, selected_city)
    city_label = f"{selected_city} · Vendor Risk Breakdown" if selected_city else "Vendor Risk Breakdown"

    return (
        build_kpi_section(**kpi, alt_view_open=bool(alt_view_open)),
        build_region_card_grid(region_cards=region_cards, selected_city=selected_city),
        city_label,
        build_executive_donut(donut_data=city_donut, total_vendors=city_summary["total_vendors"]),
        build_executive_cards(city_summary=city_summary, selected_risk=selected_risk),
    )


@callback(
    Output("store-selected-city", "data", allow_duplicate=True),
    Output("store-selected-risk", "data", allow_duplicate=True),
    Input({"type": "region-card", "index": dash.ALL}, "n_clicks"),
    State({"type": "region-card", "index": dash.ALL}, "id"),
    prevent_initial_call=True,
)
def select_city_from_region_card(
    clicks: list[int | None],
    _ids: list[dict[str, str]],
) -> tuple[str, str]:
    if not clicks or all((v or 0) <= 0 for v in clicks):
        raise PreventUpdate
    ctx = dash.callback_context
    if not ctx.triggered:
        raise PreventUpdate
    trigger = ctx.triggered_id
    if not trigger or "index" not in trigger:
        raise PreventUpdate
    return str(trigger["index"]), ""


@callback(
    Output("store-selected-risk", "data", allow_duplicate=True),
    Input({"type": "risk-card", "index": dash.ALL}, "n_clicks"),
    State("store-selected-risk", "data"),
    prevent_initial_call=True,
)
def select_risk_category(
    _clicks: list[int | None],
    current_risk: str,
) -> str:
    ctx = dash.callback_context
    if not ctx.triggered:
        raise PreventUpdate
    trigger = ctx.triggered_id
    if not trigger or "index" not in trigger:
        raise PreventUpdate
    clicked_risk = str(trigger["index"])
    next_risk = "" if current_risk == clicked_risk else clicked_risk
    logger.info("Risk selection: %s -> %s", current_risk, next_risk)
    return next_risk


@callback(
    Output("store-search-text", "data"),
    Input({"type": "pivot-search-input", "index": dash.ALL}, "value"),
    prevent_initial_call=True,
)
def sync_search_text(search_values: list[str | None]) -> str:
    return str(search_values[-1] or "").strip() if search_values else ""


@callback(
    Output("pivot-section-wrapper", "children"),
    Input("store-enriched-rows", "data"),
    Input("store-selected-city", "data"),
    Input("store-selected-risk", "data"),
    Input("store-search-text", "data"),
    Input("store-combined-view", "data"),
    Input("store-combined-search", "data"),
)
def refresh_pivot_section(
    enriched_rows: list[dict[str, Any]],
    selected_city: str,
    selected_risk: str,
    search_text: str,
    combined_view: bool,
    combined_search: str,
):
    toggle_btn_id = {"type": "combined-toggle", "index": "lpg"}

    if combined_view:
        pivot_groups = build_combined_pivot_groups(
            enriched_rows=enriched_rows,
            selected_city=selected_city,
            search_text=combined_search,
        )
        return build_combined_pivot_table(
            selected_city=selected_city,
            pivot_groups=pivot_groups,
            search_text=combined_search,
            combined_on=True,
            toggle_btn_id=toggle_btn_id,
        )

    pivot_groups = build_client_pivot_groups(
        enriched_rows=enriched_rows,
        selected_city=selected_city,
        selected_risk=selected_risk,
        search_text=search_text,
    )
    return build_city_pivot_table(
        selected_city=selected_city,
        selected_risk=selected_risk,
        pivot_groups=pivot_groups,
        search_text=search_text,
        combined_on=False,
        toggle_btn_id=toggle_btn_id,
    )


# ==========================================================================
# ALT VIEW CALLBACKS
# ==========================================================================

@callback(
    Output("store-alt-view-open", "data", allow_duplicate=True),
    Output("store-alt-selected-type", "data", allow_duplicate=True),
    Input("lpg-vendor-kpi-card", "n_clicks"),
    State("store-alt-view-open", "data"),
    prevent_initial_call=True,
)
def toggle_lpg_view(n_clicks: int | None, is_open: bool) -> tuple[bool, str]:
    if not n_clicks or n_clicks <= 0:
        raise PreventUpdate
    if not is_open:
        raise PreventUpdate
    return False, ""


@callback(
    Output("store-alt-view-open", "data"),
    Output("store-alt-selected-type", "data"),
    Input("alt-vendor-kpi-card", "n_clicks"),
    State("store-alt-view-open", "data"),
    prevent_initial_call=True,
)
def toggle_alt_view(n_clicks: int | None, is_open: bool) -> tuple[bool, str]:
    if not n_clicks or n_clicks <= 0:
        raise PreventUpdate
    new_open = not bool(is_open)
    logger.info("Alt view toggled: %s", new_open)
    return new_open, ""


@callback(
    Output("region-card-grid", "style"),
    Output("alt-city-grid", "style"),
    Output("lpg-executive-view", "style"),
    Output("alt-executive-view", "style"),
    Output("pivot-section-wrapper", "style"),
    Output("alt-pivot-wrapper", "style"),
    Input("store-alt-view-open", "data"),
)
def toggle_view_visibility(is_open: bool):
    show = {"display": "block"}
    hide = {"display": "none"}
    if is_open:
        return hide, show, hide, show, hide, show
    return show, hide, show, hide, show, hide


@callback(
    Output("kpi-section", "children", allow_duplicate=True),
    Input("store-alt-view-open", "data"),
    State("store-enriched-rows", "data"),
    prevent_initial_call=True,
)
def refresh_kpi_for_alt_toggle(
    alt_view_open: bool,
    enriched_rows: list[dict[str, Any]],
):
    # Uses the shared helper — no duplication with refresh_top_sections
    kpi = _collect_kpi_summaries(enriched_rows)
    return build_kpi_section(**kpi, alt_view_open=bool(alt_view_open))


@callback(
    Output("store-selected-city", "data", allow_duplicate=True),
    Output("store-alt-selected-type", "data", allow_duplicate=True),
    Input({"type": "alt-city-card", "index": dash.ALL}, "n_clicks"),
    prevent_initial_call=True,
)
def select_alt_city(clicks: list[int | None]) -> tuple[str, str]:
    if not clicks or all((v or 0) <= 0 for v in clicks):
        raise PreventUpdate
    ctx = dash.callback_context
    if not ctx.triggered:
        raise PreventUpdate
    trigger = ctx.triggered_id
    if not trigger or "index" not in trigger:
        raise PreventUpdate
    return str(trigger["index"]), ""


@callback(
    Output("store-alt-selected-type", "data", allow_duplicate=True),
    Input({"type": "alt-type-card", "index": dash.ALL}, "n_clicks"),
    State("store-alt-selected-type", "data"),
    prevent_initial_call=True,
)
def select_alt_type(_clicks: list[int | None], current_type: str) -> str:
    ctx = dash.callback_context
    if not ctx.triggered:
        raise PreventUpdate
    trigger = ctx.triggered_id
    if not trigger or "index" not in trigger:
        raise PreventUpdate
    clicked = str(trigger["index"])
    return "" if current_type == clicked else clicked


@callback(
    Output("alt-city-grid", "children"),
    Input("store-enriched-rows", "data"),
    Input("store-selected-city", "data"),
)
def refresh_alt_city_grid(
    enriched_rows: list[dict[str, Any]],
    selected_city: str,
):
    alt_city_cards = build_alt_city_cards(enriched_rows)
    return build_alt_city_card_grid(alt_city_cards=alt_city_cards, selected_city=selected_city)


@callback(
    Output("alt-city-label", "children"),
    Output("alt-donut-container", "children"),
    Output("alt-type-cards-container", "children"),
    Input("store-enriched-rows", "data"),
    Input("store-selected-city", "data"),
    Input("store-alt-selected-type", "data"),
)
def refresh_alt_executive_view(
    enriched_rows: list[dict[str, Any]],
    selected_city: str,
    selected_type: str,
):
    if not selected_city:
        return "Backup Availability Breakdown", [], []

    type_summary = build_alt_type_summary(enriched_rows, selected_city)
    donut_data = build_alt_donut_data(enriched_rows, selected_city)

    label = f"{selected_city} · Backup Availability Breakdown"
    donut = build_executive_donut(donut_data=donut_data, total_vendors=type_summary["total_vendors"])
    type_cards = build_alt_type_cards(type_summary=type_summary, selected_type=selected_type)

    return label, donut, type_cards


@callback(
    Output("store-alt-search", "data"),
    Input({"type": "alt-search-input", "index": dash.ALL}, "value"),
    prevent_initial_call=True,
)
def sync_alt_search(values: list[str | None]) -> str:
    return str(values[-1] or "").strip() if values else ""


@callback(
    Output("alt-pivot-wrapper", "children"),
    Input("store-enriched-rows", "data"),
    Input("store-selected-city", "data"),
    Input("store-alt-selected-type", "data"),
    Input("store-alt-search", "data"),
    Input("store-combined-view", "data"),
    Input("store-combined-search", "data"),
)
def refresh_alt_pivot(
    enriched_rows: list[dict[str, Any]],
    selected_city: str,
    selected_type: str,
    search_text: str,
    combined_view: bool,
    combined_search: str,
):
    toggle_btn_id = {"type": "combined-toggle", "index": "alt"}

    if combined_view:
        pivot_groups = build_combined_pivot_groups(
            enriched_rows=enriched_rows,
            selected_city=selected_city,
            search_text=combined_search,
        )
        return build_combined_pivot_table(
            selected_city=selected_city,
            pivot_groups=pivot_groups,
            search_text=combined_search,
            combined_on=True,
            toggle_btn_id=toggle_btn_id,
        )

    pivot_groups = build_alt_pivot_groups(
        enriched_rows=enriched_rows,
        selected_city=selected_city,
        selected_type=selected_type,
        search_text=search_text,
    )
    return build_alt_pivot_table(
        selected_city=selected_city,
        selected_type=selected_type,
        pivot_groups=pivot_groups,
        search_text=search_text,
        combined_on=False,
        toggle_btn_id=toggle_btn_id,
    )


# ==========================================================================
# COMBINED VIEW CALLBACKS
# ==========================================================================

@callback(
    Output("store-combined-view", "data"),
    Output("store-combined-search", "data"),
    Input({"type": "combined-toggle", "index": dash.ALL}, "n_clicks"),
    State("store-combined-view", "data"),
    prevent_initial_call=True,
)
def toggle_combined_view(clicks: list[int | None], is_on: bool) -> tuple[bool, str]:
    if not clicks or all((v or 0) <= 0 for v in clicks):
        raise PreventUpdate
    ctx = dash.callback_context
    if not ctx.triggered:
        raise PreventUpdate
    return not bool(is_on), ""


@callback(
    Output("store-combined-search", "data", allow_duplicate=True),
    Input({"type": "combined-search-input", "index": dash.ALL}, "value"),
    prevent_initial_call=True,
)
def sync_combined_search(values: list[str | None]) -> str:
    return str(values[-1] or "").strip() if values else ""

import math
import altair as alt
import pandas as pd

from aequitas.plot.commons.helpers import no_axis
from aequitas.plot.commons.legend import draw_legend
from aequitas.plot.commons.scales import (
    get_chart_size_range,
    get_color_scale,
    get_bubble_size_scale,
    get_shape_scale,
)
from aequitas.plot.commons.tooltips import get_tooltip_text_group_size
from aequitas.plot.commons.style.classes import (
    Threshold_Band,
    Threshold_Rule,
    Axis,
    Rule,
    Bubble,
)
from aequitas.plot.commons.style.text import FONT
import aequitas.plot.commons.style.sizes as Sizes
import aequitas.plot.commons.initializers as Initializer

# Default chart sizing options
CHART_PADDING = 0.05


def __get_position_scales(chart_height, chart_width, chart_padding):
    """Computes the scales for x and y encodings to be used in the xy metrics chart."""

    position_scales = dict()

    # X-Y RANGES (based on chart dimensions)
    x_range = get_chart_size_range(chart_width, chart_padding)  #
    y_range = get_chart_size_range(chart_height, chart_padding)  #
    y_range.reverse()

    # METRICS SCALES
    metric_domain = [0, 1]
    position_scales["x"] = alt.Scale(domain=metric_domain, range=x_range)
    position_scales["y"] = alt.Scale(domain=metric_domain, range=y_range)

    return position_scales


def __draw_threshold_bands(
    ref_group_value,
    fairness_threshold,
    main_scale,
    aux_scale,
    accessibility_mode=False,
    drawing_x=False,
):
    """Draws threshold rules and bands for both axis: regions painted red on the chart 
    where the metric is above the defined fairness threshold."""

    # DATASOURCE
    threshold_df = pd.DataFrame(
        {
            "start": 0,
            "end": 1,
            "lower_threshold": ref_group_value / fairness_threshold,
            "upper_threshold": min(ref_group_value * fairness_threshold, 1),
        },
        index=[0],
    )

    stroke_color = (
        Threshold_Rule.stroke_accessible
        if accessibility_mode
        else Threshold_Rule.stroke
    )
    fill_color = (
        Threshold_Band.color_accessible if accessibility_mode else Threshold_Band.color
    )

    # BASES
    rule_base = alt.Chart(threshold_df).mark_rule(
        stroke=stroke_color,
        strokeWidth=Threshold_Rule.stroke_width,
        opacity=Threshold_Rule.opacity,
        tooltip="",
    )

    band_base = alt.Chart(threshold_df).mark_rect(
        fill=fill_color, opacity=Threshold_Band.opacity, tooltip=""
    )

    # PARAMS
    if drawing_x:
        common_params = dict(
            y=alt.Y("start:Q", scale=aux_scale, axis=no_axis()), y2="end:Q"
        )
        upper_param = dict(
            x=alt.X("upper_threshold:Q", scale=main_scale, axis=no_axis())
        )
        lower_param = dict(
            x=alt.X("lower_threshold:Q", scale=main_scale, axis=no_axis())
        )
        lower_end_param = dict(x2="start:Q")
        upper_end_param = dict(x2="end:Q")
    else:
        common_params = dict(
            x=alt.X("start:Q", scale=aux_scale, axis=no_axis()), x2="end:Q"
        )
        upper_param = dict(
            y=alt.Y("upper_threshold:Q", scale=main_scale, axis=no_axis())
        )
        lower_param = dict(
            y=alt.Y("lower_threshold:Q", scale=main_scale, axis=no_axis())
        )
        lower_end_param = dict(y2="start:Q")
        upper_end_param = dict(y2="end:Q")

    # RULES
    lower_threshold_rule = rule_base.encode(**common_params, **lower_param,)
    upper_threshold_rule = rule_base.encode(**common_params, **upper_param,)

    # BANDS
    lower_threshold_band = band_base.encode(
        **common_params, **lower_param, **lower_end_param
    )
    upper_threshold_band = band_base.encode(
        **common_params, **upper_param, **upper_end_param
    )

    return (
        lower_threshold_rule
        + upper_threshold_rule
        + lower_threshold_band
        + upper_threshold_band
    )


def __draw_tick_labels(scales, chart_height, chart_width, chart_padding):
    """Draws the numbers in both axes."""

    axis_values = [0, 0.25, 0.5, 0.75, 1]

    axis_df = pd.DataFrame({"main_axis_values": axis_values, "aux_axis_position": 0})

    x_tick_labels = (
        alt.Chart(axis_df)
        .mark_text(
            yOffset=Axis.label_font_size * 1.5,
            tooltip="",
            align="center",
            fontSize=Axis.label_font_size,
            fontWeight=Axis.label_font_weight,
            font=FONT,
        )
        .encode(
            text=alt.Text("main_axis_values:Q"),
            x=alt.X("main_axis_values:Q", scale=scales["x"], axis=no_axis()),
            y=alt.Y("aux_axis_position:Q", scale=scales["y"], axis=no_axis()),
        )
    )

    axis_df.drop(0, inplace=True)

    y_tick_labels = (
        alt.Chart(axis_df)
        .mark_text(
            # yOffset=2,
            baseline="middle",
            xOffset=-Axis.label_font_size * 1.5,
            tooltip="",
            align="center",
            fontSize=Axis.label_font_size,
            fontWeight=Axis.label_font_weight,
            font=FONT,
        )
        .encode(
            text=alt.Text("main_axis_values:Q"),
            x=alt.X("aux_axis_position:Q", scale=scales["x"], axis=no_axis()),
            y=alt.Y("main_axis_values:Q", scale=scales["y"], axis=no_axis()),
        )
    )

    return x_tick_labels + y_tick_labels


def __draw_axis_rules(x_metric, y_metric, scales):
    """Draws horizontal and vertical rules for the axis."""

    # BASE CHART
    base = alt.Chart(pd.DataFrame({"start": 0, "end": 1}, index=[0]))

    # AXIS ENCODING
    axis_values = [0.0, 0.25, 0.5, 0.75, 1]
    bottom_axis = alt.Axis(
        values=axis_values,
        orient="bottom",
        domain=False,
        labels=False,
        ticks=False,
        title=x_metric.upper(),
    )
    left_axis = alt.Axis(
        values=axis_values,
        orient="left",
        domain=False,
        labels=False,
        ticks=False,
        title=y_metric.upper(),
    )

    # X AXIS
    x_rule = base.mark_rule(
        strokeWidth=Rule.stroke_width, stroke=Rule.stroke, tooltip=""
    ).encode(
        x=alt.X("start:Q", scale=scales["x"], axis=bottom_axis),
        x2="end:Q",
        y=alt.Y("start:Q", scale=scales["y"], axis=no_axis()),
    )

    # Y AXIS
    y_rule = base.mark_rule(
        strokeWidth=Rule.stroke_width, stroke=Rule.stroke, tooltip=""
    ).encode(
        x=alt.X("start:Q", scale=scales["x"], axis=no_axis()),
        y=alt.Y("start:Q", scale=scales["y"], axis=left_axis),
        y2="end:Q",
    )

    return x_rule + y_rule


def __draw_bubbles(
    plot_table, x_metric, y_metric, ref_group, scales, interactive_selection_group,
):
    """Draws the bubbles for all metrics."""

    # FILTER DF
    fields_to_keep_in_metric_table = [
        "group_size",
        "attribute_value",
        "total_entities",
        x_metric,
        y_metric,
    ]
    metric_plot_table = plot_table[fields_to_keep_in_metric_table].copy(deep=True)
    metric_plot_table["tooltip_group_size"] = get_tooltip_text_group_size(plot_table)

    # COLOR ENCODING
    bubble_color_encoding = alt.condition(
        interactive_selection_group,
        alt.Color("attribute_value:N", scale=scales["color"], legend=None),
        alt.value(Bubble.color_faded),
    )

    # TOOLTIP ENCODING
    bubble_tooltip_encoding = [
        alt.Tooltip(field="attribute_value", type="nominal", title="Group"),
        alt.Tooltip(field="tooltip_group_size", type="nominal", title="Group Size"),
        alt.Tooltip(
            field=x_metric, type="quantitative", format=".2f", title=x_metric.upper()
        ),
        alt.Tooltip(
            field=y_metric, type="quantitative", format=".2f", title=y_metric.upper()
        ),
    ]

    # BUBBLE CENTERS
    bubbles_centers = (
        alt.Chart(metric_plot_table)
        .mark_point(filled=True, size=Bubble.center_size)
        .encode(
            x=alt.X(f"{x_metric}:Q", scale=scales["x"], axis=no_axis()),
            y=alt.Y(f"{y_metric}:Q", scale=scales["y"], axis=no_axis()),
            tooltip=bubble_tooltip_encoding,
            color=bubble_color_encoding,
            shape=alt.Shape("attribute_value:N", scale=scales["shape"], legend=None),
        )
    )

    # BUBBLE AREAS
    bubbles_areas = (
        alt.Chart(metric_plot_table)
        .mark_circle(opacity=Bubble.opacity)
        .encode(
            size=alt.Size("group_size:Q", legend=None, scale=scales["bubble_size"]),
            x=alt.X(f"{x_metric}:Q", scale=scales["x"], axis=no_axis()),
            y=alt.Y(f"{y_metric}:Q", scale=scales["y"], axis=no_axis()),
            tooltip=bubble_tooltip_encoding,
            color=bubble_color_encoding,
        )
    )

    return bubbles_centers + bubbles_areas


def plot_xy_metrics_chart(
    disparity_df,
    x_metric,
    y_metric,
    attribute,
    fairness_threshold=1.25,
    chart_height=None,
    chart_width=None,
    chart_padding=CHART_PADDING,
    accessibility_mode=False,
):
    """ Draws XY scatterplot, with the group_size encoded in the bubble size, based on the two metrics provided. 
    Optionally draws threshold rules and bands when a fairness threshold value is provided. """

    (
        plot_table,
        x_metric,
        y_metric,
        ref_group,
        global_scales,
        chart_height,
        chart_width,
        interactive_selection_group,
    ) = Initializer.prepare_xy_chart(
        disparity_df,
        x_metric,
        y_metric,
        attribute,
        fairness_threshold,
        chart_height,
        chart_width,
        chart_padding,
        Sizes.XY_Chart,
        accessibility_mode,
    )

    position_scales = __get_position_scales(chart_height, chart_width, chart_padding,)

    scales = dict(global_scales, **position_scales)

    # AXIS RULES
    axis_rules = __draw_axis_rules(x_metric, y_metric, scales)

    # TICK LABELS
    tick_labels = __draw_tick_labels(scales, chart_height, chart_width, chart_padding)

    # INITIATE CHART
    chart = axis_rules + tick_labels

    # THRESHOLD AND BANDS
    if fairness_threshold is not None:
        # REF VALUES
        ref_group_index = plot_table.loc[
            plot_table["attribute_value"] == ref_group
        ].index

        x_ref_group_value = plot_table.loc[ref_group_index, x_metric].iloc[0]
        y_ref_group_value = plot_table.loc[ref_group_index, y_metric].iloc[0]

        # Y AXIS
        if y_metric != "prev":
            y_thresholds = __draw_threshold_bands(
                ref_group_value=y_ref_group_value,
                fairness_threshold=fairness_threshold,
                main_scale=scales["y"],
                aux_scale=scales["x"],
                accessibility_mode=accessibility_mode,
            )

            chart += y_thresholds

        # X AXIS
        if x_metric != "prev":
            x_thresholds = __draw_threshold_bands(
                ref_group_value=x_ref_group_value,
                fairness_threshold=fairness_threshold,
                main_scale=scales["x"],
                aux_scale=scales["y"],
                accessibility_mode=accessibility_mode,
                drawing_x=True,
            )

            chart += x_thresholds

    # LEGEND
    legend = draw_legend(scales, interactive_selection_group, chart_width)

    # BUBBLES
    bubbles = __draw_bubbles(
        plot_table, x_metric, y_metric, ref_group, scales, interactive_selection_group,
    )

    # FINISH CHART COMPOSITION
    chart += legend + bubbles

    # CONFIGURATION
    styled_chart = (
        chart.configure_view(strokeWidth=0)
        .properties(height=chart_height, width=chart_width)
        .configure_axis(
            titleFont=FONT,
            titleColor=Axis.title_color,
            titleFontSize=Axis.title_font_size,
            titleFontWeight=Axis.title_font_weight,
            labelFontSize=Axis.label_font_size,
            labelColor=Axis.label_color,
            labelFont=FONT,
        )
        .resolve_scale(y="independent", x="independent", size="independent")
        .resolve_axis(x="shared", y="shared")
    )

    return styled_chart

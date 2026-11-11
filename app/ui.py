"""Chart theme and small helpers shared by the pages."""
import altair as alt
import streamlit as st

import style
from features import ZONES

ZONE_COLORS = [style.BLUE, style.ORANGE, style.AQUA, style.YELLOW, style.MAGENTA, style.GREEN, style.VIOLET]
ZONE_SCALE = alt.Scale(domain=ZONES, range=ZONE_COLORS)
SEGMENTS = ["Budget starter homes", "Spacious value homes", "Compact city homes", "Premium family homes",
            "Large luxury homes"]
SEG_COLORS = [style.AQUA, style.YELLOW, style.BLUE, style.VIOLET, style.MAGENTA]
SEG_SCALE = alt.Scale(domain=SEGMENTS, range=SEG_COLORS)


def chart(c, height=320):
    st.altair_chart(
        c.properties(height=height).configure_view(strokeWidth=0)
        .configure_axis(gridColor=style.GRID, domainColor="rgba(160,170,230,0.25)", tickColor="rgba(160,170,230,0.25)",
                        labelColor=style.SOFT, titleColor=style.MUTED, labelFontSize=11, titleFontSize=11.5,
                        labelFont="Inter", titleFont="Inter", titleFontWeight=500)
        .configure_legend(labelColor=style.SOFT, titleColor=style.MUTED, orient="top", labelFont="Inter",
                          titleFont="Inter", labelFontSize=11.5, symbolType="circle")
        .configure_title(color=style.INK, font="Inter")
        .configure(background="transparent"), width="stretch")


def lakh_axis(title="Price"):
    """Axis labels in lakh / crore."""
    return alt.Axis(title=title, labelExpr="datum.value >= 100 ? format(datum.value/100, '.1~f') + ' Cr' : "
                                             "format(datum.value, '.0f') + ' L'")


def zone_color():
    return alt.Color("Zone:N", scale=ZONE_SCALE, legend=None)


def zone_legend(zones=None):
    style.legend([(z, c) for z, c in zip(ZONES, ZONE_COLORS) if zones is None or z in zones])


LAKH_TICKS = [20, 50, 100, 200, 500, 1000, 2000]


def log_lakh_axis(title):
    return alt.Axis(title=title, values=LAKH_TICKS, grid=True,
                    labelExpr="datum.value >= 100 ? format(datum.value/100, '.0f') + ' Cr' : format(datum.value, '.0f') + ' L'")

import seaborn as sns
import re
from faicons import icon_svg

# Import data from shared.py
from shared import app_dir, df
from shinywidgets import render_widget, render_plotly
from shiny import reactive
from shiny.express import input, render, ui
import matplotlib.ticker as ticker
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import dayplot as dp
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from shinyswatch import theme



ui.page_opts(title="NYC Motor Vehicle Collisions dashboard", fillable=True, theme=theme.darkly, )




with ui.navset_pill(id="tab"):  
    with ui.nav_panel("Year"):
        with ui.layout_column_wrap(fill=True):
            with ui.value_box(showcase=icon_svg("satellite-dish"), fill=True, width="auto"):
                "Number of Crashes"
                @render.text
                def num_sigthings():
                    return year_df()["count"].sum()
                
            with ui.card():
                ui.input_numeric("year", "Year input", 2019, min=2012, max=2025,  width="auto")  

        with ui.layout_column_wrap(fill=False):
            with ui.card(full_screen=True):
                ui.card_header("Crashes per day heatmap")
                @render.plot
                def heatmap():
                    fig, ax = plt.subplots(figsize=(15, 6), dpi=55)
                    dates = year_df()["CRASH_DATE"]
                    values = year_df()["count"]

                    # Set the colormap and normalization from 0 to 4500
                    cmap = "YlOrRd"
                    norm = plt.Normalize(vmin=0, vmax=4500)

                    # Plot the calendar with the explicit colormap and norm
                    dp.calendar(
                        dates=dates,
                        values=values,
                        start_date=f"{input.year()}-01-01",
                        end_date=f"{input.year()}-12-31",
                        cmap=cmap,
                        vmin=0,
                        vmax=4500,
                        day_kws={"color": "white"},
                        month_kws={"color": "white"},
                        ax=ax,
                    )

                    # Create a ScalarMappable with the same cmap and norm
                    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
                    sm.set_array([])

                    # Add the colorbar and adjust its size
                    cbar = fig.colorbar(sm, ax=ax, pad=0.02, fraction=0.006)
                    cbar.ax.yaxis.set_tick_params(color="white")
                    plt.setp(plt.getp(cbar.ax.axes, "yticklabels"), color="white")

                    fig.set_facecolor("#2d2d2d")
                    ax.set_facecolor("#2d2d2d")
                    return fig
        with ui.layout_column_wrap(fill=False):
            with ui.card(full_screen=True):
                ui.card_header("Crashes per Hour and Minute (Animated)")
                @render.ui
                def plot_crashes():

                    grouped_df = time_grouped
                    selected_year = input.year()
                    fig = go.Figure()

                    # -------- OTHER YEARS (static) --------
                    for year in grouped_df["YEAR"].unique():
                        if year == selected_year:
                            continue

                        year_df = grouped_df[grouped_df["YEAR"] == year]
                        fig.add_trace(
                            go.Scatter(
                                x=year_df["CRASH_HOUR_MINUTE"],
                                y=year_df["count"],
                                name=str(year),
                                line=dict(color="gray", width=1),
                                showlegend=False,
                            )
                        )

                    # -------- SELECTED YEAR (animated) --------
                    selected_df = grouped_df[grouped_df["YEAR"] == selected_year]

                    # Frames: progressively reveal the line
                    frames = []
                    for i in range(1, len(selected_df) + 1):
                        frames.append(
                            go.Frame(
                                data=[
                                    go.Scatter(
                                        x=selected_df["CRASH_HOUR_MINUTE"].iloc[:i],
                                        y=selected_df["count"].iloc[:i],
                                        mode="lines",
                                        line=dict(color="orange", width=3)
                                    )
                                ],
                                name=f"frame{i}"
                            )
                        )

                    fig.frames = frames

                    fig.update_layout(
                        updatemenus=[
                            {
                                "type": "buttons",
                                "showactive": False,
                                "buttons": [
                                    {
                                        "label": "Play",
                                        "method": "animate",
                                        "args": [
                                            None,
                                            {
                                                "frame": {"duration": 30, "redraw": False},
                                                "fromcurrent": True,
                                                "transition": {"duration": 0}
                                            }
                                        ]
                                    }
                                ],
                                "pad": {"r": 0, "t": 0},
                                "x": 0.97,
                                "y": 0.98
                            }
                        ]
                    )

                    # Usual layout
                    fig.update_layout(
                        title="Crashes per 15-Minute Interval by Year",
                        xaxis_title="Time of Day",
                        yaxis_title="Number of Crashes",
                        xaxis=dict(tickformat="%H:%M", tickangle=45),
                        font_color="white",
                        plot_bgcolor="#2d2d2d",
                        paper_bgcolor="#2d2d2d",
                    )

                    return ui.HTML(fig.to_html())



ui.include_css(app_dir / "styles.css")

@reactive.calc
def filtered_df():
    filt_df = df
    return filt_df

df["CRASH_DATE"] = pd.to_datetime(df["CRASH_DATE"])
df["CRASH_TIME"] = pd.to_datetime(df["CRASH_TIME"], format="%H:%M")
df["CRASH_HOUR_MINUTE"] = df["CRASH_TIME"].dt.floor("15T").dt.strftime("%H:%M")
df["YEAR"] = df["CRASH_DATE"].dt.year

time_grouped = df.groupby(["CRASH_HOUR_MINUTE", "YEAR"]).size().reset_index(name="count")

day_grouped = (
    df
    .groupby(["YEAR", df["CRASH_DATE"].dt.date])
    .size()
    .reset_index(name="count")
    .rename(columns={0: "count"})
)

day_grouped["CRASH_DATE"] = pd.to_datetime(day_grouped["CRASH_DATE"])

@reactive.calc
def year_df():
    return day_grouped[day_grouped["YEAR"] == input.year()]


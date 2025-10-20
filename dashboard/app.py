import seaborn as sns
import re
from faicons import icon_svg

# Import data from shared.py
from shared import app_dir, df

from shiny import reactive
from shiny.express import input, render, ui
import matplotlib.ticker as ticker
import matplotlib.pyplot as plt
import dayplot as dp
import pandas as pd
import plotly.express as px
from shinyswatch import theme

ui.page_opts(title="NYC Motor Vehicle Collisions dashboard", fillable=True, theme=theme.darkly)




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
                ui.card_header("Sights per day heatmap")

                @render.plot
                def heatmap():
                    fig, ax = plt.subplots(figsize=(15, 6), dpi=55)
                    # Extract dates and values from the grouped data
                    dates = year_df()["CRASH_DATE"]
                    values = year_df()["count"]

                    dp.calendar(
                        dates=dates,
                        values=values,
                        start_date=f"{input.year()}-01-01",
                        end_date=f"{input.year()}-12-31",
                        day_kws={"color": "white"},
                        month_kws={"color": "white"},
                        ax=ax,
                    )
                    fig.set_facecolor("#2d2d2d")
                    ax.set_facecolor("#2d2d2d")
                    return fig
            #with ui.card(full_screen=True):
            #    ui.card_header("Sights per day heatmap")
#
            #    @render.plot
            #    def histogram():
            #        fig = px.histogram(country_df(), x=)
            #        fig.update_xaxes(type='category')
            
                
    with ui.nav_panel("A"):
        with ui.layout_column_wrap(fill=False):
            with ui.value_box(showcase=icon_svg("satellite-dish")):
                "Number of Sightings"

                @render.text
                def count():
                    return filtered_df().shape[0]
                

            with ui.value_box(showcase=icon_svg("hourglass-start")):
                "Average Length of Encounter in Seconds"

                @render.text
                def bill_length():
                    return f"{filtered_df()['length_of_encounter_seconds'].mean():.1f} seconds"
                
            with ui.value_box(showcase=icon_svg("calendar-days")):
                "Average Sightings Per Year"

                @render.text
                def bill_depth():
                    return f"{year_df()['Unnamed: 0'].mean():.1f} Sightings"

        with ui.layout_columns():
            with ui.card(full_screen=True):
                ui.card_header("Experience and Anual Base Pay")

                @render.plot
                def length_depth():
                    ax = sns.scatterplot(
                        data=year_df(),
                        x="Year",
                        y="Unnamed: 0"
                    )
                    # Force decimal notation
                    ax.yaxis.set_major_formatter(ticker.ScalarFormatter(useOffset=False))
                    ax.ticklabel_format(style='plain', axis='y')
                    return ax

            with ui.card(full_screen=True):
                ui.card_header("UFO Sightings Data")

                @render.data_frame
                def summary_statistics():
                    cols = [
                        "Date_time",
                        "Country",
                        "Region",
                        "UFO_shape",
                        "length_of_encounter_seconds",
                    ]
                    return render.DataGrid(filtered_df()[cols], filters=True)
                
    with ui.nav_panel("B"):
        "This is the second 'page'."


ui.include_css(app_dir / "styles.css")

@reactive.calc
def filtered_df():
    filt_df = df
    return filt_df

@reactive.calc
def year_df():
    # Convert CRASH_DATE to datetime if it's not already
    df["CRASH_DATE"] = pd.to_datetime(df["CRASH_DATE"])
    # Filter by year
    filt_df = df[df["CRASH_DATE"].dt.year == input.year()]
    # Group by date and count occurrences
    grouped = filt_df.groupby(filt_df["CRASH_DATE"].dt.date).size().reset_index(name="count")
    return grouped


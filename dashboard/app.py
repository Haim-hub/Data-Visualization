import seaborn as sns
import re
from faicons import icon_svg

# Import data from shared.py
from shared import app_dir, df, salary_df

from shiny import reactive
from shiny.express import input, render, ui
import matplotlib.ticker as ticker

ui.page_opts(title="UFO Sightings dashboard", fillable=True)



#with ui.sidebar(title="Filter controls"):
#    ui.input_slider("mass", "Mass", 2000, 6000, 6000)
#    ui.input_checkbox_group(
#        "species",
#        "Species",
#        ["Adelie", "Gentoo", "Chinstrap"],
#        selected=["Adelie", "Gentoo", "Chinstrap"],
#    )

with ui.navset_pill(id="tab"):  
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
    filt_df = df.groupby(by="Year").count()
    return filt_df

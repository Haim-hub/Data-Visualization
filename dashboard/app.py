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
import dayplot as dp
import pandas as pd
import plotly.express as px
from shinyswatch import theme


ui.page_opts(
    title="NYC Motor Vehicle Collisions dashboard",
    fillable=True,
    theme=theme.darkly,
)

scale_state = reactive.Value(True)  # False = linear, True = log


@reactive.effect
@reactive.event(input.toggle_scale)
def _():
    scale_state.set(not scale_state.get())


with ui.navset_pill(id="tab"):
    with ui.nav_panel("Year"):
        with ui.layout_column_wrap(fill=True):
            with ui.value_box(
                showcase=icon_svg("satellite-dish"), fill=True, width="auto"
            ):
                "Number of Crashes"

                @render.text
                def injury_types():
                    return year_df()["count"].sum()

            with ui.card():
                ui.input_numeric(
                    "year", "Year input", 2019, min=2012, max=2025, width="auto"
                )

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
                def show_animation():
                    return ui.img(src="crashes_animation.gif", alt="Animation")

    with ui.nav_panel("Injury"):
        with ui.layout_column_wrap(fill=False):
            with ui.card(full_screen=True):
                ui.card_header("Types of resulting injury")

                @render_plotly
                def injury_plot():
                    df_injured = df[df["BODILY_INJURY"] != "Does Not Apply"]
                    injury_counts = (
                        df_injured["BODILY_INJURY"]
                        .dropna()
                        .value_counts()
                        .reset_index()
                    )

                    injury_counts.columns = ["InjuryType", "Count"]
                    fig = px.bar(
                        injury_counts,
                        x="InjuryType",
                        y="Count",
                        title="Distribution of Bodily Injury Types",
                        text="Count",
                    )
                    fig.update_layout(xaxis_tickangle=45)

                    return fig

            with ui.card(full_screen=True):
                ui.card_header("Relationship between safety equipment and being yeeted")

                @render_plotly
                def safety_ejection_plot_card():
                    relationship_counts = (
                        df.groupby(["SAFETY_EQUIPMENT", "EJECTION"])
                        .size()
                        .reset_index(name="Count")
                    )

                    relationship_counts = relationship_counts.fillna(
                        "Unknown/Not Reported"
                    )

                    fig = px.bar(
                        relationship_counts,
                        x="SAFETY_EQUIPMENT",
                        y="Count",
                        color="SAFETY_EQUIPMENT",
                        barmode="group",
                        title=f"Relationship Between Safety Equipment and Ejection Status",
                        labels={
                            "SAFETY_EQUIPMENT": "Safety Equipment Used",
                            "EJECTION": "Ejection Status",
                            "Count": "Number of Incidents",
                        },
                        height=500,
                        template="plotly_white",
                    )

                    fig.update_layout(
                        xaxis_tickangle=45, legend_title_text="Ejection Status"
                    )

                    return fig

        # injured & killed, unspecified injuries to age
        with ui.layout_column_wrap(fill=False):

            with ui.card(full_screen=True):
                ui.card_header("Injured vs Killed by Age Group")

                ui.input_action_button(
                    "toggle_scale",
                    "Toggle Log/Linear Scale",  # Static label
                    width="200px",
                )

                @render.text
                def scale_status():
                    return (
                        "Current scale: Logarithmic"
                        if scale_state.get()
                        else "Current scale: Linear"
                    )

                @render_plotly
                def injury_age_plot():
                    age_groups = ["0-17", "18-24", "25-44", "45-64", "65+"]
                    injury_data = []

                    df_all_ages = df["PERSON_AGE"].dropna()
                    df_all_ages = df_all_ages[
                        df_all_ages.apply(lambda x: str(x).isdigit())
                    ]
                    df_all_ages = df_all_ages.astype(int)

                    for age_group in age_groups:
                        if age_group == "0-17":
                            age_filtered = df_all_ages[df_all_ages <= 17]
                        elif age_group == "18-24":
                            age_filtered = df_all_ages[
                                (df_all_ages >= 18) & (df_all_ages <= 24)
                            ]
                        elif age_group == "25-44":
                            age_filtered = df_all_ages[
                                (df_all_ages >= 25) & (df_all_ages <= 44)
                            ]
                        elif age_group == "45-64":
                            age_filtered = df_all_ages[
                                (df_all_ages >= 45) & (df_all_ages <= 64)
                            ]
                        else:  # "65+"
                            age_filtered = df_all_ages[df_all_ages >= 65]

                        injured_count = df[
                            (df["PERSON_AGE"].isin(age_filtered))
                            & (df["PERSON_INJURY"] == "Injured")
                        ].shape[0]
                        killed_count = df[
                            (df["PERSON_AGE"].isin(age_filtered))
                            & (df["PERSON_INJURY"] == "Killed")
                        ].shape[0]

                        injury_data.append(
                            {
                                "Age Group": age_group,
                                "Injured": injured_count,
                                "Killed": killed_count,
                            }
                        )

                    injury_df = pd.DataFrame(injury_data)
                    fig = px.bar(
                        injury_df,
                        x="Age Group",
                        y=["Injured", "Killed"],
                        title="Injured vs Killed by Age Group",
                        barmode="group",
                        color="variable",
                        labels={
                            "value": "Number of People",
                            "variable": "Injury Status",
                        },
                        template="plotly_white",
                    )

                    yaxis_type = "log" if scale_state.get() else "linear"
                    fig.update_layout(
                        xaxis_tickangle=45,
                        yaxis_type=yaxis_type,
                        legend_title_text="Injury Status ",
                    )

                    return fig

        with ui.layout_column_wrap(fill=True):
            # Relation chart between position and injury
            with ui.card(full_screen=True):
                ui.card_header("Relation between position and injury")

                @render_plotly
                def position_injury_plot():
                    relationship_counts = (
                        df.groupby(["POSITION_IN_VEHICLE", "PERSON_INJURY"])
                        .size()
                        .reset_index(name="Count")
                    )

                    all_positions_unique = {
                        "Any person in the rear of a station wagon, pick-up truck, all passengers on a bus, etc": "Rear of vehicle (other)",
                        "Front passenger, if two or more persons, including the driver, are in the front seat": "Front passenger",
                        "If one person is seated on another person&apos;s lap": "Seated on lap",
                        "Left rear passenger, or rear passenger on a bicycle, motorcycle, snowmobile": "Left rear passenger",
                        "Middle front seat, or passenger lying across a seat": "Middle front seat",
                        "Middle rear seat, or passenger lying across a seat": "Middle rear seat",
                        "Riding/Hanging on Outside": "Riding/Hanging on Outside",
                        "Driver": "Driver",
                        "Right rear passenger or motorcycle sidecar passenger": "Right rear passenger",
                        "Unknown": "Unknown",
                    }

                    relationship_counts = relationship_counts.dropna()
                    # Exclude Driver and Does Not Apply
                    relationship_counts = relationship_counts[
                        ~relationship_counts["POSITION_IN_VEHICLE"].isin(
                            ["Does Not Apply"]
                        )
                    ]
                    # Translate them
                    relationship_counts["POSITION_IN_VEHICLE"] = relationship_counts[
                        "POSITION_IN_VEHICLE"
                    ].map(all_positions_unique)

                    fig = px.bar(
                        relationship_counts,
                        x="POSITION_IN_VEHICLE",
                        y="Count",
                        color="POSITION_IN_VEHICLE",
                        title=f"Relationship Between Position and Injury Status",
                        labels={
                            "POSITION_IN_VEHICLE": "Position in Vehicle",
                            "PERSON_INJURY": "Injury Status",
                            "Count": "Number of Incidents",
                        },
                        template="plotly_white",
                        hover_data=["PERSON_INJURY"],
                    )

                    fig.update_layout(
                        xaxis_tickangle=45,
                        legend_title_text="Injury Status",
                        yaxis_type="log",
                    )

                    return fig

    with ui.nav_panel("AI"):
        with ui.value_box(showcase=icon_svg("satellite-dish"), fill=True, width="auto"):
            "Number of Crashes"

            @render.text
            def num_sigthingss():
                return time_df()["count"].sum()


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
    grouped = (
        filt_df.groupby(filt_df["CRASH_DATE"].dt.date).size().reset_index(name="count")
    )
    grouped["CRASH_DATE"] = pd.to_datetime(grouped["CRASH_DATE"])
    return grouped


@reactive.calc
def time_df():
    # Convert CRASH_TIME to datetime, specifying the format
    df["CRASH_TIME"] = pd.to_datetime(df["CRASH_TIME"], format="%H:%M")

    # Extract only the time component (hour and minute)
    df["CRASH_HOUR_MINUTE"] = df["CRASH_TIME"].dt.strftime("%H:%M")

    # Group by the time component and count occurrences
    grouped = df.groupby("CRASH_HOUR_MINUTE").size().reset_index(name="count")

    return grouped

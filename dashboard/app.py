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
        with ui.card(full_screen=True):
            ui.card_header("Crashes by Age and Gender")
            ui.input_switch("drivers_only", "Show Drivers Only", value=False)
            @render_plotly
            def age_sex_histogram_chart():
                d = filtered_year_data()
                
                # --- ROBUST DATA CLEANING ---
                # Explicitly use .copy() to ensure 'd' is a new object and avoid SettingWithCopyWarning
                d = d.copy()
                
                # Apply Drivers Only filter if switch is on
                if input.drivers_only():
                    d = d[d["POSITION_IN_VEHICLE"] == "Driver"]
                
                d["PERSON_AGE"] = pd.to_numeric(d["PERSON_AGE"], errors='coerce')
                
                # When dropping NaNs, force a copy so subsequent assignments don't trigger warnings
                d = d.dropna(subset=["PERSON_AGE"]).copy()
                
                # Now safe to convert
                d["PERSON_AGE"] = d["PERSON_AGE"].astype(int)
                
                # Filter Age (1-100) and Sex (M/F)
                d = d[(d["PERSON_AGE"] >= 1) & (d["PERSON_AGE"] <= 100)]
                d = d[d["PERSON_SEX"].isin(["M", "F"])]
                
                # Group by Age and Sex
                age_sex_counts = d.groupby(["PERSON_AGE", "PERSON_SEX"]).size().unstack(fill_value=0)
                
                # Ensure columns exist
                if "M" not in age_sex_counts.columns: age_sex_counts["M"] = 0
                if "F" not in age_sex_counts.columns: age_sex_counts["F"] = 0
                
                age_sex_counts = age_sex_counts.sort_index()
                ages = age_sex_counts.index
                men_counts = age_sex_counts["M"]
                women_counts = age_sex_counts["F"]

                # --- PLOTLY CONSTRUCTION ---
                fig = go.Figure()

                # 1. Women (Right side, Positive)
                fig.add_trace(go.Bar(
                    y=ages,
                    x=women_counts,
                    orientation='h',
                    name='Women',
                    marker_color='#e74c3c',
                    hoverinfo='x+y'
                ))

                # 2. Men (Left side, Negative)
                # We make values negative for position, but use 'customdata' for hover text
                fig.add_trace(go.Bar(
                    y=ages,
                    x=-men_counts,
                    orientation='h',
                    name='Men',
                    marker_color='#3498db',
                    customdata=men_counts, # Actual positive counts
                    hovertemplate='Men: %{customdata}<br>Age: %{y}<extra></extra>'
                ))

                # 3. Layout Adjustments
                title_suffix = " (Drivers Only)" if input.drivers_only() else ""
                fig.update_layout(
                    title=f"Crash Distribution by Age ({input.year()}){title_suffix}",
                    barmode='overlay', # Overlay allows them to share the row without stacking
                    bargap=0.1,
                    xaxis=dict(
                        title='Count',
                        tickmode='sync',
                        # Custom tick formatter to show positive numbers for negative values
                        tickformat='s' 
                    ),
                    yaxis=dict(
                        title='Age',
                        range=[100, 0] # Reverses the axis: 0 at top, 100 at bottom
                    ),
                    legend=dict(x=0.8, y=0.9),
                    margin=dict(l=20, r=20, t=50, b=20)
                )
                
                # Optional: Force X-axis to be symmetric
                max_val = max(men_counts.max(), women_counts.max()) if not age_sex_counts.empty else 10
                limit = max_val * 1.1
                fig.update_xaxes(range=[-limit, limit])

                # Fix the negative tick labels on X-axis using standard JS format
                fig.update_layout(xaxis=dict(ticksuffix=""))

                return fig
            
            @render_plotly
            def age_sex_chart():
                d = filtered_year_data()
                
                # --- ROBUST DATA CLEANING ---
                d = d.copy()
                
                # Apply Drivers Only filter if switch is on
                if input.drivers_only():
                    d = d[d["POSITION_IN_VEHICLE"] == "Driver"]
                
                d["PERSON_AGE"] = pd.to_numeric(d["PERSON_AGE"], errors='coerce')
                d = d.dropna(subset=["PERSON_AGE"]).copy()
                d["PERSON_AGE"] = d["PERSON_AGE"].astype(int)
                
                # Filter Age (1-100) and Sex (M/F)
                d = d[(d["PERSON_AGE"] >= 1) & (d["PERSON_AGE"] <= 100)]
                d = d[d["PERSON_SEX"].isin(["M", "F"])]

                # --- PLOTLY BOXPLOT CONSTRUCTION ---
                fig = go.Figure()

                # 1. Women Boxplot
                fig.add_trace(go.Box(
                    y=d[d["PERSON_SEX"] == "F"]["PERSON_AGE"],
                    name='Women',
                    marker_color='#e74c3c',
                    boxpoints='outliers', # Only show outlier points to keep it clean
                    showlegend=False
                ))

                # 2. Men Boxplot
                fig.add_trace(go.Box(
                    y=d[d["PERSON_SEX"] == "M"]["PERSON_AGE"],
                    name='Men',
                    marker_color='#3498db',
                    boxpoints='outliers',
                    showlegend=False
                ))

                # 3. Layout Adjustments
                title_suffix = " (Drivers Only)" if input.drivers_only() else ""
                fig.update_layout(
                    title=f"Age Distribution by Gender ({input.year()}){title_suffix}",
                    yaxis_title="Age",
                    xaxis_title="Gender",
                    margin=dict(l=40, r=20, t=50, b=40),
                    template="plotly_white"
                )

                return fig
    
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


    with ui.nav_panel("Injury"):
        with ui.layout_columns(fill=False, col_widths=(4, 8)):
            with ui.card(full_screen=True):
                ui.card_header("Types of resulting injury")
                with ui.card_body(padding=0):
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
                            text="Count",
                        )
                        fig.update_layout(
                            plot_bgcolor='rgba(0,0,0,0)',
                            paper_bgcolor='rgba(0,0,0,0)',
                            font_color='white',
                            xaxis_tickangle=-45
                        )
                    

                        return fig
            with ui.card(full_screen=True):
                ui.card_header("Relationship between safety equipment and being thrown from the vehicle")
                with ui.card_body(padding=0):
                    @render_plotly
                    def safety_ejection_plot_card():
                        df_status = df[
                            (~df['EJECTION'].isin(['Unknown', 'Does Not Apply'])) &
                            (~df['SAFETY_EQUIPMENT'].isin(['-', 'Unknown']))
                        ].copy()
                        
                        equipment_map = {
                            'Air Bag Deployed': 'Air Bag',
                            'Air Bag Deployed/Lap Belt': 'Air Bag + Lap Belt',
                            'Air Bag Deployed/Child Restraint': 'Air Bag + Child Rstrnt',
                            'Air Bag Deployed/Lap Belt/Harness': 'Air Bag + LB + Hrnss',
                            'Child Restraint Only': 'Child Rstrnt',
                            'Helmet (Motorcycle Only)': 'Helm (Mtr)',
                            'Helmet/Other (In-Line Skater/Bicyclist)': 'Helm/Othr (Sk8/Bike)',
                            'Helmet Only (In-Line Skater/Bicyclist)': 'Helm (Sk8/Bike)',
                            'Pads Only (In-Line Skater/Bicyclist)': 'Pads (Sk8/Bike)',
                            'Stoppers Only (In-Line Skater/Bicyclist)': 'Stoppers (Sk8/Bike)',
                        }
    
                        df_status['SAFETY_EQUIPMENT_SHORT'] = df_status['SAFETY_EQUIPMENT'].apply(
                            lambda x: equipment_map.get(x, x)
                        )
                        
                        df_grouped = df_status.groupby(['SAFETY_EQUIPMENT_SHORT', 'SAFETY_EQUIPMENT', 'EJECTION']).size().reset_index(name='Count')
                        df_grouped['TOTAL_PER_EQUIPMENT'] = df_grouped.groupby('SAFETY_EQUIPMENT_SHORT')['Count'].transform('sum')
                        df_grouped['PERCENTAGE'] = (df_grouped['Count'] / df_grouped['TOTAL_PER_EQUIPMENT']) * 100
                        df_grouped['PERCENTAGE'] = df_grouped['PERCENTAGE'].round(1)

                        fig = px.bar(
                            df_grouped,
                            x="SAFETY_EQUIPMENT_SHORT",
                            y="PERCENTAGE",
                            color="EJECTION",
                            barmode="stack",
                            hover_data={"SAFETY_EQUIPMENT_SHORT": False, "SAFETY_EQUIPMENT": False},
                            hover_name="SAFETY_EQUIPMENT",
                            labels={
                                "SAFETY_EQUIPMENT_SHORT": "Type of Safety Equipment Used",
                                "PERCENTAGE": "Ejection Status (%)",
                                "EJECTION": "Ejection Status",
                            },
                            text='PERCENTAGE',
                            category_orders={"EJECTION": ["Not Ejected", "Trapped", "Partially Ejected", "Ejected"]},
                            height=600,
                            template="plotly_white"
                        )
                        fig.update_traces(texttemplate='%{y:.1f}%', textposition='inside')
                        fig.update_yaxes(range=[0, 100], ticksuffix='%')                  
                        fig.update_layout(
                            plot_bgcolor='rgba(0,0,0,0)',
                            paper_bgcolor='rgba(0,0,0,0)',
                            font_color='white',
                            xaxis_tickangle=-45
                        )  

                        return fig
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
    
    with ui.nav_panel("About"):
        pass


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

@reactive.calc
def filtered_year_data():
    """Filters the main dataframe based on the selected year."""
    selected_year = int(input.year())
    return df[df["YEAR"] == selected_year].copy()

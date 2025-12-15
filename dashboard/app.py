from faicons import icon_svg


from shared import app_dir, df, time_grouped, day_grouped
from shinywidgets import render_plotly
from shiny import reactive
from shiny.express import input, render, ui
import matplotlib.pyplot as plt
import dayplot as dp
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from shinyswatch import theme


ui.page_opts(
    title="NYC Motor Vehicle Collisions Dashboard",
    fillable=True,
    theme=theme.darkly,
)

scale_state = reactive.Value(True)  # False = linear, True = log
position_scale_state = reactive.Value(True)  # False = linear, True = log


@reactive.effect
@reactive.event(input.toggle_scale)
def _():
    scale_state.set(not scale_state.get())

@reactive.effect
@reactive.event(input.toggle_position_scale)
def _():
    position_scale_state.set(not position_scale_state.get())


with ui.navset_pill(id="tab"):
    with ui.nav_panel("Year"):
        with ui.layout_column_wrap(fill=True):
            with ui.value_box(
                showcase=icon_svg("car-burst"), fill=True, width="auto"
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
                
                d = d.copy()
                

                if input.drivers_only():
                    d = d[d["POSITION_IN_VEHICLE"] == "Driver"]
                
                d["PERSON_AGE"] = pd.to_numeric(d["PERSON_AGE"], errors='coerce')
                
                d = d.dropna(subset=["PERSON_AGE"]).copy()
                
                d["PERSON_AGE"] = d["PERSON_AGE"].astype(int)
                
                d = d[(d["PERSON_AGE"] >= 1) & (d["PERSON_AGE"] <= 100)]
                d = d[d["PERSON_SEX"].isin(["M", "F"])]
                
                age_sex_counts = d.groupby(["PERSON_AGE", "PERSON_SEX"]).size().unstack(fill_value=0)
                
                if "M" not in age_sex_counts.columns: age_sex_counts["M"] = 0
                if "F" not in age_sex_counts.columns: age_sex_counts["F"] = 0
                
                age_sex_counts = age_sex_counts.sort_index()
                ages = age_sex_counts.index
                men_counts = age_sex_counts["M"]
                women_counts = age_sex_counts["F"]

                fig = go.Figure()

                fig.add_trace(go.Bar(
                    y=ages,
                    x=women_counts,
                    orientation='h',
                    name='Women',
                    width=1,
                    marker=dict(
                        color="#B36A7A",
                        line=dict(
                            color='#A35A6A', 
                            width=0.2
                        )
                    ),
                    hoverinfo='x+y'
                ))

                fig.add_trace(go.Bar(
                    y=ages,
                    x=-men_counts,
                    orientation='h',
                    name='Men',
                    width=1,
                    marker=dict(
                        color="#6AA2B3",
                        line=dict(
                            color='#5A92A3', 
                            width=0.2
                        )
                    ),
                    customdata=men_counts,
                    hovertemplate='Men: %{customdata}<br>Age: %{y}<extra></extra>'
                ))

                title_suffix = " (Drivers Only)" if input.drivers_only() else ""
                fig.update_layout(
                    title=f"Crash Distribution by Age ({input.year()}){title_suffix}",
                    barmode='overlay',
                    bargap=1,
                    xaxis=dict(
                        title='Count',
                        tickmode='sync',
                        tickformat='s' 
                    ),
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    font_color="white",
                    yaxis=dict(
                        title='Age',
                        dtick=5,
                        range=[100, 0] 
                    ),
                    legend=dict(x=0.8, y=0.9),
                    margin=dict(l=20, r=20, t=50, b=20)
                )
                
                max_val = max(men_counts.max(), women_counts.max()) if not age_sex_counts.empty else 10
                limit = max_val * 1.1
                fig.update_xaxes(range=[-limit, limit])

                fig.update_layout(xaxis=dict(ticksuffix=""))

                return fig
            
            @render_plotly
            def age_sex_chart():
                d = filtered_year_data()
                
                d = d.copy()
                
                if input.drivers_only():
                    d = d[d["POSITION_IN_VEHICLE"] == "Driver"]
                
                d["PERSON_AGE"] = pd.to_numeric(d["PERSON_AGE"], errors='coerce')
                d = d.dropna(subset=["PERSON_AGE"]).copy()
                d["PERSON_AGE"] = d["PERSON_AGE"].astype(int)
                
                d = d[(d["PERSON_AGE"] >= 1) & (d["PERSON_AGE"] <= 100)]
                d = d[d["PERSON_SEX"].isin(["M", "F"])]

                fig = go.Figure()

                fig.add_trace(go.Box(
                    y=d[d["PERSON_SEX"] == "M"]["PERSON_AGE"],
                    name='Men',
                    marker_color='#6AA2B3',
                    boxpoints='outliers',
                    showlegend=False
                ))

                fig.add_trace(go.Box(
                    y=d[d["PERSON_SEX"] == "F"]["PERSON_AGE"],
                    name='Women',
                    marker_color='#B36A7A',
                    boxpoints='outliers', 
                    showlegend=False
                ))

                title_suffix = " (Drivers Only)" if input.drivers_only() else ""
                fig.update_layout(
                    title=f"Age Distribution by Gender ({input.year()}){title_suffix}",
                    yaxis_title="Age",
                    xaxis_title="Gender",
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    font_color="white",
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

                    cmap = "YlOrRd"
                    norm = plt.Normalize(vmin=0, vmax=4500)

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

                    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
                    sm.set_array([])

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

                    selected_df = grouped_df[grouped_df["YEAR"] == selected_year]

                    frames = []
                    for i in range(1, len(selected_df) + 1):
                        frames.append(
                            go.Frame(
                                data=[
                                    go.Scatter(
                                        x=selected_df["CRASH_HOUR_MINUTE"].iloc[:i],
                                        y=selected_df["count"].iloc[:i],
                                        mode="lines",
                                        line=dict(color="orange", width=3),
                                    )
                                ],
                                name=f"frame{i}",
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
                                                "frame": {
                                                    "duration": 30,
                                                    "redraw": False,
                                                },
                                                "fromcurrent": True,
                                                "transition": {"duration": 0},
                                            },
                                        ],
                                    }
                                ],
                                "pad": {"r": 0, "t": 0},
                                "x": 0.97,
                                "y": 0.98,
                            }
                        ]
                    )

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
                        fig.update_traces(marker_color='orange')
                        fig.update_layout(
                            plot_bgcolor="rgba(0,0,0,0)",
                            paper_bgcolor="rgba(0,0,0,0)",
                            font_color="white",
                            xaxis_tickangle=-45,
                        )

                        return fig

            with ui.card(full_screen=True):
                ui.card_header(
                    "Relationship between safety equipment and being thrown from the vehicle"
                )
                with ui.card_body(padding=0):

                    @render_plotly
                    def safety_ejection_plot_card():
                        df_status = df[
                            (~df["EJECTION"].isin(["Unknown", "Does Not Apply"]))
                            & (~df["SAFETY_EQUIPMENT"].isin(["-", "Unknown"]))
                        ].copy()

                        equipment_map = {
                            "Air Bag Deployed": "Air Bag",
                            "Air Bag Deployed/Lap Belt": "Air Bag + Lap Belt",
                            "Air Bag Deployed/Child Restraint": "Air Bag + Child Rstrnt",
                            "Air Bag Deployed/Lap Belt/Harness": "Air Bag + LB + Hrnss",
                            "Child Restraint Only": "Child Rstrnt",
                            "Helmet (Motorcycle Only)": "Helm (Mtr)",
                            "Helmet/Other (In-Line Skater/Bicyclist)": "Helm/Othr (Sk8/Bike)",
                            "Helmet Only (In-Line Skater/Bicyclist)": "Helm (Sk8/Bike)",
                            "Pads Only (In-Line Skater/Bicyclist)": "Pads (Sk8/Bike)",
                            "Stoppers Only (In-Line Skater/Bicyclist)": "Stoppers (Sk8/Bike)",
                        }

                        df_status["SAFETY_EQUIPMENT_SHORT"] = df_status[
                            "SAFETY_EQUIPMENT"
                        ].apply(lambda x: equipment_map.get(x, x))

                        df_grouped = (
                            df_status.groupby(
                                [
                                    "SAFETY_EQUIPMENT_SHORT",
                                    "SAFETY_EQUIPMENT",
                                    "EJECTION",
                                ]
                            )
                            .size()
                            .reset_index(name="Count")
                        )
                        df_grouped["TOTAL_PER_EQUIPMENT"] = df_grouped.groupby(
                            "SAFETY_EQUIPMENT_SHORT"
                        )["Count"].transform("sum")
                        df_grouped["PERCENTAGE"] = (
                            df_grouped["Count"] / df_grouped["TOTAL_PER_EQUIPMENT"]
                        ) * 100
                        df_grouped["PERCENTAGE"] = df_grouped["PERCENTAGE"].round(1)

                        injury_colors = {
                            "Not Ejected": "#FFF8DC",
                            "Trapped": "yellow",
                            "Partially Ejected": "orange",
                            "Ejected": "red"
                        }

                        fig = px.bar(
                            df_grouped,
                            x="SAFETY_EQUIPMENT_SHORT",
                            y="PERCENTAGE",
                            color="EJECTION",
                            color_discrete_map=injury_colors,
                            barmode="stack",
                            hover_data={
                                "SAFETY_EQUIPMENT_SHORT": False,
                                "SAFETY_EQUIPMENT": False,
                            },
                            hover_name="SAFETY_EQUIPMENT",
                            labels={
                                "SAFETY_EQUIPMENT_SHORT": "Type of Safety Equipment Used",
                                "PERCENTAGE": "Ejection Status (%)",
                                "EJECTION": "Ejection Status",
                            },
                            text="PERCENTAGE",
                            category_orders={
                                "EJECTION": [
                                    "Not Ejected",
                                    "Trapped",
                                    "Partially Ejected",
                                    "Ejected",
                                ]
                            },
                            template="plotly_white",
                        )
                        fig.update_traces(
                            texttemplate="%{y:.1f}%", textposition="inside"
                        )
                        fig.update_yaxes(range=[0, 100], ticksuffix="%")
                        fig.update_layout(
                            plot_bgcolor="rgba(0,0,0,0)",
                            paper_bgcolor="rgba(0,0,0,0)",
                            font_color="white",
                            xaxis_tickangle=-45,
                        )

                        return fig

            with ui.layout_column_wrap(fill=False):
                with ui.card(full_screen=True):
                    ui.card_header("Injured vs Killed by Age Group")

                    @render.ui
                    def toggle_scale_ui():

                        current_scale = scale_state.get()

                        if current_scale:
                            label = "Switch to Linear Scale"
                        else:
                            label = "Switch to Logarithmic Scale"


                        return ui.input_action_button(
                            "toggle_scale",
                            label,
                            width="250px",
                        )

                    @render_plotly
                    def injury_age_plot():
                        age_groups = ["0-17", "18-24", "25-44", "45-64", "65+"]
                        injury_data = []

                        df_clean = df.dropna(subset=["PERSON_AGE"])
                        
                        for age_group in age_groups:
                            if age_group == "0-17":
                                mask = df_clean["PERSON_AGE"] <= 17
                            elif age_group == "18-24":
                                mask = (df_clean["PERSON_AGE"] >= 18) & (df_clean["PERSON_AGE"] <= 24)
                            elif age_group == "25-44":
                                mask = (df_clean["PERSON_AGE"] >= 25) & (df_clean["PERSON_AGE"] <= 44)
                            elif age_group == "45-64":
                                mask = (df_clean["PERSON_AGE"] >= 45) & (df_clean["PERSON_AGE"] <= 64)
                            else:  # "65+"
                                mask = df_clean["PERSON_AGE"] >= 65

                            group_data = df_clean[mask]

                            injured_count = len(group_data[group_data["PERSON_INJURY"] == "Injured"])
                            killed_count = len(group_data[group_data["PERSON_INJURY"] == "Killed"])

                            injury_data.append(
                                {
                                    "Age Group": age_group,
                                    "Injured": injured_count,
                                    "Killed": killed_count,
                                }
                            )

                        injury_df = pd.DataFrame(injury_data)

                        injury_colors = {
                            "Injured": "orange",
                            "Killed": "red",
                        }

                        fig = px.bar(
                            injury_df,
                            x="Age Group",
                            y=["Injured", "Killed"],
                            title="Injured vs Killed by Age Group",
                            barmode="group",
                            color_discrete_map=injury_colors,
                            labels={
                                "value": "Number of People",
                                "variable": "Injury Status",
                            },
                            template="plotly_white",
                        )

                        yaxis_type = "log" if scale_state.get() else "linear"
                        fig.update_layout(
                            plot_bgcolor='rgba(0,0,0,0)',
                            paper_bgcolor='rgba(0,0,0,0)',
                            font_color='white',
                            xaxis_tickangle=45,
                            yaxis_type=yaxis_type,
                            legend_title_text="Injury Status ",
                        )

                        return fig
                    
            with ui.layout_column_wrap(fill=True):
                with ui.card(full_screen=True):
                    ui.card_header("Relation between position and injury")

                    @render.ui
                    def toggle_position_scale_ui():

                        current_scale = position_scale_state.get()

                        if current_scale:
                            label = "Switch to Linear Scale"
                        else:
                            label = "Switch to Logarithmic Scale"


                        return ui.input_action_button(
                            "toggle_position_scale",
                            label,
                            width="250px",
                        )

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
                        relationship_counts = relationship_counts[
                            ~relationship_counts["POSITION_IN_VEHICLE"].isin(
                                ["Does Not Apply"]
                            )
                        ]
                        relationship_counts["POSITION_IN_VEHICLE"] = (
                            relationship_counts["POSITION_IN_VEHICLE"].map(
                                all_positions_unique
                            )
                        )

                        injury_colors = {
                            "Injured": "orange",
                            "Unspecified": "yellow",
                            "Killed": "red"
                        }

                        fig = px.bar(
                            relationship_counts,
                            x="POSITION_IN_VEHICLE",
                            y="Count",
                            color="PERSON_INJURY",
                            title=f"Relationship Between Position and Injury Status",
                            color_discrete_map=injury_colors,
                            labels={
                                "POSITION_IN_VEHICLE": "Position in Vehicle",
                                "PERSON_INJURY": "Injury Status",
                                "Count": "Number of Incidents",
                            },
                            template="plotly_white",
                            hover_data=["PERSON_INJURY"],
                        )

                        yaxis_type = "log" if position_scale_state.get() else "linear"

                        fig.update_layout(
                            plot_bgcolor='rgba(0,0,0,0)',
                            paper_bgcolor='rgba(0,0,0,0)',
                            font_color='white',
                            xaxis_tickangle=45,
                            
                            legend_title_text="Injury Status",
                            yaxis_type=yaxis_type,
                        )

                        return fig

    with ui.nav_panel("AI"):

        with ui.layout_column_wrap(fill=False):

            # CHART 1: SANKEY (Improved Labels & Flow Colors)
            with ui.card(full_screen=True):
                ui.card_header("AI Analysis: Pedestrian Risk Flow")

                @render_plotly
                def pedestrian_sankey():
                    # 1. Data Prep
                    df_ped = df[df["PERSON_TYPE"] == "Pedestrian"].copy()
                    cols = ["PED_LOCATION", "PED_ACTION", "PERSON_INJURY"]
                    for c in cols:
                        df_ped = df_ped[
                            ~df_ped[c].isin(
                                ["Unknown", "Does Not Apply", "nan", "Unspecified"]
                            )
                        ]
                        df_ped = df_ped.dropna(subset=[c])

                    # 2. Shorten Labels (Crucial for cleaner visuals)
                    df_ped["PED_LOCATION"] = df_ped["PED_LOCATION"].replace(
                        {
                            "Pedestrian/Bicyclist/Other Pedestrian at Intersection": "Intersection",
                            "Pedestrian/Bicyclist/Other Pedestrian Not at Intersection": "Not at Intersection",
                        }
                    )

                    # 3. Add Suffixes
                    df_ped["L"] = df_ped["PED_LOCATION"]
                    df_ped["A"] = df_ped["PED_ACTION"] + " (Act)"
                    df_ped["R"] = df_ped["PERSON_INJURY"]

                    # 4. Create Flows
                    flow1 = df_ped.groupby(["L", "A"]).size().reset_index(name="value")
                    flow1.columns = ["source", "target", "value"]

                    flow2 = df_ped.groupby(["A", "R"]).size().reset_index(name="value")
                    flow2.columns = ["source", "target", "value"]

                    links = pd.concat([flow1, flow2], axis=0)

                    # 5. Map Nodes
                    unique_nodes = list(
                        pd.unique(links[["source", "target"]].values.ravel("K"))
                    )
                    node_map = {name: i for i, name in enumerate(unique_nodes)}

                    links["source_id"] = links["source"].map(node_map)
                    links["target_id"] = links["target"].map(node_map)

                    # 6. Colors: Cool Blues for Context, Hot Colors for Danger
                    node_colors_map = {}
                    for node in unique_nodes:
                        if "Killed" in node:
                            color = "#FF0055"  # Neon Red
                        elif "Injured" in node:
                            color = "#FF9900"  # Neon Orange
                        elif "Intersection" in node:
                            color = "#00D4FF"  # Cyan
                        elif "(Act)" in node:
                            color = "#9D00FF"  # Electric Purple
                        else:
                            color = "#666666"
                        node_colors_map[node] = color

                    node_colors_list = [node_colors_map[n] for n in unique_nodes]

                    # 7. Link Gradients
                    link_colors = []
                    for index, row in links.iterrows():
                        # If the target is "Killed", make the link RED regardless of source
                        if "Killed" in row["target"]:
                            link_colors.append("rgba(255, 0, 85, 0.8)")  # Solid Red
                        elif "Injured" in row["target"]:
                            link_colors.append(
                                "rgba(255, 153, 0, 0.4)"
                            )  # Semi-transparent Orange
                        else:
                            link_colors.append("rgba(100, 100, 255, 0.2)")  # Faint Blue

                    fig = go.Figure(
                        data=[
                            go.Sankey(
                                node=dict(
                                    pad=20,
                                    thickness=15,
                                    line=dict(color="black", width=0.5),
                                    label=[
                                        n.replace(" (Act)", "") for n in unique_nodes
                                    ],
                                    color=node_colors_list,
                                ),
                                link=dict(
                                    source=links["source_id"],
                                    target=links["target_id"],
                                    value=links["value"],
                                    color=link_colors,
                                ),
                            )
                        ]
                    )

                    fig.update_layout(
                        title_text="Pedestrian Incident Flow",
                        font_size=12,
                        height=600,
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)",
                        font_color="white",
                        margin=dict(l=10, r=10, t=40, b=10),
                    )
                    return fig

            # CHART 2: PARALLEL CATEGORIES (Ghost vs Neon Edition)
            with ui.card(full_screen=True):
                ui.card_header("AI Analysis: Fatal Accident Pathways")

                @render_plotly
                def parallel_categories_plot():
                    cols = [
                        "PERSON_SEX",
                        "PERSON_TYPE",
                        "SAFETY_EQUIPMENT",
                        "PERSON_INJURY",
                    ]
                    df_cat = df[cols].copy().dropna()

                    for c in cols:
                        df_cat = df_cat[
                            ~df_cat[c].isin(
                                [
                                    "Unknown",
                                    "Does Not Apply",
                                    "nan",
                                    "Unspecified",
                                    "U",
                                    "-",
                                ]
                            )
                        ]

                    df_cat = df_cat[df_cat["PERSON_INJURY"].isin(["Injured", "Killed"])]

                    def clean_equip(x):
                        if "Lap Belt" in x or "Harness" in x:
                            return "Seatbelt"
                        if "Air Bag" in x:
                            return "Airbag"
                        if "Helmet" in x:
                            return "Helmet"
                        if "None" in x:
                            return "None"
                        return "Other"

                    df_cat["SAFETY_EQUIPMENT"] = df_cat["SAFETY_EQUIPMENT"].apply(
                        clean_equip
                    )

                    # --- THE TRICK: Custom Color Scale ---
                    # Map Injured -> 0, Killed -> 1
                    injury_map = {"Injured": 0, "Killed": 1}
                    df_cat["INJURY_CODE"] = df_cat["PERSON_INJURY"].map(injury_map)

                    # Sort: Important! We want Killed (1) to be plotted LAST so they appear ON TOP
                    df_cat = df_cat.sort_values("INJURY_CODE")

                    fig = px.parallel_categories(
                        df_cat,
                        dimensions=[
                            "PERSON_TYPE",
                            "PERSON_SEX",
                            "SAFETY_EQUIPMENT",
                            "PERSON_INJURY",
                        ],
                        color="INJURY_CODE",
                        # Ghost Mode: 0 is faint blue-grey, 1 is bright neon red
                        color_continuous_scale=[
                            (
                                0.00,
                                "rgba(100, 149, 237, 0.2)",
                            ),  # Ghostly Cornflower Blue
                            (1.00, "rgba(255, 0, 0, 1.0)"),  # Solid Neon Red
                        ],
                        labels={
                            "PERSON_TYPE": "Role",
                            "PERSON_SEX": "Sex",
                            "SAFETY_EQUIPMENT": "Safety",
                            "PERSON_INJURY": "Outcome",
                        },
                        height=600,
                    )

                    fig.update_layout(
                        margin=dict(l=20, r=20, t=40, b=20),
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)",
                        font_color="white",
                        coloraxis_showscale=False,
                    )

                    return fig

    with ui.nav_panel("About"):
        with ui.card(full_screen=True):
            ui.card_header("About")

            ui.h3("Purpose")
            ui.p("This application provides interactive visualizations and analysis of vehicular crash incidents across New York City.")
            ui.p("Its goal is to help users explore accident patterns, contributing factors, and trends over time.")
            
            ui.br()

            ui.h3("Data Source")
            ui.p("The analysis is based on a dataset of motor vehicle collisons in New York City",)
    
            ui.p(
                "This data is compiled by the New York City Police Department (NYPD) and is publicly available through ",
                ui.a(
                     "NYC OpenData",
                     href="https://data.cityofnewyork.us/Public-Safety/Motor-Vehicle-Collisions-Person/f55k-p6yu/about_data",
                     target="_blank"
                 ),
                 "."
            )

            ui.br()
            
            ui.h3("Technical Details")
            ui.p("Developed using Shiny for Python and various data science libraries.")
            ui.p("Data is current as of December 8th 2025.")

ui.include_css(app_dir / "styles.css")



@reactive.calc
def year_df():
    return day_grouped[day_grouped["YEAR"] == input.year()]

@reactive.calc
def filtered_year_data():
    """Filters the main dataframe based on the selected year."""
    selected_year = int(input.year())
    return df[df["YEAR"] == selected_year].copy()

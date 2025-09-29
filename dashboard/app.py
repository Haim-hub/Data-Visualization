import seaborn as sns
import re
from faicons import icon_svg

# Import data from shared.py
from shared import app_dir, df, pen_df

from shiny import reactive
from shiny.express import input, render, ui
import matplotlib.ticker as ticker

ui.page_opts(title="Tech Salaries dashboard", fillable=True)



#with ui.sidebar(title="Filter controls"):
#    ui.input_slider("mass", "Mass", 2000, 6000, 6000)
#    ui.input_checkbox_group(
#        "species",
#        "Species",
#        ["Adelie", "Gentoo", "Chinstrap"],
#        selected=["Adelie", "Gentoo", "Chinstrap"],
#    )


with ui.layout_column_wrap(fill=False):
    with ui.value_box(showcase=icon_svg("users-line")):
        "Number of people"

        @render.text
        def count():
            return filtered_df().shape[0]

    with ui.value_box(showcase=icon_svg("business-time")):
        "Average Total Experience Years"

        @render.text
        def bill_length():
            return f"{filtered_df()['total_experience_years'].mean():.1f} years"

    with ui.value_box(showcase=icon_svg("money-bill")):
        "Average Annual Base Pay"

        @render.text
        def bill_depth():
            return f"{filtered_df()['annual_base_pay'].mean():.1f} $"


with ui.layout_columns():
    with ui.card(full_screen=True):
        ui.card_header("Experience and Anual Base Pay")

        @render.plot
        def length_depth():
            ax = sns.scatterplot(
                data=filtered_df(),
                x="total_experience_years",
                y="annual_base_pay",
                hue="job_title_category",
            )
            # Force decimal notation
            ax.yaxis.set_major_formatter(ticker.ScalarFormatter(useOffset=False))
            ax.ticklabel_format(style='plain', axis='y')
            return ax

    with ui.card(full_screen=True):
        ui.card_header("Tech Salary data")

        @render.data_frame
        def summary_statistics():
            cols = [
                "job_title",
                "job_title_category",
                "total_experience_years",
                "annual_base_pay",
            ]
            return render.DataGrid(filtered_df()[cols], filters=True)


ui.include_css(app_dir / "styles.css")


@reactive.calc
def filtered_pen_df():
    filt_df = pen_df[pen_df["species"].isin(input.species())]
    filt_df = filt_df.loc[filt_df["body_mass_g"] < input.mass()]
    return filt_df

def is_valid_job_title(name):
    # Check for excessive special characters or numbers
    if re.search(r'[!@#$%^&*()_+=\[\]{};:\'"\\|,.<>\/?0-9ÛÜûüæøåÆØÅ]{3,}', name):
        return False
    # Check for unreasonable length
    if len(name) < 3 or len(name) > 100:
        return False
    if name in ["nigger in cheif", "asdf", "_à¾á±á´¬ÜüÇ", "tom", "twat master", "muffin stuffer", "chief lubricator", "sveeeeeeeeetrs peeeeeeeeetrs", "buch", "job title"]:
        return False
    return True

@reactive.calc
def filtered_df():
    filt_df = df[df['job_title'].apply(is_valid_job_title)]
    filt_df = filt_df[filt_df["annual_base_pay"] < 1000000]
    return filt_df
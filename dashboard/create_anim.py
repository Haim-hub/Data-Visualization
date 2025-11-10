import matplotlib.pyplot as plt
import matplotlib.animation as animation
import matplotlib.dates as mdates
from matplotlib.ticker import MaxNLocator
import pandas as pd
import os
from shared import app_dir, df

def generate_and_save_animation(df, output_path="static/crashes_animation.gif"):
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Prepare data: Group by minute and sort
    df["CRASH_TIME"] = pd.to_datetime(df["CRASH_TIME"], format="%H:%M")
    df["CRASH_HOUR_MINUTE"] = df["CRASH_TIME"].dt.strftime("%H:%M")
    grouped = df.groupby("CRASH_HOUR_MINUTE").size().reset_index(name="count")
    grouped = grouped.sort_values("CRASH_HOUR_MINUTE")

    # Convert times to datetime for plotting
    times = pd.to_datetime(grouped["CRASH_HOUR_MINUTE"], format="%H:%M")
    counts = grouped["count"]

    # Create the figure and axis
    fig, ax = plt.subplots(figsize=(15, 6), dpi=55)
    ax.set_facecolor("#2d2d2d")
    fig.set_facecolor("#2d2d2d")

    # Set x-axis to show time with hourly ticks
    ax.xaxis.set_major_locator(mdates.HourLocator(interval=1))  # Tick every hour
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))  # Format as HH:MM

    # Rotate x-axis labels for readability
    plt.xticks(rotation=45)

    # Initialize the line plot
    line, = ax.plot([], [], color="skyblue", lw=2)

    # Set labels and title
    ax.set_xlabel("Time of Day", color="white")
    ax.set_ylabel("Number of Crashes", color="white")
    ax.set_title("Crashes per Minute (Animated)", color="white")
    ax.tick_params(colors="white")

    # Set x and y limits
    ax.set_xlim(times.min(), times.max())
    ax.set_ylim(0, max(counts) * 1.1)  # Add 10% padding

    # Animation function
    def animate(i):
        line.set_data(times[:i+1], counts[:i+1])
        return line,

    # Create the animation
    anim = animation.FuncAnimation(
        fig,
        animate,
        frames=len(times),
        interval=50,  # Controls speed (milliseconds)
        blit=True,     # Optimize animation
        repeat=True,
    )

    # Save the animation as a GIF
    anim.save(output_path, writer="pillow", fps=40)
    plt.close(fig)

generate_and_save_animation(df)
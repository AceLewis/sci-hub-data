import csv
import os
from datetime import datetime
from itertools import accumulate
from typing import List, Union

import matplotlib.pyplot as plt  # type: ignore

plt.style.use("seaborn-whitegrid")  # This makes it look a bit nicer.


def filter_torrent_infos_one_step(torrent_infos: List[List[int]]) -> List[List[int]]:
    """Does one step of the filtering."""
    torrent_infos_filtered = []

    for current_torrent, next_torrent in zip(torrent_infos, torrent_infos[1:]):
        # Look one day ahead to see if a torrent has been created, if so cobine them.
        if current_torrent[0] > next_torrent[0] - 3600 * 24:
            next_torrent[1] += current_torrent[1]
            next_torrent[2] += current_torrent[2]
        else:
            torrent_infos_filtered.append(current_torrent)
    torrent_infos_filtered.append(torrent_infos[-1])
    return torrent_infos_filtered


def filter_torrent_infos(torrent_infos: List[List[int]]) -> List[List[int]]:
    """
    Torrents are made on Saturday and batched into groups of 100,000. If over 200,000 articles are
    being processed we want to combine this information as it is possible for torrents of ealier
    files to be made later.
    """
    while True:
        new_torrent_infos = filter_torrent_infos_one_step(torrent_infos)
        if new_torrent_infos != torrent_infos:
            torrent_infos = new_torrent_infos
        else:
            return torrent_infos


def make_plot(
    x: List[datetime],
    y: List[Union[int, float]],
    title: str,
    ylabel: str,
    plot_name: str,
    cut_off_time: int,
) -> None:
    """Make the plot"""
    fig, ax = plt.subplots(figsize=(8, 8))
    ax.plot(x, y, linewidth=3)

    # We made the plot, now label it and try to make it look better.
    fontdict = {"fontsize": 20, "fontweight": "bold", "color": "gray"}
    plt.ylabel(ylabel, fontdict=fontdict)

    fontdict = {"fontsize": 25, "fontweight": "bold", "color": "gray"}
    plt.title(title, fontdict=fontdict, y=1.03)

    # Change label axis weight and colour
    ax.xaxis.label.set_color("grey")
    ax.xaxis.label.set_weight("bold")
    ax.yaxis.label.set_color("grey")
    ax.yaxis.label.set_weight("bold")

    # Change splines, splines are the lines on the graph
    ax.spines["right"].set_visible(False)
    ax.spines["top"].set_visible(False)
    ax.spines["left"].set_color("grey")
    ax.spines["left"].set_linewidth(1.5)
    ax.spines["bottom"].set_color("grey")
    ax.spines["bottom"].set_linewidth(1.5)

    # Increase tick font size and colour
    ax.yaxis.set_tick_params(labelsize=20, colors="grey")
    ax.xaxis.set_tick_params(labelsize=20, colors="grey")

    # Set xlim start to the start date
    ax.set_xlim((datetime.fromtimestamp(cut_off_time)))

    plt.autoscale(enable=True, axis="y", tight=True)
    plt.tight_layout(rect=[0.01, 0.01, 0.95, 0.99])

    # Put some text in the bottom left.
    fontdict = {"fontsize": 10, "fontweight": "bold", "color": "gray"}
    fig.text(
        0.01,
        0.005,
        "Source: http://libgen.rs/scimag/repository_torrent/ - AceLewis.com",
        fontdict=fontdict,
        horizontalalignment="left",
    )

    # Save and close figure.
    os.makedirs("./images/", exist_ok=True)
    fig.savefig(f"./images/{plot_name}.png", dpi=300)
    fig.savefig(f"./images/{plot_name}.svg", dpi=300)
    plt.close()


def main():
    """Main function"""
    # Start in 2015 because before then Sci-Hub/LibGen didn't put the articles in torrents. At the
    # end of 2014 all articles were made into torrents so the creation dates of torrents before 2015
    # is not useful.
    cut_off_time = int(datetime(2015, 1, 1).timestamp())

    with open("torrent_info.csv", "r") as csvfile:
        reader = tuple(csv.reader(csvfile, skipinitialspace=True))
        # We need to calcualte the sum of the articles and file size before the cutoff.
        _, number_of_articles_before, total_bytes_before = (
            sum(map(int, y)) for y in zip(*(x for x in reader if int(x[0]) <= cut_off_time))
        )
        after_cutoff = list(list(map(int, x)) for x in reader if int(x[0]) > cut_off_time)

    # Filter torrents that were made in a batch jobs together
    after_cutoff = filter_torrent_infos(after_cutoff)

    # Unpack the torrent infos to lists.
    creation_dates_str, numbers_of_articles_str, sizes_in_bytes_str = zip(
        *(x for x in after_cutoff if int(x[0]) > cut_off_time)
    )
    # Convert strings to integers
    creation_dates_unix = [int(x) for x in creation_dates_str]
    numbers_of_articles = [int(x) for x in numbers_of_articles_str]
    sizes_in_bytes = [int(x) for x in sizes_in_bytes_str]

    # Cumulative sum the data for the y-axis and add the sum for before the cutoff.
    number_of_articles_cumsum = [
        x + number_of_articles_before for x in accumulate(numbers_of_articles)
    ]
    sizes_in_bytes_cumsum = [x + total_bytes_before for x in accumulate(sizes_in_bytes)]
    # Convert unix timestamp into datetime objects.
    creation_dates = [datetime.fromtimestamp(x) for x in creation_dates_unix]
    # Divide by a million else the numbers would be too large.
    number_of_articles_cumsum_in_million = [x / 1e6 for x in number_of_articles_cumsum]
    # Convert bytes into terabytes.
    terabyte = 1024 ** 4
    size_in_terabytes_cumsum = [x / terabyte for x in sizes_in_bytes_cumsum]

    # Make plots for the number of articles and total file size.
    title = "Number of Articles on Sci-Hub"
    ylabel = "Number in Millions"
    make_plot(
        creation_dates,
        number_of_articles_cumsum_in_million,
        title,
        ylabel,
        "number_of_articles",
        cut_off_time,
    )

    title = "Total File Size of Articles on Sci-Hub"
    ylabel = "Total File Size in Terabytes"
    make_plot(creation_dates, size_in_terabytes_cumsum, title, ylabel, "file_size", cut_off_time)


if __name__ == "__main__":
    main()

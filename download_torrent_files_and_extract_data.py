import csv
import glob
import os
import re
from dataclasses import dataclass
from typing import List, Set

import requests
import torrent_parser as tp  # type: ignore
from bs4 import BeautifulSoup  # type: ignore
from tqdm import tqdm  # type: ignore


@dataclass
class TorrentInfo:
    """Information about a torrent."""

    creation_date: int  # Unix time stamp
    number_of_articles: int
    size_in_bytes: int

    def __iter__(self):
        return iter([self.creation_date, self.number_of_articles, self.size_in_bytes])


TORRENT_DIRECTORY = "./torrents/"
SCI_HUB_TORRENT_URL = "http://libgen.rs/scimag/repository_torrent/"


def get_torrent_names() -> Set[str]:
    """Get the name of the torrents from Library Genesis/Sci-Hub."""
    html = requests.get(SCI_HUB_TORRENT_URL).text
    soup = BeautifulSoup(html, "html.parser")
    all_links = soup.find_all("a", {"href": re.compile(r".*\.torrent")})
    return {x.get("href") for x in all_links}


def get_torrents_on_disk() -> Set[str]:
    """Get all torrents that have been previously saved on disk."""
    os.makedirs(TORRENT_DIRECTORY, exist_ok=True)
    return {x.split("\\")[-1] for x in glob.glob(TORRENT_DIRECTORY + "*.torrent")}


def get_torrents_to_download() -> List[str]:
    """Get all torrents to download."""
    return list(get_torrent_names() - get_torrents_on_disk())


def download_torrent(torrent_link: str) -> None:
    """Download a single torrent file."""
    torrent = requests.get(SCI_HUB_TORRENT_URL + torrent_link)

    with open(TORRENT_DIRECTORY + torrent_link, "wb") as file:
        file.write(torrent.content)


def download_torrents() -> None:
    """Download all torrent files that are not already saved to the disk."""
    torrent_links = get_torrents_to_download()
    if torrent_links:
        for torrent_link in tqdm(torrent_links, desc="Downloading torrent files"):
            download_torrent(torrent_link)


def get_torrent_info(torrent_name: str) -> TorrentInfo:
    """
    Get the information about the torrent. This returns a TorrentInfo with the unix timestamp of
    when the torrent was created, the number of articles in the torrent and the file size in bytes.
    """
    # All files have 100,000 torrents but we calculate it anyway incase it changes in the future.
    regex_match = re.match(r"sm_([0-9]*)-([0-9]*)\.torrent", torrent_name)
    assert regex_match is not None  # For type checking
    article_start, article_end = map(int, regex_match.groups())

    number_of_articles = article_end - article_start + 1
    # Read torrent file to get the rest of the data
    torrent_data = tp.parse_torrent_file(TORRENT_DIRECTORY + torrent_name)

    creation_date = torrent_data["creation date"]
    size_in_bytes = torrent_data["info"]["piece length"] * len(torrent_data["info"]["pieces"])
    return TorrentInfo(creation_date, number_of_articles, size_in_bytes)


def get_all_torrent_info() -> List[TorrentInfo]:
    """
    Get information for all torrents on the disk, sort by the torrent name so the return is in
    order of lower article numbers first.
    """
    return [get_torrent_info(torrent_name) for torrent_name in sorted(get_torrents_on_disk())]


def get_torrents_info_and_save_to_csv() -> None:
    """Get all torrent info and save it to a csv file."""
    all_torrent_info = get_all_torrent_info()

    with open("torrent_info.csv", "w", newline="") as file:
        writer = csv.writer(file, delimiter=",")
        writer.writerows(all_torrent_info)


if __name__ == "__main__":
    # Download all torrents from Sci-Hub/Library Genesis
    download_torrents()
    # Get info for every torrent
    get_torrents_info_and_save_to_csv()

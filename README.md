# sci-hub-data
A python project to download and process information from Sci-Hub torrents and make graphs.

## What is Sci-Hub
Sci-Hub is a website that allows free public access to scientific papers that are usually behind paywalls thus removing barriers in the way of science.

## Data
The data is extracted from torrent files from http://libgen.rs/scimag/repository_torrent/ .
Sci-Hub and Library Genesis share the same article database.

## Graphs
[![Number of articles vs time]("Number of articles vs time")](./images/number_of_articles.png "Number of articles vs time")
[![Total size size vs time]("Total size size vs time")](./images/file_size.png "Total size size vs time")

## How to download the torrent files and make the graphs
First run:

`python download_torrent_files_and_extract_data.py`

To download the torrents then extract the data to `'torrent_info.csv'`.

Then run:

`python data_visualisation.py`

The graphs will be saved in `./images/`.

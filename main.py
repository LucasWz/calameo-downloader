import logging
from pathlib import Path
from typing import Dict, List

import requests

from packages.pdf import merge_img_to_pdf, merge_svg_to_pdf
from packages.scraper import (
    dowload_page,
    get_book_description,
    get_firstpage_link,
    get_response,
    get_soup,
)
from packages.utils import clean_title, load_yaml_config, remove_tree

logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)


def download_calameo_pdf(path: str, session: requests.Session) -> Path:
    global logger
    # Parse website HTML
    response = get_response(session, path)
    soup = get_soup(response)

    # Retrieve book infos
    book_link = get_firstpage_link(soup)
    description = get_book_description(soup)

    # Create convient folder to store data
    main_dir = Path(clean_title(description.get("title")))
    temp_dir = main_dir.joinpath(".temp")
    temp_dir.mkdir(parents=True, exist_ok=True)
    out_pdf = main_dir.joinpath(f"{main_dir}.pdf")

    # Choose to parse as SVG or JPG
    # SVG format is slower but cleaner and allow copy-paste.
    suffix, merger = (
        (".svgz", merge_svg_to_pdf) if SVG_QUALITY else (".jpg", merge_img_to_pdf)
    )

    # Download each page from calameo
    temp_files = []
    for i in range(1, int(description.get("page")) + 1):
        path = f"{book_link}/p{i}{suffix}"
        fname = temp_dir.joinpath(f"output_{i}{suffix}")
        temp_files.append(fname)
        response = get_response(session, path)
        dowload_page(response, fname)

    # Merge pdf and remove temporary files
    merger(temp_files, out_pdf)
    remove_tree(temp_dir)

    return out_pdf


if __name__ == "__main__":

    config = load_yaml_config("config.yml")
    BOOK_LIST: List[str] = config.get("book_list")
    SVG_QUALITY: bool = config.get("svg_quality")
    HEADERS: Dict[str, str] = config.get("headers")

    with requests.Session() as session:
        for book in BOOK_LIST:
            pdf = download_calameo_pdf(book, session)
            logger.info(f"Successfuly load PDF from calaméo:'{pdf}'")

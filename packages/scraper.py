import logging
import re
from typing import Dict

import requests
from bs4 import BeautifulSoup as bs

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class PageNotFound(requests.exceptions.HTTPError):
    pass


Response = requests.models.Response


def get_response(
    session: requests.Session,
    path: str,
) -> Response:
    response = session.get(path)
    if not response.ok:
        if response.status_code == 404:
            raise PageNotFound(path)
        else:
            response.raise_for_status()
    return response


def get_soup(response: Response) -> bs:
    return bs(response.text, features="lxml")


def get_firstpage_link(soup: bs) -> str:
    return (
        soup.head.find("meta", attrs={"property": "og:image"})
        .get("content")
        .rsplit("/", 1)[0]
    )


def get_book_description(soup: bs) -> str:
    PATTERN = r"(?:Title\s?:\s?)(?P<title>.*)(?:,\s?Author\s?:\s?)(?P<author>.*)(?:,\s?Length\s?:\s?)(?P<page>.*)(?:\spages\s?,\s?Published\s?:\s?)(?P<publication_date>\d{4}-\d{2}-\d{2})"

    description = soup.head.find("meta", attrs={"name": "description"})["content"]
    match = re.search(PATTERN, description)
    if match is not None:
        return match.groupdict()
    else:
        logger.warning(f"Description not found for '{description}'.")


def dowload_page(response: Response, fname: str) -> None:
    with open(fname, "wb") as f:
        f.write(response.content)

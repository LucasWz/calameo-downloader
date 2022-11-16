import logging
import re
import shutil
from pathlib import Path
from typing import Dict, List, Union

import cairosvg
import requests
import yaml
from bs4 import BeautifulSoup as bs
from fpdf import FPDF
from PIL import Image
from PyPDF2 import PdfFileMerger
from yaml.loader import SafeLoader

logging.basicConfig(level=logging.INFO)

class PageNotFound(requests.exceptions.HTTPError):
    pass

Response = requests.models.Response


def load_yaml_config(path: str = "test.yml") -> dict:

    with open(path, mode="r", encoding="utf-8") as f:
        data = yaml.load(f, Loader=SafeLoader)

    return data


def get_response(
    session: requests.Session, path: str, headers: Dict[str, str]
) -> Response:
    response = session.get(path, headers=headers)
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
        logging.warning(f"Description not found for '{description}'.")


def dowload_page(response: Response, fname: str) -> None:
    with open(fname, "wb") as f:
        f.write(response.content)


def clean_title(s: str) -> str:
    keepcharacters = ("-", "_")
    return "".join(c for c in s if c.isalnum() or c in keepcharacters).rstrip()


def svg_to_pdf(path) -> None:
    path = Path(path)
    pdf_path = path.rename(path.with_suffix(".pdf"))
    cairosvg.svg2pdf(url=path, write_to=pdf_path)
    return pdf_path


def merge_pdfs(pdf_list: List[Union[str, Path]], out_path: Union[str, Path]) -> None:
    merger = PdfFileMerger()
    for path in pdf_list:
        merger.append(path)
    merger.write(out_path)
    merger.close()


def merge_svg_to_pdf(
    svg_list: List[Union[str, Path]], out_path: Union[str, Path]
) -> None:

    pdf_list = [svg_to_pdf(path) for path in svg_list]
    merge_pdfs(pdf_list, out_path)


def remove_tree(path: Union[str, Path]) -> None:
    shutil.rmtree(path, ignore_errors=True)
    

def merge_img_to_pdf(
    img_list: List[Union[str, Path]], out_path: Union[str, Path]
) -> None:
    cover = Image.open(img_list[0])
    width, height = cover.size
    pdf = FPDF(unit="pt", format=[width, height])
    for img in img_list:
        pdf.add_page()
        pdf.image(img, 0, 0)
    pdf.output(out_path)
    
    
def download_calameo_pdf(path:str, session:requests.Session) -> Path:
    # Parse website HTML
    response = get_response(session, BOOK_LIST[i], HEADERS)
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
    for i in range(1, int(description.get("page"))):
        path = f"{book_link}/p{i}{suffix}"
        fname = temp_dir.joinpath(f"output_{i}{suffix}")
        temp_files.join(fname)
        response = get_response(session, path, HEADERS)
        dowload_page(response, fname)
        
    # Merge pdf and remove temporary files
    merger(temp_files, out_pdf)
    remove_tree(temp_dir)


if __name__ == "__main__":
    
    config = load_yaml_config("config.yml")
    BOOK_LIST: List[str] = config.get("book_list")
    SVG_QUALITY: bool = config.get("svg_quality")
    HEADERS: Dict[str, str] = config.get("headers")

    with requests.Session() as session:
        for book in BOOK_LIST:
            path = download_calameo_pdf(book, session)
            logging.info()




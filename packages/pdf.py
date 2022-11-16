import logging
from typing import List, Union
from pathlib import Path
import cairosvg
from fpdf import FPDF
from PIL import Image
from PyPDF2 import PdfFileMerger

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

def svg_to_pdf(path) -> None:
    path = Path(path)
    pdf_path = path.with_suffix(".pdf")
    cairosvg.svg2pdf(url=str(path), write_to=str(pdf_path))
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


def merge_img_to_pdf(
    img_list: List[Union[str, Path]], out_path: Union[str, Path]
) -> None:
    cover = Image.open(img_list[0])
    width, height = cover.size
    pdf = FPDF(unit="pt", format=[width, height])
    for img in img_list:
        pdf.add_page()
        pdf.image(str(img), 0, 0)
    pdf.output(out_path)
    
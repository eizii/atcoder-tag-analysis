from collect_statements import ROOT
import fitz
with fitz.open(ROOT/"cache/abc001_editorial.pdf") as doc:
    doc[doc.page_count-1].get_pixmap(matrix=fitz.Matrix(1.25,1.25)).save(ROOT/"pdf_extraction_sample.png")
print("Rendered representative PDF page")

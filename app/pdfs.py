# -*- coding: utf-8 -*-
from xhtml2pdf import pisa
from io import BytesIO

def create_pdf(pdf_data):
    pdf = BytesIO()
    pisa.CreatePDF(BytesIO(pdf_data), pdf)

    return pdf

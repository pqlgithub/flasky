# -*- coding: utf-8 -*-
from xhtml2pdf import pisa
from io import BytesIO

def create_pdf(pdf_data):
    pdf = BytesIO()
    pisa.CreatePDF(pdf_data, pdf)
    resp = pdf.getvalue()
    pdf.close()

    return resp

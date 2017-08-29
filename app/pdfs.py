# -*- coding: utf-8 -*-
from xhtml2pdf import pisa
from io import BytesIO, StringIO
import mimerender

mimerender.register_mime('pdf', ('application/pdf',))
mimerender = mimerender.FlaskMimeRender(global_charset='UTF-8')

def render_pdf(html):
    pdf = StringIO()
    pisa.CreatePDF(StringIO(html.encode('utf-8')), pdf)
    resp = pdf.getvalue()
    pdf.close()

    return resp


def create_pdf(pdf_data):
    pdf = BytesIO()
    pisa.CreatePDF(BytesIO(pdf_data), pdf)

    return pdf

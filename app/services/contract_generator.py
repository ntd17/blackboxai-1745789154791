import logging
from weasyprint import HTML, CSS
from pdfminer.high_level import extract_pages
from pdfminer.layout import LAParams
from flask import current_app
from .exceptions import PDFGenerationError, LLMUnavailableError

logger = logging.getLogger(__name__)

def validate_pdf_format(pdf_path):
    """Validate PDF meets legal document requirements"""
    required_margins = {
        'left': 72,   # 1 inch
        'right': 72,
        'top': 72,
        'bottom': 72
    }
    required_fonts = ['Helvetica', 'Times-Roman']
    min_font_size = 11

    try:
        for page_layout in extract_pages(pdf_path, laparams=LAParams()):
            # Validate page size (A4: 595.44 x 841.68 points)
            if not (590 < page_layout.width < 600 and 840 < page_layout.height < 842):
                raise ValueError(f"Invalid page size: {page_layout.width}x{page_layout.height} - Must be A4 format")

            # Check margins and content positioning
            for element in page_layout:
                if hasattr(element, 'bbox'):
                    x0, y0, x1, y1 = element.bbox
                    if x0 < required_margins['left']:
                        raise ValueError(f"Left margin violation: {x0}pt < {required_margins['left']}pt")
                    if x1 > (page_layout.width - required_margins['right']):
                        raise ValueError(f"Right margin violation: {x1}pt > {page_layout.width - required_margins['right']}pt")

                # Font validation
                if hasattr(element, 'text'):
                    for font in element.font:
                        if font.fontname not in required_fonts:
                            raise ValueError(f"Invalid font: {font.fontname}. Allowed: {', '.join(required_fonts)}")
                        if element.size < min_font_size:
                            raise ValueError(f"Font size {element.size}pt below minimum {min_font_size}pt")

        return True
    except Exception as e:
        current_app.logger.error(f"PDF validation failed: {str(e)}")
        raise PDFGenerationError(str(e))

def generate_pdf(html_content, output_path, lang='pt-br'):
    """Generate legally compliant PDF contract with validation"""
    try:
        # Generate PDF with proper page setup
        html = HTML(string=html_content)
        pdf = html.write_pdf(
            stylesheets=[CSS(string='''
                @page {
                    size: A4;
                    margin: 1in;
                    @top-left { content: "Confidential Contract Document"; }
                    @bottom-right { content: "Page " counter(page); }
                }
                body { font-family: Helvetica; font-size: 12pt; }
            ''')],
            presentational_hints=True
        )

        # Write to file
        with open(output_path, 'wb') as f:
            f.write(pdf)

        # Validate format
        validate_pdf_format(output_path)

        return output_path

    except LLMUnavailableError:
        logger.warning("LLM service unavailable, using default clauses")
        return generate_pdf(
            html_content.replace('{{ llm_clauses }}', '{{ default_clauses }}'),
            output_path,
            lang
        )
    except Exception as e:
        logger.error(f"PDF generation failed: {str(e)}")
        raise PDFGenerationError(f"Failed to generate contract PDF: {str(e)}")

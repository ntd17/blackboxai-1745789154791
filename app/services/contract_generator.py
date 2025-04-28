from datetime import datetime
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from app.services.pdf_generator import generate_pdf
from app.utils.logger import logger
from app.utils.llm_integration import generate_contract_clause

class ContractGenerator:
    def __init__(self):
        self.template_env = Environment(
            loader=FileSystemLoader(str(Path(__file__).parent.parent / 'templates/contracts')),
            autoescape=True
        )

    def generate_painting_contract(self, contract_data: dict) -> str:
        """Generate a painting service contract PDF from template and data"""
        try:
            # Validate required fields
            required_fields = ['contractor_name', 'client_name', 'total_price']
            if not all(field in contract_data for field in required_fields):
                raise ValueError("Missing required contract fields")

            # Generate dynamic clauses using LLM
            contract_data.setdefault('scope_of_work', 
                generate_contract_clause("scope_of_work", contract_data))
            
            contract_data.setdefault('warranties_liabilities',
                generate_contract_clause("warranties_liabilities", contract_data))

            # Set default dates
            contract_data.setdefault('contract_date', datetime.now().strftime('%B %d, %Y'))
            contract_data.setdefault('start_date', 'TBD')
            contract_data.setdefault('completion_date', 'TBD')

            # Render template
            template = self.template_env.get_template('painting_contract.html')
            html_content = template.render(**contract_data)

            # Generate PDF with professional formatting
            pdf_path = generate_pdf(
                html_content,
                output_name=f"Painting_Contract_{contract_data['client_name'].replace(' ', '_')}.pdf",
                options={
                    'page-size': 'Letter',
                    'margin-top': '0.75in',
                    'margin-right': '0.75in',
                    'margin-bottom': '0.75in',
                    'margin-left': '0.75in',
                    'encoding': 'UTF-8'
                }
            )

            return pdf_path

        except Exception as e:
            logger.error(f"Contract generation failed: {str(e)}")
            raise

import os
import openai
from typing import Dict, Any
from app.utils.logger import logger
from app.utils.cache import cache

class LLMContractGenerator:
    def __init__(self):
        self.api_key = os.getenv('LLM_API_KEY')
        self.model = os.getenv('LLM_MODEL', 'gpt-4')
        self.temperature = float(os.getenv('LLM_TEMPERATURE', 0.5))
        
        # Configure OpenAI client
        openai.api_key = self.api_key
        
        # Predefined prompts for contract sections
        self.prompts = {
            'scope_of_work': (
                "Generate a professional scope of work section for a painting contract. "
                "Include details about surface preparation, number of coats, paint specifications, "
                "and cleanup procedures. Use formal legal language. "
                "Contractor: {contractor_name}, Client: {client_name}, "
                "Property Type: {property_type}, Surface Area: {surface_area}"
            ),
            'warranties_liabilities': (
                "Create comprehensive warranty and liability clauses for a painting contract. "
                "Include terms about workmanship warranty duration, material defects, "
                "limitation of liability, and dispute resolution. "
                "Contract Value: {total_price}, Project Duration: {project_duration}"
            )
        }

    @cache.memoize(timeout=3600)  # Cache for 1 hour
    def generate_clause(self, clause_type: str, context: Dict[str, Any]) -> str:
        """Generate a contract clause using LLM with context-aware prompts"""
        try:
            if clause_type not in self.prompts:
                raise ValueError(f"Unknown clause type: {clause_type}")

            prompt = self.prompts[clause_type].format(**context)
            
            response = openai.chat.completions.create(
                model=self.model,
                messages=[{
                    "role": "system",
                    "content": "You are a legal contract assistant. Generate formal, professional contract clauses."
                }, {
                    "role": "user",
                    "content": prompt
                }],
                temperature=self.temperature,
                max_tokens=500
            )

            generated_text = response.choices[0].message.content.strip()
            logger.info(f"Generated {clause_type} clause")
            return generated_text

        except Exception as e:
            logger.error(f"LLM clause generation failed: {str(e)}")
            raise

def generate_contract_clause(clause_type: str, context: Dict[str, Any]) -> str:
    generator = LLMContractGenerator()
    return generator.generate_clause(clause_type, context)

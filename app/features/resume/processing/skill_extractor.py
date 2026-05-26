# app/features/resume/processing/skill_extractor.py

import time
import logging

from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from app.shared.ai.llm.dependencies import get_llm_executor


logger = logging.getLogger(__name__)


def normalize_skills(skills):
    return list({
        s.strip().lower()
        for s in skills
        if isinstance(s, str) and 1 < len(s.strip()) < 50
    })


def build_chain(llm):

    prompt = PromptTemplate.from_template(
        """
You are a strict information extraction system.

Extract ONLY technical skills.

RULES:
- Output valid JSON
- No explanation
- Lowercase
- No duplicates

FORMAT:
{{"skills": ["python", "fastapi"]}}

TEXT:
{input}
"""
    )

    parser = JsonOutputParser()

    return prompt | llm | parser


def extract_skills(text: str):

    logger.info("Starting skill extraction")

    executor = get_llm_executor()

    try:
        # ✅ Use executor LLM
        chain = build_chain(executor.primary)
        response = executor.execute(chain, {"input": text})

    except Exception as e:
        logger.warning(f"Primary failed → fallback: {str(e)}")

        # ✅ fallback
        fallback_chain = build_chain(executor.fallback)
        response = fallback_chain.invoke({"input": text})

    skills = response.get("skills", [])

    if not isinstance(skills, list):
        raise ValueError("Invalid skills format")

    return normalize_skills(skills)

def safe_extract_skills(text: str):

    for attempt in range(3):
        try:
            start = time.time()

            skills = extract_skills(text)

            duration = round(time.time() - start, 2)

            logger.info(
                "skill_extraction_success",
                extra={
                    "attempt": attempt + 1,
                    "skills_count": len(skills),
                    "latency": duration,
                },
            )

            return skills

        except Exception as e:
            logger.warning(
                "skill_extraction_failed",
                extra={"attempt": attempt + 1, "error": str(e)},
            )

            time.sleep(1 * (attempt + 1))

    logger.error("skill_extraction_total_failure")

    return []
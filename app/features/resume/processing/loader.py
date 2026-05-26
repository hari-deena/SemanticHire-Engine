from langchain_community.document_loaders import PyPDFLoader
from typing import List
import logging

logger = logging.getLogger(__name__)


def load_document(path: str) -> List[str]:
    try:
        loader = PyPDFLoader(path)
        docs = loader.load()

        if not docs:
            logger.warning(f"No content found in file: {path}")
            return []

        # Return list instead of single string (better for chunking later)
        return [doc.page_content for doc in docs]

    except Exception as e:
        logger.exception(f"Failed to load document: {path}")
        raise RuntimeError(f"Document loading failed: {str(e)}")
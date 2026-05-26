# from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_text_splitters import RecursiveCharacterTextSplitter
import logging

logger = logging.getLogger(__name__)


def split_text(text: str):

    try:
        # 🔥 Resume-specific structure
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=600,
            chunk_overlap=120,
            separators=[
                "\n\n",          # sections (Experience, Skills)
                "\n",            # lines
                ". ",            # sentences
                " "              # fallback
            ]
        )

        chunks = splitter.split_text(text)

        # 🔥 Clean + filter
        clean_chunks = [
            c.strip()
            for c in chunks
            if len(c.strip()) > 40
        ]

        logger.info(
            "chunking_completed",
            extra={"chunks": len(clean_chunks)}
        )

        return clean_chunks

    except Exception as e:
        logger.exception("chunking_failed")
        raise RuntimeError("Chunking failed")
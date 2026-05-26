from langchain.text_splitter import RecursiveCharacterTextSplitter


def chunk_text(pages: list[str]):

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,          # tuned for embeddings
        chunk_overlap=100,       # keeps context
        separators=["\n\n", "\n", ".", " "]
    )

    chunks = splitter.create_documents(pages)

    return chunks
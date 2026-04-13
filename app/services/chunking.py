from langchain_text_splitters import RecursiveCharacterTextSplitter


def split_text(text: str):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=700,
        chunk_overlap=50
    )

    return splitter.split_text(text)


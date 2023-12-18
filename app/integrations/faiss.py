import pickle
from pathlib import Path

from langchain.chat_models import ChatOpenAI
from langchain.document_loaders import PyPDFLoader
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import FAISS

from app.config import settings


def build_index(pdf_path_str: str, use_cached: bool = True) -> FAISS:
    """
    Build a FAISS index from a PDF file.

    Args:
        pdf_path_str (str): path to the PDF file
        use_cached (bool, optional): whether to use the cached index. Defaults to True.

    Raises:
        FileNotFoundError: if the PDF file does not exist

    Returns:
        FAISS: the Langchain FAISS index object
    """
    pdf_path = Path(pdf_path_str).resolve()
    if not pdf_path.exists():
        raise FileNotFoundError(f"File {pdf_path} does not exist")

    pickle_filepath = Path(pdf_path_str.replace(".pdf", ".pickle")).resolve()
    if pickle_filepath.exists() and use_cached:
        with open(pickle_filepath, "rb") as handle:
            faiss_index = pickle.load(handle)
    else:
        loader = PyPDFLoader(pdf_path.as_posix())
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=250, chunk_overlap=50)
        all_splits = text_splitter.split_documents(loader.load())

        faiss_index = FAISS.from_documents(all_splits, OpenAIEmbeddings())

        with open(pickle_filepath, "wb") as handle:
            pickle.dump(faiss_index, handle, protocol=pickle.HIGHEST_PROTOCOL)

    return faiss_index


if __name__ == "__main__":
    pdf_path_str = "./assets/HR_policies.pdf"
    pdf_path = Path(pdf_path_str).resolve()
    if not pdf_path.exists():
        raise FileNotFoundError(f"File {pdf_path} does not exist")

    pickle_filepath = Path(pdf_path_str.replace(".pdf", ".pickle")).resolve()
    if pickle_filepath.exists():
        with open(pickle_filepath, "rb") as handle_rb:
            faiss_index = pickle.load(handle_rb)
    else:
        loader = PyPDFLoader(pdf_path.as_posix())

        text_splitter = RecursiveCharacterTextSplitter(chunk_size=250, chunk_overlap=50)
        all_splits = text_splitter.split_documents(loader.load())

        faiss_index = FAISS.from_documents(all_splits, OpenAIEmbeddings())
        with open(pickle_filepath, "wb") as handle_wb:
            pickle.dump(faiss_index, handle_wb, protocol=pickle.HIGHEST_PROTOCOL)

    query = "what is the holiday policy?"
    docs = faiss_index.similarity_search(query, k=5)

    llm = ChatOpenAI(temperature=0.1, model=settings.OPENAI_MODEL)

    clean_docs = [doc.page_content for doc in docs]
    result = llm.predict(
        f"""You are a helpful question-answering assistant. You are asked the following question:\n\n
        "{query}"\n

        You have to answer the question. You can use the following information:\n\n
        {clean_docs}\n

        Be concise. Answer:"
        """
    )

    print(result)

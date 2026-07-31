"""
RAG Tabanlı Akıllı PDF Asistanı - Çekirdek Mantık ve Yardımcı Fonksiyonlar
"""

import os
import tempfile
from typing import List, Tuple, Dict, Any
from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import PromptTemplate

from config import (
    DEFAULT_LLM_MODEL,
    DEFAULT_EMBEDDING_MODEL,
    CHUNK_SIZE,
    CHUNK_OVERLAP,
    MODE_STRICT,
    MODE_HYBRID,
    STRICT_SYSTEM_PROMPT,
    HYBRID_SYSTEM_PROMPT
)


def load_pdf_with_page_metadata(uploaded_file) -> Tuple[List[Document], int]:
    """
    Streamlit üzerinden yüklenen PDF dosyasını geçici dosyaya yazıp PyPDFLoader ile okur.
    Her sayfanın 1-indexed sayfa numarasını metadata olarak kaydeder.
    
    Returns:
        Tuple[List[Document], int]: (Doküman listesi, Toplam sayfa sayısı)
    """
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        tmp_file.write(uploaded_file.getvalue())
        tmp_path = tmp_file.name

    try:
        loader = PyPDFLoader(tmp_path)
        documents = loader.load()
        
        total_pages = len(documents)
        # Sayfa numaralarını 1-indexed yapmak için düzenliyoruz (PyPDFLoader 0-indexed verir)
        for doc in documents:
            if "page" in doc.metadata:
                doc.metadata["page"] = doc.metadata["page"] + 1
            else:
                doc.metadata["page"] = 1
                
        return documents, total_pages
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def split_documents(documents: List[Document]) -> List[Document]:
    """
    Dokümanları belirlenen chunk_size ve chunk_overlap değerlerine göre böler.
    Sayfa metadatasını korur.
    """
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", " ", ""]
    )
    chunks = text_splitter.split_documents(documents)
    return chunks


def create_faiss_vector_store(chunks: List[Document], api_key: str = None) -> FAISS:
    """
    Metin parçalarından yerel HuggingFaceEmbeddings (all-MiniLM-L6-v2) kullanarak FAISS vektör veritabanı oluşturur.
    """
    embeddings = HuggingFaceEmbeddings(model_name=DEFAULT_EMBEDDING_MODEL)
    vector_store = FAISS.from_documents(chunks, embeddings)
    return vector_store


def answer_question_stream(
    vector_store: FAISS,
    query: str,
    api_key: str,
    mode: str = MODE_STRICT,
    llm_model: str = DEFAULT_LLM_MODEL,
    k: int = 4
) -> Tuple[Any, List[Document]]:
    """
    Kullanıcının sorusuna seçilen moda göre canlı kelime akışı (generator) ve kaynak dokümanları döner.
    Exception handling ve güvenli jeneratör yapısı içerir.
    """
    # Vektör veritabanından en alakalı k parçayı getir
    retriever = vector_store.as_retriever(search_kwargs={"k": k})
    relevant_docs = retriever.invoke(query)

    # Bağlamı (context) sayfa bilgisiyle birleştir
    context_blocks = []
    for doc in relevant_docs:
        page_num = doc.metadata.get("page", "?")
        context_blocks.append(f"[Sayfa {page_num}]:\n{doc.page_content}")
        
    context_text = "\n\n---\n\n".join(context_blocks)

    # Moda göre prompt seç
    prompt_str = HYBRID_SYSTEM_PROMPT if mode == MODE_HYBRID else STRICT_SYSTEM_PROMPT
    prompt_template = PromptTemplate(
        template=prompt_str,
        input_variables=["context", "question"]
    )

    formatted_prompt = prompt_template.format(context=context_text, question=query)

    # LLM Çağrısı (Streaming Aktif)
    llm = ChatGoogleGenerativeAI(
        model=llm_model,
        google_api_key=api_key,
        temperature=0.3 if mode == MODE_HYBRID else 0.0,
        streaming=True
    )

    def text_generator():
        try:
            for chunk in llm.stream(formatted_prompt):
                if chunk and chunk.content:
                    yield chunk.content
        except Exception as e:
            yield f"\n\n⚠️ **Hata:** Yanıt akışı sırasında bir sorun oluştu: {str(e)}"

    return text_generator(), relevant_docs


def answer_question(
    vector_store: FAISS,
    query: str,
    api_key: str,
    mode: str = MODE_STRICT,
    llm_model: str = DEFAULT_LLM_MODEL,
    k: int = 4
) -> Tuple[str, List[Document]]:
    """
    Kullanıcının sorusuna tek seferde yanıt verir ve kullanılan kaynak dokümanları döner.
    """
    retriever = vector_store.as_retriever(search_kwargs={"k": k})
    relevant_docs = retriever.invoke(query)

    context_blocks = []
    for doc in relevant_docs:
        page_num = doc.metadata.get("page", "?")
        context_blocks.append(f"[Sayfa {page_num}]:\n{doc.page_content}")
        
    context_text = "\n\n---\n\n".join(context_blocks)

    prompt_str = HYBRID_SYSTEM_PROMPT if mode == MODE_HYBRID else STRICT_SYSTEM_PROMPT
    prompt_template = PromptTemplate(
        template=prompt_str,
        input_variables=["context", "question"]
    )

    formatted_prompt = prompt_template.format(context=context_text, question=query)

    llm = ChatGoogleGenerativeAI(
        model=llm_model,
        google_api_key=api_key,
        temperature=0.3 if mode == MODE_HYBRID else 0.0
    )

    response = llm.invoke(formatted_prompt)
    answer = response.content

    return answer, relevant_docs

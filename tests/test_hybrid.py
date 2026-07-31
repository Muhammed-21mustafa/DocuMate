"""
Adım 3: Hybrid Search (BM25 Keyword + FAISS Vector Ensemble) Testleri
"""

from langchain_core.documents import Document
from utils import create_faiss_vector_store, create_hybrid_retriever
from config import HYBRID_WEIGHT_BM25, HYBRID_WEIGHT_FAISS, RETRIEVER_K


def test_hybrid_search_creation():
    """
    create_hybrid_retriever fonksiyonunun BM25 ve FAISS motorlarını doğru ağırlıklarla birleştirdiğini test eder.
    """
    doc1 = Document(page_content="Round Robin O(1) zaman karmaşıklığına sahiptir.", metadata={"page": 1})
    doc2 = Document(page_content="TCP 3-way handshake üçlü el sıkışma mekanizmasıdır.", metadata={"page": 2})
    chunks = [doc1, doc2]

    # Gerçek FAISS Vector Store oluştur
    vector_store = create_faiss_vector_store(chunks)

    # Hybrid Retriever Oluştur
    ensemble_retriever = create_hybrid_retriever(chunks, vector_store, k=2)

    # Ağırlıkların config.py'deki değerlerle eşleştiğini doğrula
    assert len(ensemble_retriever.retrievers) == 2
    assert ensemble_retriever.weights == [HYBRID_WEIGHT_BM25, HYBRID_WEIGHT_FAISS]
    assert ensemble_retriever.weights[0] == 0.5
    assert ensemble_retriever.weights[1] == 0.5


def test_bm25_keyword_matching():
    """
    BM25 retriever'ın tam kelime / kısaltma aramalarını (%100 kelime eşleşmesi) başarıyla bulduğunu test eder.
    """
    doc1 = Document(page_content="İşlemci zamanlaması süreç sıralaması yönetimidir.", metadata={"page": 1})
    doc2 = Document(page_content="Özel Kısaltma: DEADLOCK_PREVENTION_ALGORITHM_V2", metadata={"page": 2})
    chunks = [doc1, doc2]

    vector_store = create_faiss_vector_store(chunks)
    ensemble_retriever = create_hybrid_retriever(chunks, vector_store, k=1)
    
    # Kısaltmayı arat
    results = ensemble_retriever.invoke("DEADLOCK_PREVENTION_ALGORITHM_V2")
    
    assert len(results) > 0
    assert any("DEADLOCK_PREVENTION_ALGORITHM_V2" in r.page_content for r in results)

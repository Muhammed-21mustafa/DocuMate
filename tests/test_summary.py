"""
Adım 4: Tam Doküman Map-Reduce Özetleme Testleri
"""

from unittest.mock import MagicMock, patch
from langchain_core.documents import Document
from utils import is_summary_request, generate_full_document_summary_stream


def test_is_summary_request_detection():
    """
    Özetleme anahtar kelimelerinin doğru tespit edildiğini doğrular.
    """
    assert is_summary_request("Bana bu PDF'in genel bir özetini çıkar") is True
    assert is_summary_request("Dokümanı özetler misin?") is True
    assert is_summary_request("Ana hatları nelerdir?") is True
    assert is_summary_request("Round Robin algoritması nedir?") is False


@patch("utils.ChatGoogleGenerativeAI")
def test_generate_full_document_summary_stream(mock_llm_class):
    """
    Map-Reduce özetleme akışının parçaları sıralı işleyip jeneratör ürettiğini test eder.
    """
    mock_instance = MagicMock()
    mock_instance.invoke.return_value = MagicMock(content="Bölüm ara özeti")
    mock_instance.stream.return_value = [MagicMock(content="Final "), MagicMock(content="Özeti")]
    mock_llm_class.return_value = mock_instance

    doc1 = Document(page_content="Bölüm 1 metni...", metadata={"page": 1})
    doc2 = Document(page_content="Bölüm 2 metni...", metadata={"page": 15})
    chunks = [doc1, doc2]

    stream_gen, selected_chunks = generate_full_document_summary_stream(
        chunks=chunks,
        api_key="fake_key"
    )

    assert len(selected_chunks) > 0
    full_output = "".join(list(stream_gen))
    assert full_output == "Final Özeti"

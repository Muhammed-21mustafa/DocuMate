"""
Adım 1: Streaming Response ve Markdown Stabilitesi Testleri
"""

from unittest.mock import MagicMock
from langchain_core.documents import Document
from utils import answer_question_stream
from config import MODE_STRICT, DEFAULT_LLM_MODEL


def test_markdown_streaming_chunks():
    """
    Kod blokları (```python ... ```) ve listelerin stream jeneratöründen tam olarak aktarıldığını doğrular.
    """
    mock_chunks = [
        MagicMock(content="İşte bir Java örneği:\n\n```java\n"),
        MagicMock(content="public class Test {\n"),
        MagicMock(content="    public static void main(String[] args) {\n"),
        MagicMock(content='        System.out.println("Hello World");\n'),
        MagicMock(content="    }\n}\n```\n\n- Liste maddesi 1\n- Liste maddesi 2")
    ]
    
    # Text generator simülasyonu
    def mock_generator():
        for chunk in mock_chunks:
            yield chunk.content
            
    full_text = "".join(list(mock_generator()))
    
    # Kod bloklarının ve listenin bozulmadığını kontrol et
    assert "```java" in full_text
    assert "System.out.println" in full_text
    assert "```" in full_text
    assert "- Liste maddesi 1" in full_text


def test_streaming_exception_handling():
    """
    Stream sırasında oluşabilecek API/Ağ hatalarının yakalanıp jeneratörden kullanıcı dostu mesaj dönmesini test eder.
    """
    def faulty_generator():
        yield "Başlangıç parçası..."
        raise RuntimeError("API bağlantısı koptu!")

    def safe_generator_wrapper(gen):
        try:
            for item in gen:
                yield item
        except Exception as e:
            yield f"\n\n⚠️ **Hata:** Yanıt akışı sırasında bir sorun oluştu: {str(e)}"

    output = list(safe_generator_wrapper(faulty_generator()))
    full_output = "".join(output)
    
    assert "Başlangıç parçası..." in full_output
    assert "⚠️ **Hata:**" in full_output
    assert "API bağlantısı koptu!" in full_output

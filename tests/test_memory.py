"""
Adım 2: Conversation Memory (Sohbet Hafızası & Soru Yeniden Yazıcı) Testleri
"""

from unittest.mock import MagicMock, patch
from utils import format_chat_history, rewrite_question_with_history


def test_format_chat_history():
    """
    Sohbet geçmişindeki tüm mesajların kesintisiz (unbounded) biçimlendirildiğini kontrol eder.
    """
    history = [
        {"role": "user", "content": "Round Robin nedir?"},
        {"role": "assistant", "content": "Round Robin bir zamanlama algoritmasıdır."},
        {"role": "user", "content": "Peki bunun avantajı nedir?"},
        {"role": "assistant", "content": "Kilitlenmeyi önler ve adil süre verir."}
    ]
    
    formatted = format_chat_history(history)
    
    assert "Kullanıcı: Round Robin nedir?" in formatted
    assert "Asistan: Round Robin bir zamanlama algoritmasıdır." in formatted
    assert "Kullanıcı: Peki bunun avantajı nedir?" in formatted
    assert "Asistan: Kilitlenmeyi önler ve adil süre verir." in formatted


def test_rewrite_question_with_history_fallback():
    """
    Sohbet geçmişi olmadığında veya API hatasında orijinal sorunun korunduğunu test eder.
    """
    # 1. Geçmiş boşsa orijinal soru dönmeli
    assert rewrite_question_with_history("Peki bunun avantajı ne?", [], "fake_key") == "Peki bunun avantajı ne?"
    
    # 2. API Key yoksa orijinal soru dönmeli
    history = [{"role": "user", "content": "Soru 1"}]
    assert rewrite_question_with_history("Soru 2", history, "") == "Soru 2"


@patch("utils.ChatGoogleGenerativeAI")
def test_rewrite_question_success(mock_llm_class):
    """
    LLM başarıyla yeni sorgu ürettiğinde bağımsız sorunun döndüğünü test eder.
    """
    mock_instance = MagicMock()
    mock_instance.invoke.return_value = MagicMock(content="Round Robin zamanlama algoritmasının avantajları nelerdir?")
    mock_llm_class.return_value = mock_instance

    history = [{"role": "user", "content": "Round Robin nedir?"}]
    rewritten = rewrite_question_with_history("Peki bunun avantajları nelerdir?", history, "fake_key")
    
    assert rewritten == "Round Robin zamanlama algoritmasının avantajları nelerdir?"

"""
RAG Tabanlı Akıllı PDF Asistanı - Konfigürasyon Yapılandırması
"""

import os

# Model Yapılandırmaları
DEFAULT_LLM_MODEL = "gemini-2.5-flash"
AVAILABLE_LLM_MODELS = [
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gemini-1.5-pro",
    "gemini-1.5-flash-latest"
]
DEFAULT_EMBEDDING_MODEL = "all-MiniLM-L6-v2"

# Chunking (Metin Bölme) Parametreleri
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200

# Hybrid Search Yapılandırmaları (BM25 + FAISS Ağırlıkları)
HYBRID_WEIGHT_BM25 = 0.5
HYBRID_WEIGHT_FAISS = 0.5
RETRIEVER_K = 4

# RAG Çalışma Modları
MODE_STRICT = "strict"
MODE_HYBRID = "hybrid"

# Prompt Şablonları

STRICT_SYSTEM_PROMPT = """Sen yüklenen PDF dokümanı konusunda uzmanlaşmış katı bir asistansın.

Sana verilen bağlamı (context) dikkatlice oku ve kullanıcının sorusunu SADECE ve SADECE verilen bağlama dayanarak yanıtla.

KURALLAR:
1. Bağlam dışından hiçbir genel bilgi, varsayım veya tahmin EKLEME.
2. Eğer kullanıcının sorusunun cevabı bağlamda açıkça geçmiyorsa, dürüstçe "Bu bilgi verilen dokümanda bulunmamaktadır." de.
3. Cevap verirken kibar, öz ve anlaşılır ol.
4. Cevabını doğrudan bağlamdaki bilgilere dayandır.

Bağlam (Context):
{context}

Soru:
{question}

Cevap:"""

HYBRID_SYSTEM_PROMPT = """Sen yüklenen PDF dokümanını temel alan ama kullanıcının konuyu detaylarıyla anlamasına yardımcı olan akıllı bir ders ve araştırma asistansın.

Sana verilen bağlamı (context) ve kullanıcının sorusunu incele.

KURALLAR:
1. Öncelikli olarak cevabını verilen bağlama (PDF içeriğine) dayandır.
2. Eğer dokümandaki bilgi kısıtlıysa veya kullanıcı konuyla ilgili kod/örnek/açıklama istemiş ama dokümanda tam yoksa:
   - Önce dokümanda yazan kısmı sun ve belirt.
   - Ardından "💡 Öğretmen Notu (PDF Dışı Ek Bilgi)" başlığı altında kendi genel bilginle konuyu açıklayıcı örnekler ve detaylar ver.
3. Ek bilginin doküman dışından olduğunu net bir şekilde vurgula ki kullanıcı neyin PDF'ten neyin ek bilgi olduğundan emin olsun.

Bağlam (Context):
{context}

Soru:
{question}

Cevap:"""

REWRITE_QUESTION_SYSTEM_PROMPT = """Sohbet geçmişi ve kullanıcının son sorusu aşağıda verilmiştir.

Görev: Sohbet geçmişindeki bağlamı göz önüne alarak, kullanıcının son sorusunu tamamen bağımsız (standalone) ve kendi başına anlaşılır tek bir soru olarak yeniden yaz.

KURALLAR:
1. Son sorudaki 'bu', 'bunun', 'o', 'şundaki', 'yukarıdaki' gibi atıfları sohbet geçmişindeki açık kavramlarla değiştir.
2. Soruyu CEVAPLAMA, SADECE yeniden yazılmış tek bir soru cümlesi üret.
3. Eğer soru zaten tam ve bağımsızsa veya sohbet geçmişiyle ilgisizse, soruyu hiç değiştirmeden AYNEN döndür.

Sohbet Geçmişi:
{chat_history}

Kullanıcının Son Sorusu:
{question}

Yeniden Yazılmış Bağımsız Soru:"""

# Özet İstek Kelimeleri
SUMMARY_KEYWORDS = [
    "özet", "özetle", "özetini", "özetler misin", "özeti",
    "ana hatları", "genel bakış", "ne anlatıyor", "doküman özeti"
]

SUMMARY_MAP_PROMPT = """Aşağıdaki metin parçası uzun bir PDF dokümanının bir bölümüdür.

Görev: Bu metin parçasındaki ana fikirleri, önemli tanımları ve öne çıkan noktaları maddeler halinde özetle.

Metin Parçası:
{context}

Bölüm Özeti:"""

SUMMARY_REDUCE_PROMPT = """Aşağıda uzun bir PDF dokümanının farklı bölümlerinden elde edilen ara özetler verilmiştir.

Görev: Bu ara özetleri birleştirerek tüm dokümanı kapsayan, akıcı, anlaşılır ve yapılandırılmış profesyonel bir FİNAL DOKÜMAN ÖZETİ oluştur.

Lütfen çıktıyı şu başlıklar altında düzenle:
📌 **1. Dokümanın Ana Konusu ve Amacı**
📚 **2. Öne Çıkan Ana Başlıklar ve Özetler**
💡 **3. Kritik Tanımlar ve Sonuç**

Ara Özetler:
{context}

Final Doküman Özeti:"""

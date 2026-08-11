# 📚 RAG Tabanlı Akıllı PDF Asistanı

![Python](https://img.shields.io/badge/Python-3.9%2B-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-1.30%2B-red)
![LangChain](https://img.shields.io/badge/LangChain-Enabled-green)
![Gemini API](https://img.shields.io/badge/Google%20Gemini-1.5%20Flash-orange)
![FAISS](https://img.shields.io/badge/FAISS-Vector%20Store-purple)

Kullanıcıların kendi PDF dokümanlarını (ders notları, kitaplar, makaleler, şartnameler) yükleyerek içindeki bilgilerle sohbet edebilmesini sağlayan yerel (local) bir **Retrieval-Augmented Generation (RAG)** sistemidir.

Proje, genel LLM modellerinin halüsinasyon görmesini engellemek, doküman sadakatini önceliklendirerek halüsinasyon riskini en aza indirmek ve yüklenen dokümana sadık kalarak **sayfa numaralı kaynak gösterimi (citation)** sunmak amacıyla geliştirilmiştir.

---

## 🌟 Öne Çıkan Özellikler

- **🔍 Hibrit Arama (BM25 + FAISS Ensemble):** Birebir kelime/kısaltma eşleşmesi için BM25 ile anlamsal vektör aramasını (FAISS) birleştirerek en alakalı metin parçalarını yakalar.
- **📑 Tam Doküman Map-Reduce Özetleme:** Uzun PDF'lerin tamamını gruplayarak sırayla taranan ara özetlerden yapılandırılmış, profesyonel bir doküman özeti üretir.
- **🔄 Sohbet Hafızası (History-Aware Rewriter):** Kullanıcının takip sorularını sohbet geçmişinden bağımsız net sorgulara dönüştürür.
- **⚡ Yerel Embeddings (all-MiniLM-L6-v2):** Doküman parçalaması ve vektörleşme tamamen yerel HuggingFace modelleriyle sıfır embedding API maliyetiyle gerçekleşir.
- **🎯 Çift Modlu RAG (Dual-Mode RAG Architecture):**
  - **Katı Sınav Modu (Strict Grounding):** Sadece ve sadece yüklenen PDF'teki bilgilere dayanır. PDF'te olmayan sorular için halüsinasyon riskini önlemek adına *"Dokümanda bulunmamaktadır"* yanıtı verir.
  - **Öğretmen / Hibrit Mod (Hybrid Learning):** PDF'teki bilgiyi sunduktan sonra, konunun anlaşılması için eksik kalan kod örneklerini ve detayları `💡 Öğretmen Notu (PDF Dışı Ek Bilgi)` başlığı altında ayrıştırarak sunar.
- **📌 Sayfa Numaralı Kaynak Gösterimi (Page Citations):** Üretilen her yanıtın altında, bilginin PDF'in tam olarak hangi sayfasından ve hangi paragrafından alındığı açılır kartlar (expander) şeklinde gösterilir.
- **⚡ Canlı Metin Akışı (Streaming):** Yanıtlar kullanıcıya kelime kelime canlı akar.

---

## 🛠️ Teknoloji Yığını

- **Kullanıcı Arayüzü:** [Streamlit](https://streamlit.io/)
- **RAG Orkestrasyonu:** [LangChain](https://www.langchain.com/)
- **Vektör & Kelime Veritabanı:** [FAISS](https://github.com/facebookresearch/faiss) & [BM25 (rank-bm25)](https://pypi.org/project/rank-bm25/)
- **Metin İşleme & PDF Parsing:** `PyPDF` / `RecursiveCharacterTextSplitter`
- **LLM & Embeddings:** Google Gemini API (`gemini-2.5-flash`) & Yerel `all-MiniLM-L6-v2` (`sentence-transformers`)

---

## 🏗️ Proje Mimarisi

```
RagProject/
├── app.py               # Streamlit kullanıcı arayüzü ve sohbet akışı
├── utils.py             # Sayfa bazlı PDF işleme, BM25+FAISS indeksleme, Map-Reduce ve RAG sorgulama
├── config.py            # Model yapılandırmaları, RAG ağırlıkları ve prompt şablonları
├── tests/               # Streaming, Sohbet Hafızası, Hibrit Arama ve Özetleme birim testleri
├── requirements.txt     # Bağımlılıklar
├── .env.example         # Çevre değişkeni örneği
└── README.md            # Proje dokümantasyonu
```

### Çalışma Akışı (Pipeline)

1. **Load (Yükleme):** Yüklenen PDF `PyPDFLoader` ile okunur ve her sayfanın numarası metadata olarak kaydedilir.
2. **Chunking (Bölme):** Uzun metinler `RecursiveCharacterTextSplitter` ile 1000 karakterlik parçalara bölünür (sayfa numarası korunur).
3. **Embedding & Hybrid Index:** Metinler yerel `all-MiniLM-L6-v2` ile vektörleştirilip FAISS veritabanına ve kelimesel arama için BM25 indeksine aktarılır.
4. **Question Rewrite & Retrieval:** Takip soruları geçmişle birleştirilerek bağımsız sorguya dönüştürülür ve `EnsembleRetriever` (0.5 BM25 + 0.5 FAISS) ile en alakalı parçalar getirilir.
5. **Generation & Streaming:** Seçilen moda (Katı, Hibrit veya Map-Reduce Özet) uygun prompt ile Gemini LLM'e gönderilerek canlı yayın olarak yanıt üretilir.

---

## 🚀 Kurulum ve Çalıştırma

### 1. Depoyu Klonlayın
```bash
git clone https://github.com/KULLANICI_ADINIZ/pdf-asistani.git
cd pdf-asistani
```

### 2. Sanal Ortam Oluşturun ve Aktifleştirin
* **Windows:**
  ```cmd
  python -m venv venv
  venv\Scripts\activate
  ```
* **macOS / Linux:**
  ```bash
  python3 -m venv venv
  source venv/bin/activate
  ```

### 3. Gerekli Kütüphaneleri Kurun
```bash
pip install -r requirements.txt
```

### 4. API Anahtarınızı Ayarlayın
`.env.example` dosyasının adını `.env` olarak değiştirin ve [Google AI Studio](https://aistudio.google.com/)'dan aldığınız API anahtarını ekleyin:
```env
GOOGLE_API_KEY=sizin_gemini_api_anahtariniz
```
*(Not: API anahtarınızı Streamlit arayüzündeki sol menüden de girebilirsiniz).*

### 5. Uygulamayı Başlatın
```bash
streamlit run app.py
```

---

## 🤖 Cursor / AI Geliştirici Yönergeleri

Proje üzerinde yapay zeka asistanları (Cursor, GitHub Copilot vb.) ile geliştirme yaparken dikkat edilecek kurallar:

1. **Modüler Yapıyı Koruyun:** UI mantığı `app.py` içerisinde, ağır RAG ve veri işleme mantığı `utils.py` içerisinde kalmalıdır.
2. **Prompt Güvenliği:** Prompt üzerinde değişiklik yaparken `config.py` içerisindeki katı ve hibrit kural kalıplarını bozmamaya dikkat edin.
3. **Metadata Takipleri:** PDF metadatasından `page` bilgisinin silinmediğinden ve her zaman 1-indexed olarak kullanıcıya sunulduğundan emin olun.

---

## 📄 Lisans
Bu proje [MIT Lisansı](LICENSE) ile lisanslanmıştır. Açık kaynak olarak dilediğiniz gibi kullanabilir ve geliştirebilirsiniz.

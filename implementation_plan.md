# 🚀 Adım 4: Akıllı Soru Yönlendirici (Query Router & Metadata/Özetleme Mantığı) Uygulama Planı

Bu adım, kullanıcı sorularını niyetlerine (intent) göre sınıflandırarak **Metadata Soruları**, **Doküman Özetleme İstekleri** ve **Standart RAG Soruları** arasında akıllı yönlendirme yapan bir **Query Router Agent** mimarisini eklemeyi hedefler.

---

## 🎯 Amaç ve Kazanımlar
- **Sıfır Maliyet & Anında Yanıt (Metadata Queries):** *"Bu PDF kaç sayfa?"*, *"Dosya adı ne?"* gibi sorular için RAG/Vektör araması baypas edilerek doğrudan doküman verilerinden anında yanıt verilir.
- **Kapsamlı Özetleme (Document Summarization):** *"Bana bu PDF'i özetle"* isteklerinde 4 rastgele chunk getirmek yerine tüm dokümanın ana hatlarını çıkaran özel özetleme zinciri tetiklenir.
- **Akıllı Niyet Sınıflandırması (Query Router):** Her soru otomatik olarak 3 kategoriden birine yönlendirilir (`METADATA`, `SUMMARY`, `RAG`).

---

## 📝 Değişiklik Detayları (Proposed Changes)

### 1. Yapılandırma ve Promptlar

#### [MODIFY] [config.py](file:///c:/Users/musta/Desktop/RagProject/config.py)
- `QUERY_ROUTER_PROMPT` şablonu eklenecek:
  - Kullanıcı sorusunu `METADATA`, `SUMMARY` veya `RAG` olarak etikete dönüştüren hafif ve hızlı prompt.

### 2. Çekirdek RAG & Router Motoru

#### [MODIFY] [utils.py](file:///c:/Users/musta/Desktop/RagProject/utils.py)
- `classify_query(query, api_key, llm_model)` fonksiyonu eklenecek:
  - Sorunun niyetini belirleyecek. Hata durumunda güvenli bir şekilde `RAG` kategorisine düşecek.
- `generate_document_summary_stream(vector_store, api_key, llm_model)` fonksiyonu eklenecek:
  - Dokümanın genel yapısını temsil eden parçalardan yapılandırılmış özet akışı üretecek.

### 3. Kullanıcı Arayüzü (UI)

#### [MODIFY] [app.py](file:///c:/Users/musta/Desktop/RagProject/app.py)
- Soru sorulduğunda önce `classify_query` çalışacak:
  - **METADATA** ise: Vektör aramasını atlayıp doğrudan `pdf_stats` üzerinden anında yanıt verecek.
  - **SUMMARY** ise: Özel özetleme akışını başlatacak.
  - **RAG** ise: Mevcut History-Aware Hybrid RAG akışını çalıştıracak.

### 4. Birim Testler

#### [NEW] [tests/test_router.py](file:///c:/Users/musta/Desktop/RagProject/tests/test_router.py)
- Niyet sınıflandırma, metadata hızlı yanıtı ve fallback mantığını doğrulayan birim testler.

---

## 🧪 Doğrulama Planı (Verification Plan)

### Manuel Doğrulama Adımları
1. Uygulama `streamlit run app.py` ile çalıştırılacak.
2. PDF yüklenecek ve *"Bu PDF kaç sayfa ve dosya adı ne?"* sorulacak -> Vektör araması yapılmadan anında metadata yanıtı alındığı doğrulanacak.
3. *"Bu dokümanın genel bir özetini çıkar"* sorulacak -> Yapılandırılmış özet çıktığı doğrulanacak.
4. Konu detayı sorulacak -> Hibrit RAG mekanizmasının çalıştığı doğrulanacak.

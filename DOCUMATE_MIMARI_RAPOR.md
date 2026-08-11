# 📘 DocuMate - RAG Tabanlı Akıllı PDF Asistanı (Kapsamlı Mimari & Çalışma Raporu)

Bu rapor, **DocuMate** projesinin çalışma mantığını, mimari bileşenlerini, kullanılan tüm prompt şablonlarını ve gerçek hayat kullanım senaryolarını %100 şeffaflıkla açıklamak amacıyla hazırlanmıştır.

---

## 🎯 1. Projenin Var Olma Sebebi ve Temel Felsefesi

### Problem: Neden Direkt ChatGPT/Gemini Web Arayüzü Değil?
Kullanıcılar 60-70 sayfalık (veya daha uzun) ders notlarını veya teknik dokümanları doğrudan ChatGPT/Gemini web arayüzüne yüklediklerinde **3 ana problemle** karşılaşırlar:
1. **Halüsinasyon (Uydurma Bilgi):** Model genel bilgi dağarcığı ile doküman bilgisini harmanlar ve dokümanda yazmayan şeyleri yazmış gibi sunabilir.
2. **Context Window ve Yüzeysellik:** Doküman uzadıkça model metnin ortasındaki kritik detayları kaçırır (Needle-in-a-Haystack problemi).
3. **Kaynak Gösterilememesi:** Cevabın PDF'in tam olarak hangi sayfasından ve hangi paragrafından alındığı teyit edilemez.

### Çözüm: DocuMate Nasıl Çözer?
DocuMate; metni sayfa bazlı indeksleyen yerel embedding modelleri (`all-MiniLM-L6-v2`), kelime ve anlamsal aramayı birleştiren **Hibrit Arama (BM25 + FAISS)**, sohbet hafızasını yöneten **Soru Yeniden Yazıcı (Query Rewriter)**, dokümanın tamamını kapsayan **Map-Reduce Özetleme** ve **Çift Modlu Prompt Mimarısı** ile doküman sadakatini önceliklendirerek halüsinasyon riskini en aza indirir.

---

## 🏗️ 2. Sistem Mimarisi ve Veri Akış Şeması

DocuMate üzerindeki bir kullanıcının PDF yükleme ve soru sorma adımlarındaki veri akışı şu şekildedir:

```text
               [ Yüklenen PDF Dosyası ]
                          │
                 (PyPDFLoader Parsing)
                          │
          [ Sayfa Metadatalı Dokümanlar ]
            (metadata: {"page": 1, 2...})
                          │
           (RecursiveCharacterTextSplitter)
            (chunk_size=1000, overlap=200)
                          │
           (Sohbet Sorusu veya Özet İsteği)
                          │
           [ is_summary_request Kontrolü ]
            /                           \
       (Evet)                          (Hayır)
         │                                │
         ▼                                ▼
[ Map-Reduce Özet ]            [ Question Rewriter ]
(Sıralı Parça Taraması)       (Bağımsız Sorgu Oluşturur)
         │                                │
         │                     ┌──────────┴──────────┐
         │                     ▼                     ▼
         │             [ BM25 Retriever ]    [ FAISS Vector Store ]
         │             (Keyword Matching)    (Semantic Search)
         │                     └──────────┬──────────┘
         │                                ▼
         │                    [ EnsembleRetriever ]
         │                    (0.5 BM25 / 0.5 FAISS)
         │                                │
         └────────────────┬───────────────┘
                          ▼
            [ Gemini 2.5 Flash API (Streaming) ]
                          │
                          ▼
            [ Streamlit UI + Sayfa Kartları ]
```

---

## 📝 3. Kullanılan Tüm Prompt'lar ve Çalışma Mantıkları

Sistem içerisinde 3 farklı özel yapıda prompt şablonu çalışır:

### 1. 🎯 Katı Sınav Modu Promptu (`STRICT_SYSTEM_PROMPT`)
* **Mantık:** `temperature=0.0`. Modelin PDF dışından tek bir kelime dahi eklemesine izin vermez. Dokümanda yoksa dürüstçe *"Bulunmamaktadır"* der.
* **Kullanım Amacı:** Vize/Final öncesi "Sadece hocanın notlarında yazanları bileyim" diyen öğrenciler veya hukuki/resmi belge inceleyenler için.

```text
Sen yüklenen PDF dokümanı konusunda uzmanlaşmış katı bir asistansın.

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

Cevap:
```

---

### 2. 🧠 Öğretmen / Hibrit Mod Promptu (`HYBRID_SYSTEM_PROMPT`)
* **Mantık:** `temperature=0.3`. Önce PDF'teki bilgiyi sunar. Dokümanda kısıtlı bilgi varsa, PDF dışı açıklamayı **`💡 Öğretmen Notu (PDF Dışı Ek Bilgi)`** başlığı altında net bir şekilde ayırarak verir.
* **Kullanım Amacı:** PDF'teki tanımı okuyup anlamayan, ek kod örneğine veya detaylı açıklamaya ihtiyaç duyan öğrenciler için.

```text
Sen yüklenen PDF dokümanını temel alan ama kullanıcının konuyu detaylarıyla anlamasına yardımcı olan akıllı bir ders ve araştırma asistansın.

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

Cevap:
```

---

### 3. 🔄 Soru Yeniden Yazıcı Promptu (`REWRITE_QUESTION_SYSTEM_PROMPT`)
* **Mantık:** Kullanıcı sohbet sırasında takip sorusu sorduğunda (örn: *"Peki bunun avantajı ne?"*), bu soruyu vektör veritabanında aratmak imkansızdır. Bu prompt sohbet geçmişini okuyup soruyu bağımsız (standalone) bir arama sorgusuna dönüştürür (örn: *"Round Robin zamanlama algoritmasının avantajı nedir?"*).

```text
Sohbet geçmişi ve kullanıcının son sorusu aşağıda verilmiştir.

Görev: Sohbet geçmişindeki bağlamı göz önüne alarak, kullanıcının son sorusunu tamamen bağımsız (standalone) ve kendi başına anlaşılır tek bir soru olarak yeniden yaz.

KURALLAR:
1. Son sorudaki 'bu', 'bunun', 'o', 'şundaki', 'yukarıdaki' gibi atıfları sohbet geçmişindeki açık kavramlarla değiştir.
2. Soruyu CEVAPLAMA, SADECE yeniden yazılmış tek bir soru cümlesi üret.
3. Eğer soru zaten tam ve bağımsızsa veya sohbet geçmişiyle ilgisizse, soruyu hiç değiştirmeden AYNEN döndür.

Sohbet Geçmişi:
{chat_history}

Kullanıcının Son Sorusu:
{question}

Yeniden Yazılmış Bağımsız Soru:
```

---

### 4. 📄 Tam Doküman Map-Reduce Özetleme Promptu (`SUMMARY_REDUCE_PROMPT`)
* **Mantık:** Dokümanın tüm kısımları sıralı ve kontrollü olarak taranır (Map), elde edilen ara özetler birleştirilerek tek bir yapılandırılmış final özete dönüştürülür (Reduce).
* **Kullanım Amacı:** 100+ sayfalık bir dokümanın genel hatlarını ve ana felsefesini tek seferde kavramak isteyen kullanıcılar için.

```text
Aşağıda uzun bir PDF dokümanının farklı bölümlerinden elde edilen ara özetler verilmiştir.

Görev: Bu ara özetleri birleştirerek tüm dokümanı kapsayan, akıcı, anlaşılır ve yapılandırılmış profesyonel bir FİNAL DOKÜMAN ÖZETİ oluştur.

Lütfen çıktıyı şu başlıklar altında düzenle:
📌 1. Dokümanın Ana Konusu ve Amacı
📚 2. Öne Çıkan Ana Başlıklar ve Özetler
💡 3. Kritik Tanımlar ve Sonuç

Ara Özetler:
{context}

Final Doküman Özeti:
```

---

## 🎬 4. Gerçek Hayat Kullanım Senaryoları

### 📌 Senaryo 1: Vize Öncesi Hocanın Slaydına Sadık Kalma (Katı Mod)
* **Kullanıcı:** Ahmet (Bilgisayar Mühendisliği 3. Sınıf)
* **Doküman:** 70 sayfalık "İşletim Sistemleri" PDF slaytı.
* **Soru:** *"Hocanın slayttaki 'Round Robin' algoritması için belirttiği zaman karmaşıklığı nedir?"*
* **Sistem Çalışması:**
  1. `BM25` ve `FAISS` slayt 42'deki ilgili paragrafı yakalar.
  2. Katı mod devreye girer.
  3. Yanıt: *"Slayt sayfa 42'ye göre Round Robin zaman karmaşıklığı O(1)'dir."*
  4. Altına **📌 Kaynak: Sayfa 42** kartı eklenir. Genel internet tanımı eklenmez.

### 📌 Senaryo 2: Tanımı Anlamayıp Kod Örneği İsteme (Hibrit Mod)
* **Kullanıcı:** Mehmet (Yazılım Mühendisliği Öğrencisi)
* **Doküman:** Java Ders Notları PDF'i (Sayfa 14'te sadece *"Interface gövdesiz metot barındırır"* yazıyor).
* **Soru:** *"Interface nedir? Bana bir Java kod örneğiyle açıkla."*
* **Sistem Çalışması:**
  1. Hibrit Mod algılanır.
  2. Yanıtın ilk kısmında PDF Sayfa 14'teki tanım verilir.
  3. Altında `💡 Öğretmen Notu (PDF Dışı Ek Bilgi)` başlığı açılır ve canlı Java kod örneği türetilerek sunulur.

### 📌 Senaryo 3: Peş Peşe Takip Soruları Sorabilme (History-Aware Memory)
* **Kullanıcı:** Zeynep (Araştırmacı)
* **Akış:**
  1. *Soru 1:* *"TCP protokolü nedir?"* -> Yanıt verilir.
  2. *Soru 2:* *"Peki bunun 3 yollu el sıkışma mekanizması nasıl çalışır?"*
* **Sistem Çalışması:**
  1. `rewrite_question_with_history` devreye girer.
  2. *"Peki bunun..."* ifadesini sohbet geçmişinden okuyarak arkada **"TCP protokolünün 3 yollu el sıkışma mekanizması nasıl çalışır?"** şekline dönüştürür.
  3. FAISS ve BM25 aramayı bu net cümleyle yaparak tam doğru sayfayı getirir.

### 📌 Senaryo 4: Kod / Özel Kısaltma Arama (BM25 + FAISS Hybrid Search)
* **Kullanıcı:** Can (Sistem Programcısı)
* **Soru:** *"Sistemde 'DEADLOCK_PREVENTION_V2' algoritması nasıl kurulmuş?"*
* **Sistem Çalışması:**
  1. Vektör araması (FAISS) bu özel kod adını kaçırabilir.
  2. `BM25Retriever` devreye girer ve dokümandaki `"DEADLOCK_PREVENTION_V2"` kelime dizilimini %100 oranında yakalar.
  3. `EnsembleRetriever` iki aramayı harmanlayarak doğru kod bloğunu LLM'e sunar.

---

## 🛠️ 5. Proje Dosya Ağacı ve İşlev Özet Tablosu

| Dosya Adı | Sorumluluk / İşlev |
| :--- | :--- |
| **`app.py`** | Streamlit UI arayüzü, session state kilitleri, canlı chat mesaj akışı ve sayfa referansı expander kartları. |
| **`utils.py`** | Sayfa takipli PDF yükleme, chunking, `all-MiniLM-L6-v2` yerel indeksleme, `BM25 + FAISS` EnsembleRetriever, Sohbet Hafızası soru yeniden yazma ve canlı streaming motoru. |
| **`config.py`** | Model yapılandırmaları (`gemini-2.5-flash`, `all-MiniLM-L6-v2`), RAG ağırlıkları (`0.5 BM25 / 0.5 FAISS`) ve tüm prompt şablonları. |
| **`requirements.txt`** | Proje kütüphane bağımlılıkları (`streamlit`, `langchain`, `faiss-cpu`, `sentence-transformers`, `rank-bm25`). |
| **`tests/`** | Streaming stabilitesi, Sohbet Hafızası fallback'leri ve Hibrit Arama mekanizmasını doğrulayan birim testler. |

---

## 💡 Özet
DocuMate; kullanıcısına **"uydurma bilgi vermeyen"**, **"sayfasını açıkça gösteren"**, **"ister katı sınav yanıtı ister açıklayıcı öğretmen yanıtı verebilen"** ve **"özel kodları/terimleri kaçırmayan"** üretim seviyesinde (production-grade) bir RAG asistanıdır.

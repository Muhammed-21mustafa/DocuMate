"""
RAG Tabanlı Akıllı PDF Asistanı - Streamlit Kullanıcı Arayüzü (UI)
"""

import os
import streamlit as st
from dotenv import load_dotenv

from config import MODE_STRICT, MODE_HYBRID, AVAILABLE_LLM_MODELS, DEFAULT_LLM_MODEL
from utils import (
    load_pdf_with_page_metadata,
    split_documents,
    create_faiss_vector_store,
    create_hybrid_retriever,
    answer_question,
    answer_question_stream,
    is_summary_request,
    generate_full_document_summary_stream
)

# .env dosyasını yükle
load_dotenv()

# Streamlit Sayfa Ayarları
st.set_page_config(
    page_title="RAG Akıllı PDF Asistanı",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Özel CSS Stilleri (Modern & Şık Görünüm)
st.markdown("""
    <style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1E88E5;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #555;
        text-align: center;
        margin-bottom: 2rem;
    }
    .badge-strict {
        background-color: #E3F2FD;
        color: #1565C0;
        padding: 4px 8px;
        border-radius: 4px;
        font-weight: 600;
    }
    .badge-hybrid {
        background-color: #F3E5F5;
        color: #7B1FA2;
        padding: 4px 8px;
        border-radius: 4px;
        font-weight: 600;
    }
    .source-box {
        background-color: #F8F9FA;
        border-left: 4px solid #1E88E5;
        padding: 10px;
        margin-top: 10px;
        border-radius: 4px;
        font-size: 0.9rem;
    }
    </style>
""", unsafe_allow_html=True)

# Oturum Durumları (Session State)
if "messages" not in st.session_state:
    st.session_state.messages = []

if "vector_store" not in st.session_state:
    st.session_state.vector_store = None

if "pdf_chunks" not in st.session_state:
    st.session_state.pdf_chunks = []

if "hybrid_retriever" not in st.session_state:
    st.session_state.hybrid_retriever = None

if "pdf_processed" not in st.session_state:
    st.session_state.pdf_processed = False

if "pdf_stats" not in st.session_state:
    st.session_state.pdf_stats = {"pages": 0, "chunks": 0, "filename": ""}

if "is_generating" not in st.session_state:
    st.session_state.is_generating = False


# --- SOL YAN MENÜ (SIDEBAR) ---
with st.sidebar:
    st.title("⚙️ Ayarlar ve Yükleme")
    
    # 1. API Key Girdisi
    env_api_key = os.getenv("GOOGLE_API_KEY", "")
    api_key = st.text_input(
        "Google Gemini API Key",
        value=env_api_key,
        type="password",
        help="Google AI Studio'dan alacağınız ücretsiz API anahtarınız."
    )
    
    if not api_key:
        st.warning("⚠️ Lütfen devam etmek için Gemini API anahtarınızı girin.")
    
    st.divider()
    
    # 2. PDF Yükleme Alanı
    st.subheader("📄 Doküman Yükleme")
    uploaded_file = st.file_uploader(
        "Bir PDF Dosyası Seçin",
        type=["pdf"],
        help="Sohbet etmek istediğiniz ders notu, kitap veya makaleyi yükleyin."
    )
    
    if uploaded_file and api_key:
        # Eğer yeni bir dosya yüklendiyse veya henüz işlenmediyse
        if st.session_state.pdf_stats["filename"] != uploaded_file.name:
            with st.spinner("PDF ayrıştırılıyor ve hibrit vektör indeksleri oluşturuluyor..."):
                try:
                    # PDF Yükle & Sayfa Sayısını Al
                    docs, total_pages = load_pdf_with_page_metadata(uploaded_file)
                    
                    # Chunking
                    chunks = split_documents(docs)
                    
                    # Vektör Veritabanı (FAISS)
                    vector_store = create_faiss_vector_store(chunks, api_key)
                    
                    # Hybrid Retriever (BM25 + FAISS Ensemble)
                    hybrid_retriever = create_hybrid_retriever(chunks, vector_store)
                    
                    # State Güncelle
                    st.session_state.vector_store = vector_store
                    st.session_state.hybrid_retriever = hybrid_retriever
                    st.session_state.pdf_chunks = chunks
                    st.session_state.pdf_processed = True
                    st.session_state.pdf_stats = {
                        "pages": total_pages,
                        "chunks": len(chunks),
                        "filename": uploaded_file.name
                    }
                    st.session_state.messages = []  # Yeni PDF için sohbeti sıfırla
                    st.success("✅ PDF hibrit indeks ile başarıyla yüklendi!")
                except Exception as e:
                    st.error(f"Hata oluştu: {str(e)}")
                    
    # Doküman İstatistikleri
    if st.session_state.pdf_processed:
        st.info(
            f"**Doküman:** {st.session_state.pdf_stats['filename']}\n\n"
            f"📄 **Sayfa Sayısı:** {st.session_state.pdf_stats['pages']}\n\n"
            f"🧩 **Chunk Sayısı:** {st.session_state.pdf_stats['chunks']}"
        )
        
    st.divider()
    
    # 3. Çift Modlu RAG Seçimi
    st.subheader("🎛️ RAG Çalışma Modu")
    selected_mode_label = st.radio(
        "Mod Seçiniz:",
        options=[
            "🎯 Katı Sınav Modu (Sadece PDF)",
            "🧠 Öğretmen / Hibrit Mod (PDF + Ek Örnekler)"
        ],
        help="Katı Mod: Sadece PDF'teki bilgilere dayanır. Hibrit Mod: Eksik kalan yerlerde PDF dışı açıklayıcı örnekler sunar."
    )
    
    current_mode = MODE_STRICT if "Katı" in selected_mode_label else MODE_HYBRID
    
    st.divider()
    
    # 4. LLM Model Seçimi
    st.subheader("🤖 LLM Modeli")
    selected_llm_model = st.selectbox(
        "Model Seçiniz:",
        options=AVAILABLE_LLM_MODELS,
        index=0,
        help="Yanıt üretirken kullanılacak Google Gemini modeli."
    )
    
    st.divider()
    
    # 5. Sohbeti Temizle
    if st.button("🧹 Sohbet Geçmişini Temizle", use_container_width=True):
        st.session_state.messages = []
        st.rerun()


# --- ANA EKRAN ---
st.markdown('<div class="main-header">📚 RAG Tabanlı Akıllı PDF Asistanı</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Dokümanlarınızla güvenle sohbet edin • Sayfa referanslı yanıtlar • Halüsinasyon önleyici mimari</div>', unsafe_allow_html=True)

# Aktif Mod Göstergesi
col_mode, col_space = st.columns([2, 5])
with col_mode:
    if current_mode == MODE_STRICT:
        st.markdown('<span class="badge-strict">🎯 Aktif Mod: Katı Sınav Modu (Sadece PDF)</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="badge-hybrid">🧠 Aktif Mod: Öğretmen / Hibrit Mod (PDF + Ek Bilgi)</span>', unsafe_allow_html=True)

st.write("")

# Doküman Yüklenmediyse Bilgilendirme Kartı Göster
if not st.session_state.pdf_processed:
    st.info("""
    ### 👋 Hoş Geldiniz!
    Başlamak için lütfen sol menüden:
    1. **Gemini API Key** anahtarınızı girin.
    2. Çalışmak istediğiniz **PDF dosyasını** yükleyin.
    3. İhtiyacınıza uygun **RAG Çalışma Modunu** seçip sorularınızı sorun!
    """)
else:
    # Sohbet Geçmişini Listele
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            
            # Eğer yanıt asistan tarafından verildiyse ve kaynaklar varsa göster
            if message["role"] == "assistant" and "sources" in message:
                with st.expander("📌 Yanıtta Kullanılan Kaynaklar ve Sayfalar"):
                    for idx, doc in enumerate(message["sources"], 1):
                        page_num = doc.metadata.get("page", "Bilinmiyor")
                        st.markdown(f"**Kaynak {idx} (Sayfa {page_num}):**")
                        st.caption(f"_{doc.page_content.strip()}_")
                        st.divider()

    # Kullanıcı Girdisi Alanı (Yanıt üretilirken kilitlenir)
    if user_prompt := st.chat_input(
        "PDF içeriği hakkında bir soru sorun...",
        disabled=st.session_state.is_generating
    ):
        if not api_key:
            st.error("Lütfen önce sol panelden API anahtarınızı girin.")
        else:
            # Kullanıcı mesajını ekle
            st.session_state.messages.append({"role": "user", "content": user_prompt})
            with st.chat_message("user"):
                st.markdown(user_prompt)

            # Asistan yanıtını canlı stream ile üret
            st.session_state.is_generating = True
            with st.chat_message("assistant"):
                try:
                    if is_summary_request(user_prompt):
                        with st.spinner("Dokümanın tüm bölümleri taranıyor ve Map-Reduce özet oluşturuluyor..."):
                            stream_gen, sources = generate_full_document_summary_stream(
                                chunks=st.session_state.pdf_chunks,
                                api_key=api_key,
                                llm_model=selected_llm_model
                            )
                    else:
                        stream_gen, sources = answer_question_stream(
                            vector_store=st.session_state.vector_store,
                            query=user_prompt,
                            api_key=api_key,
                            mode=current_mode,
                            llm_model=selected_llm_model,
                            chat_history=st.session_state.messages[:-1],
                            retriever=st.session_state.hybrid_retriever
                        )
                    
                    # Canlı Metin Akışı (Streaming)
                    full_response = st.write_stream(stream_gen)
                    
                    # Kaynakları Göster
                    if sources:
                        with st.expander("📌 Yanıtta Kullanılan Kaynaklar ve Sayfalar"):
                            for idx, doc in enumerate(sources, 1):
                                page_num = doc.metadata.get("page", "Bilinmiyor")
                                st.markdown(f"**Kaynak {idx} (Sayfa {page_num}):**")
                                st.caption(f"_{doc.page_content.strip()}_")
                                st.divider()
                                
                    # Mesajı ve kaynakları geçmişe kaydet
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": full_response,
                        "sources": sources
                    })
                except Exception as e:
                    st.error(f"Yanıt üretilirken bir hata oluştu: {str(e)}")
                finally:
                    st.session_state.is_generating = False

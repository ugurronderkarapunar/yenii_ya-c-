import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import io

st.set_page_config(page_title="Gemi Yağcı Ordino Planlayıcı", layout="wide")

# Türkçe Gün İsimleri
GUNLER = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]

st.title("🚢 Gemi Yağcı Ordino & İkame Planlayıcı (Dinamik Excel Yükleme)")
st.markdown("Kendi Excel dosyanızı yükleyerek kurallara en uygun 4 ikame personeli listeleyebilir ve güncel ordino planını Excel olarak indirebilirsiniz.")

# --- KENAR ÇUCUĞU: EXCEL DOSYA YÜKLEME ---
st.sidebar.header("📁 Veri Yönetimi")
uploaded_file = st.sidebar.file_uploader(
    "Excel Dosyanızı Yükleyin (.xlsx)", 
    type=["xlsx"],
    help="İçinde 'Personel', 'Vardiya_ve_Izin' ve 'Gecmis_Cekilme' sayfaları olan Excel dosyanızı yükleyin."
)

# Örnek Şablon Oluşturma ve İndirme Butonu
def create_sample_excel():
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        pd.DataFrame([
            {"Personel": "Uğur", "Statu": "Sabit", "Gemi": "Beykoz", "Makineler": "MTU, Caterpillar", "Haftalik_Izin": "Perşembe"},
            {"Personel": "Ahmet", "Statu": "İzinci", "Gemi": "Yedek", "Makineler": "MTU, Caterpillar, Baudouin", "Haftalik_Izin": "Pazar"},
            {"Personel": "Mehmet", "Statu": "İzinci", "Gemi": "Yedek", "Makineler": "Caterpillar, Wartsila", "Haftalik_Izin": "Salı"},
            {"Personel": "Can", "Statu": "8-5", "Gemi": "Beşiktaş", "Makineler": "MTU, Caterpillar", "Haftalik_Izin": "Cumartesi"},
            {"Personel": "Emre", "Statu": "İzinci", "Gemi": "Yedek", "Makineler": "MTU, Baudouin", "Haftalik_Izin": "Çarşamba"},
            {"Personel": "Burak", "Statu": "8-5", "Gemi": "Karaköy", "Makineler": "MTU, Caterpillar", "Haftalik_Izin": "Pazar"},
            {"Personel": "Selim", "Statu": "İzinci", "Gemi": "Yedek", "Makineler": "Wartsila", "Haftalik_Izin": "Cuma"},
            {"Personel": "Murat", "Statu": "Sabit", "Gemi": "Kadıköy", "Makineler": "MTU, Caterpillar", "Haftalik_Izin": "Pazartesi"},
        ]).to_excel(writer, sheet_name="Personel", index=False)

        bugun = datetime.now().strftime("%Y-%m-%d")
        pd.DataFrame([
            {"Tarih": bugun, "Personel": "Uğur", "Durum": "İzinli", "Vardiya": "Pzt-Çar-Cum", "Gemi": "Beykoz"},
            {"Tarih": bugun, "Personel": "Ahmet", "Durum": "Müsait", "Vardiya": "Yok", "Gemi": "Yedek"},
            {"Tarih": bugun, "Personel": "Mehmet", "Durum": "Müsait", "Vardiya": "Yok", "Gemi": "Yedek"},
            {"Tarih": bugun, "Personel": "Can", "Durum": "Çalışıyor", "Vardiya": "08-17", "Gemi": "Beşiktaş"},
            {"Tarih": bugun, "Personel": "Emre", "Durum": "Vardiya Çıkışı", "Vardiya": "Gece Çıkışı", "Gemi": "Yedek"},
            {"Tarih": bugun, "Personel": "Burak", "Durum": "Çalışıyor", "Vardiya": "08-17", "Gemi": "Karaköy"},
            {"Tarih": bugun, "Personel": "Selim", "Durum": "Müsait", "Vardiya": "Yok", "Gemi": "Yedek"},
            {"Tarih": bugun, "Personel": "Murat", "Durum": "Çalışıyor", "Vardiya": "Sabit", "Gemi": "Kadıköy"},
        ]).to_excel(writer, sheet_name="Vardiya_ve_Izin", index=False)

        pd.DataFrame([
            {"Personel": "Burak", "Cekildigi_Gemi": "Beykoz"},
        ]).to_excel(writer, sheet_name="Gecmis_Cekilme", index=False)
    return output.getvalue()

st.sidebar.download_button(
    label="📥 Örnek Excel Şablonunu İndir",
    data=create_sample_excel(),
    file_name="ornek_ordino_sablonu.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

# --- VERİLERİ OKUMA ---
@st.cache_data
def load_data_from_buffer(file_buffer):
    p_df = pd.read_excel(file_buffer, sheet_name="Personel")
    v_df = pd.read_excel(file_buffer, sheet_name="Vardiya_ve_Izin")
    g_df = pd.read_excel(file_buffer, sheet_name="Gecmis_Cekilme")
    return p_df, v_df, g_df

if uploaded_file is not None:
    try:
        personel_df, vardiya_df, gecmis_df = load_data_from_buffer(uploaded_file)
        st.sidebar.success("✅ Excel dosyanız başarıyla yüklendi!")
    except Exception as e:
        st.sidebar.error(f"Hata: Excel sayfaları okunamadı. ('Personel', 'Vardiya_ve_Izin', 'Gecmis_Cekilme' sayfaları olduğundan emin olun)\n{e}")
        st.stop()
else:
    default_buffer = create_sample_excel()
    personel_df, vardiya_df, gecmis_df = load_data_from_buffer(io.BytesIO(default_buffer))
    st.sidebar.info("💡 Örnek verilerle çalışılıyor (kendi dosyanızı yükleyebilirsiniz).")

# --- ALGORİTMA: EN UYGUN 4 ADAYI BUL (Parametreler sabitlendi) ---
def en_uygun_adaylari_bul(hedef_gemi, gerekli_makine, tarih_str):
    secilen_tarih = datetime.strptime(tarih_str, "%Y-%m-%d")
    gun_adi = GUNLER[secilen_tarih.weekday()]
    
    adaylar = []

    for _, row in personel_df.iterrows():
        ad = str(row["Personel"])
        statu = str(row["Statu"])
        bildigi_makineler = [m.strip().lower() for m in str(row["Makineler"]).split(",")]
        haftalik_izin = str(row["Haftalik_Izin"]).strip()

        # 1. KURAL: Sabit personel başka gemiye kaydırılmaz
        if statu.lower() == "sabit":
            continue

        # 2. KURAL: Makine Bilgisi Eşleşmesi
        if gerekli_makine.lower() not in bildigi_makineler:
            continue

        # 3. KURAL: Haftalık İzin Kontrolü
        if haftalik_izin.lower() == gun_adi.lower():
            continue

        # 4. KURAL: Daha önce hedef gemiden çekilmemiş olacak
        cekilmis_mi = not gecmis_df[(gecmis_df["Personel"].astype(str) == ad) & (gecmis_df["Cekildigi_Gemi"].astype(str) == hedef_gemi)].empty
        if cekilmis_mi:
            continue

        # 5. KURAL: Günlük Durum Kontrolü (İzinde veya Vardiya Çıkışında olmayacak)
        gunluk_kayit = vardiya_df[(vardiya_df["Personel"].astype(str) == ad) & (vardiya_df["Tarih"].astype(str) == tarih_str)]
        durum = "Müsait"
        if not gunluk_kayit.empty:
            durum = str(gunluk_kayit.iloc[0]["Durum"])
            if durum in ["İzinli", "Vardiya Çıkışı", "Haftalık İzin"]:
                continue

        # --- PUANLAMA ---
        puan = 0
        aciklama = []

        if statu.lower() == "izinci":
            puan += 100
            aciklama.append("Asli görev: İzinci (+100)")
        elif statu.lower() == "8-5":
            puan += 50
            aciklama.append("8-5 Personeli - Kaydırılabilir (+50)")

        if durum == "Müsait":
            puan += 20
            aciklama.append("O gün müsait (+20)")

        adaylar.append({
            "Personel": ad,
            "Statü": statu,
            "Mevcut Gemi": row["Gemi"],
            "Bildiği Makineler": row["Makineler"],
            "Haftalık İzin": haftalik_izin,
            "O Günkü Durum": durum,
            "Uygunluk Puanı": puan,
            "Seçim Nedeni": " | ".join(aciklama)
        })

    sonuc_df = pd.DataFrame(adaylar)
    if not sonuc_df.empty:
        sonuc_df = sonuc_df.sort_values(by="Uygunluk Puanı", ascending=False).head(4)
    return sonuc_df

# --- ARAYÜZ (UI) ---
col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("1. İzin / Eksik Bilgisi")
    izinli_kisi = st.selectbox("İzin Alan Personel", personel_df["Personel"].tolist())
    kisi_bilgi = personel_df[personel_df["Personel"] == izinli_kisi].iloc[0]
    
    hedef_gemi = st.text_input("Görev Yeri (Gemi)", value=str(kisi_bilgi["Gemi"]))
    gemi_makinesi = st.selectbox("Gemi Makine Tipi", ["MTU", "Caterpillar", "Baudouin", "Wartsila"])
    plan_tarihi = st.date_input("Planlama Tarihi", value=datetime.now())
    
    st.info(f"**Seçilen Personel Statüsü:** {kisi_bilgi['Statu']} | **Haftalık İzni:** {kisi_bilgi['Haftalik_Izin']}")

with col2:
    st.subheader("2. Önerilen En Uygun 4 Aday")
    if st.button("Uygun Personelleri Bul", type="primary"):
        # Doğru argümanlar ile fonksiyon çağrısı
        oneriler = en_uygun_adaylari_bul(
            hedef_gemi=hedef_gemi,
            gemi_makinesi=gemi_makinesi,
            tarih_str=plan_tarihi.strftime("%Y-%m-%d")
        )
        
        if oneriler.empty:
            st.error("Belirtilen kriterlere uygun boşta personel bulunamadı!")
        else:
            st.success(f"**{hedef_gemi}** gemisi için en uygun {len(oneriler)} aday listelenmiştir:")
            st.dataframe(oneriler, use_container_width=True, hide_index=True)

            st.markdown("---")
            st.subheader("3. Ordino Onayı ve Dışa Aktarım")
            secilen_ikame = st.selectbox("Gemiye Gönderilecek Personeli Seçin:", oneriler["Personel"].tolist())
            
            if st.button("Güncel Ordino Raporunu Excel Olarak İndir"):
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine="openpyxl") as writer:
                    rapor_df = pd.DataFrame([{
                        "Planlama Tarihi": plan_tarihi.strftime("%Y-%m-%d"),
                        "İzin Alan Personel": izinli_kisi,
                        "Görev Yeri (Gemi)": hedef_gemi,
                        "Makine Tipi": gemi_makinesi,
                        "Atanan İkame Personel": secilen_ikame,
                        "Durum": "Onaylandı"
                    }])
                    rapor_df.to_excel(writer, sheet_name="Atama_Sonucu", index=False)
                    oneriler.to_excel(writer, sheet_name="Aday_Degerlendirme_Listesi", index=False)
                    personel_df.to_excel(writer, sheet_name="Guncel_Personel", index=False)
                
                processed_data = output.getvalue()
                
                st.download_button(
                    label="📥 Excel Raporunu İndir (.xlsx)",
                    data=processed_data,
                    file_name=f"Ordino_Raporu_{plan_tarihi.strftime('%Y%m%d')}_{hedef_gemi}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
                st.success(f"✅ {secilen_ikame}, {hedef_gemi} gemisi için başarıyla atandı ve rapor hazırlandı!")

st.divider()
with st.expander("📊 Yüklü Veri Tablolarını İncele"):
    t1, t2, t3 = st.tabs(["Personel Listesi", "Günlük Vardiya & İzin", "Geçmiş Gemi Çekilme"])
    with t1:
        st.dataframe(personel_df, use_container_width=True)
    with t2:
        st.dataframe(vardiya_df, use_container_width=True)
    with t3:
        st.dataframe(gecmis_df, use_container_width=True)

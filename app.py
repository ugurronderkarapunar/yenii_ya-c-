import streamlit as st
import pandas as pd
from datetime import datetime
import io

st.set_page_config(page_title="Gemi Yağcı Ordino & İkame Planlayıcı", layout="wide")

GUNLER = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]

st.title("🚢 Gemi Yağcı Ordino & İkame Planlayıcı (Kapsamlı Modül)")
st.markdown("Personel, Gemi Makineleri, Kaptan/Baş Makinist ve Rapor/Sicil kurallarına göre en uygun ikame planlaması.")

# --- KENAR ÇUCUĞU: EXCEL YÖNETİMİ ---
st.sidebar.header("📁 Veri Yönetimi")
uploaded_file = st.sidebar.file_uploader(
    "Excel Dosyanızı Yükleyin (.xlsx)", 
    type=["xlsx"],
    help="Personel, Gemiler, Gemi_Makineleri, Vardiya_ve_Izin, Gemi_Gecmisi, Raporlar sayfalarını içeren dosya."
)

# Kapsamlı Örnek Şablon Üretici
def create_comprehensive_excel():
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        # 1. Personel Sayfası
        pd.DataFrame([
            {"Ad_Soyad": "Uğur Önder", "Sicil_No": "1001", "Statu": "Sabit", "Bildigi_Gemiler": "Beykoz, Kadıköy", "Vardiya_Gunleri": "Pazartesi, Çarşamba, Cuma", "Haftalik_Izin": "Perşembe", "Vardiya_Tipi": "08-16"},
            {"Ad_Soyad": "Ahmet Yılmaz", "Sicil_No": "1002", "Statu": "İzinci", "Bildigi_Gemiler": "Beykoz, Beşiktaş, Karaköy", "Vardiya_Gunleri": "Hergün", "Haftalik_Izin": "Pazar", "Vardiya_Tipi": "Vardiyalı"},
            {"Ad_Soyad": "Mehmet Demir", "Sicil_No": "1003", "Statu": "İzinci", "Bildigi_Gemiler": "Beykoz, Kadıköy", "Vardiya_Gunleri": "Hergün", "Haftalik_Izin": "Salı", "Vardiya_Tipi": "Vardiyalı"},
            {"Ad_Soyad": "Can Kaya", "Sicil_No": "1004", "Statu": "8-5", "Bildigi_Gemiler": "Beykoz, Beşiktaş", "Vardiya_Gunleri": "Pazartesi-Cuma", "Haftalik_Izin": "Cumartesi", "Vardiya_Tipi": "08-17"},
            {"Ad_Soyad": "Emre Şahin", "Sicil_No": "1005", "Statu": "İzinci", "Bildigi_Gemiler": "Karaköy, Kadıköy", "Vardiya_Gunleri": "Hergün", "Haftalik_Izin": "Çarşamba", "Vardiya_Tipi": "Vardiyalı"},
        ]).to_excel(writer, sheet_name="Personel", index=False)

        # 2. Gemi Makineleri Sayfası
        pd.DataFrame([
            {"Makine_Adi": "MTU 16V"},
            {"Makine_Adi": "Caterpillar 3512"},
            {"Makine_Adi": "Baudouin 12M"},
            {"Makine_Adi": "Wartsila 6L20"}
        ]).to_excel(writer, sheet_name="Gemi_Makineleri", index=False)

        # 3. Gemiler Sayfası
        pd.DataFrame([
            {"Gemi_Adi": "Beykoz", "Makine_Bilgisi": "MTU 16V", "Konum": "Haliç Tersanesi"},
            {"Gemi_Adi": "Beşiktaş", "Makine_Bilgisi": "Caterpillar 3512", "Konum": "Karaköy İskelesi"},
            {"Gemi_Adi": "Kadıköy", "Makine_Bilgisi": "Baudouin 12M", "Konum": "Kadıköy İskelesi"},
            {"Gemi_Adi": "Karaköy", "Makine_Bilgisi": "Wartsila 6L20", "Konum": "Beşiktaş İskelesi"}
        ]).to_excel(writer, sheet_name="Gemiler", index=False)

        # 4. Gemi Kaptan & Baş Makinist Bilgileri
        pd.DataFrame([
            {"Gemi_Adi": "Beykoz", "Tarih": "2026-06-06", "Kaptan": "Ali Reis", "Bas_Makinist": "Hasan Baş Mühendis"},
            {"Gemi_Adi": "Beşiktaş", "Tarih": "2026-06-06", "Kaptan": "Kemal Reis", "Bas_Makinist": "Orhan Baş Mühendis"}
        ]).to_excel(writer, sheet_name="Gemi_Kaptan_Bas_Mak", index=False)

        # 5. Vardiya ve İzin Durumları
        bugun = datetime.now().strftime("%Y-%m-%d")
        pd.DataFrame([
            {"Tarih": bugun, "Ad_Soyad": "Uğur Önder", "Durum": "İzinli"},
            {"Tarih": bugun, "Ad_Soyad": "Ahmet Yılmaz", "Durum": "Müsait"},
            {"Tarih": bugun, "Ad_Soyad": "Mehmet Demir", "Durum": "Müsait"},
            {"Tarih": bugun, "Ad_Soyad": "Can Kaya", "Durum": "Çalışıyor"},
            {"Tarih": bugun, "Ad_Soyad": "Emre Şahin", "Durum": "Vardiya Çıkışı"}
        ]).to_excel(writer, sheet_name="Vardiya_ve_Izin", index=False)

        # 6. Gemi Geçmişi (Daha önce hangi gemilerde çalıştı - O gemiyi bilmiş olacak)
        pd.DataFrame([
            {"Ad_Soyad": "Ahmet Yılmaz", "Gemi_Adi": "Beykoz"},
            {"Ad_Soyad": "Mehmet Demir", "Gemi_Adi": "Beykoz"},
            {"Ad_Soyad": "Can Kaya", "Gemi_Adi": "Beykoz"},
            {"Ad_Soyad": "Emre Şahin", "Gemi_Adi": "Kadıköy"}
        ]).to_excel(writer, sheet_name="Gemi_Gecmisi", index=False)

        # 7. Rapor / Disiplin Cezası Tablosu (Kaptan veya Baş Makinitten rapor yemiş olanlar)
        pd.DataFrame([
            # Örn: Emre Şahin Karaköy'de rapor yemiş
            {"Ad_Soyad": "Emre Şahin", "Gemi_Adi": "Beykoz", "Rapor_Durumu": "Yok"}
        ]).to_excel(writer, sheet_name="Raporlar", index=False)

    return output.getvalue()

st.sidebar.download_button(
    label="📥 Kapsamlı Örnek Excel Şablonunu İndir",
    data=create_comprehensive_excel(),
    file_name="kapsamli_ordino_sablonu.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

# --- VERİLERİ OKUMA ---
@st.cache_data
def load_data(file_buffer):
    p_df = pd.read_excel(file_buffer, sheet_name="Personel")
    g_df = pd.read_excel(file_buffer, sheet_name="Gemiler")
    m_df = pd.read_excel(file_buffer, sheet_name="Gemi_Makineleri")
    v_df = pd.read_excel(file_buffer, sheet_name="Vardiya_ve_Izin")
    gec_df = pd.read_excel(file_buffer, sheet_name="Gemi_Gecmisi")
    rap_df = pd.read_excel(file_buffer, sheet_name="Raporlar")
    return p_df, g_df, m_df, v_df, gec_df, rap_df

if uploaded_file is not None:
    try:
        personel_df, gemiler_df, makineler_df, vardiya_df, gemi_gecmisi_df, raporlar_df = load_data(uploaded_file)
        st.sidebar.success("✅ Excel dosyanız başarıyla yüklendi!")
    except Exception as e:
        st.sidebar.error(f"Excel sayfaları okunurken hata oluştu: {e}")
        st.stop()
else:
    default_buffer = create_comprehensive_excel()
    personel_df, gemiler_df, makineler_df, vardiya_df, gemi_gecmisi_df, raporlar_df = load_data(io.BytesIO(default_buffer))
    st.sidebar.info("💡 Örnek veri seti ile çalışılıyor.")

# --- ÖNERİ ALGORİTMASI ---
def en_uygun_adaylari_bul(hedef_gemi, tarih_str):
    secilen_tarih = datetime.strptime(tarih_str, "%Y-%m-%d")
    gun_adi = GUNLER[secilen_tarih.weekday()]
    
    # Hedef geminin makine bilgisini bul
    gemi_row = gemiler_df[gemiler_df["Gemi_Adi"].astype(str) == hedef_gemi]
    gemi_makinesi = gemi_row.iloc[0]["Makine_Bilgisi"] if not gemi_row.empty else ""

    adaylar = []

    for _, row in personel_df.iterrows():
        ad = str(row["Ad_Soyad"])
        statu = str(row["Statu"])
        bildigi_gemiler = [g.strip().lower() for g in str(row["Bildigi_Gemiler"]).split(",")]
        haftalik_izin = str(row["Haftalik_Izin"]).strip()

        # 1. KURAL: Sabit personel başka gemiye kaydırılmaz
        if statu.lower() == "sabit":
            continue

        # 2. KURAL: O gemiyi bilmiş olacak (Daha önce o gemide çalışmış mı?)
        daha_once_calisti_mi = not gemi_gecmisi_df[
            (gemi_gecmisi_df["Ad_Soyad"].astype(str) == ad) & 
            (gemi_gecmisi_df["Gemi_Adi"].astype(str).str.lower() == hedef_gemi.lower())
        ].empty

        if not daha_once_calisti_mi:
            continue

        # 3. KURAL: Haftalık İzin Kontrolü (O gün haftaizni var mı?)
        if haftalik_izin.lower() == gun_adi.lower():
            continue

        # 4. KURAL: Günlük Durum Kontrolü (İzinde veya Vardiya Çıkışında olmayacak)
        gunluk_kayit = vardiya_df[(vardiya_df["Ad_Soyad"].astype(str) == ad) & (vardiya_df["Tarih"].astype(str) == tarih_str)]
        durum = "Müsait"
        if not gunluk_kayit.empty:
            durum = str(gunluk_kayit.iloc[0]["Durum"])
            if durum in ["İzinli", "Vardiya Çıkışı", "Haftalık İzin"]:
                continue

        # 5. KURAL: Kaptan ya da Baş Makinitten Rapor / Cezası Olmayacak
        ceza_var_mi = not raporlar_df[
            (raporlar_df["Ad_Soyad"].astype(str) == ad) & 
            (raporlar_df["Gemi_Adi"].astype(str).str.lower() == hedef_gemi.lower()) &
            (raporlar_df["Rapor_Durumu"].astype(str).str.lower() != "yok")
        ].empty

        if ceza_var_mi:
            continue

        # --- PUANLAMA ---
        puan = 0
        aciklama = []

        if statu.lower() == "izinci":
            puan += 100
            aciklama.append("Asli İzinci (+100)")
        elif statu.lower() == "8-5":
            puan += 50
            aciklama.append("8-5 Kaydırılabilir (+50)")

        if daha_once_calisti_mi:
            puan += 30
            aciklama.append("Gemiyi biliyor (+30)")

        if durum == "Müsait":
            puan += 20
            aciklama.append("O gün müsait (+20)")

        adaylar.append({
            "Personel": ad,
            "Sicil No": row["Sicil_No"],
            "Statü": statu,
            "Vardiya Tipi": row

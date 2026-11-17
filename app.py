import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os

st.set_page_config(page_title="Gemi Yağcı Ordino Planlayıcı", layout="wide")

EXCEL_FILE = "ordino_verisi.xlsx"

# --- ÖRNEK VERİ OLUŞTURUCU (Dosya yoksa otomatik oluşturur) ---
def init_excel():
    if not os.path.exists(EXCEL_FILE):
        personel_df = pd.DataFrame([
            {"Personel": "Uğur", "Statu": "Sabit", "Gemi": "Beykoz", "Makineler": "MTU, Caterpillar", "Haftalik_Izin": "Perşembe"},
            {"Personel": "Ahmet", "Statu": "İzinci", "Gemi": "Yedek", "Makineler": "MTU, Caterpillar, Baudouin", "Haftalik_Izin": "Pazar"},
            {"Personel": "Mehmet", "Statu": "İzinci", "Gemi": "Yedek", "Makineler": "Caterpillar, Wartsila", "Haftalik_Izin": "Salı"},
            {"Personel": "Can", "Statu": "8-5", "Gemi": "Beşiktaş", "Makineler": "MTU, Caterpillar", "Haftalik_Izin": "Cumartesi"},
            {"Personel": "Emre", "Statu": "İzinci", "Gemi": "Yedek", "Makineler": "MTU, Baudouin", "Haftalik_Izin": "Çarşamba"},
            {"Personel": "Burak", "Statu": "8-5", "Gemi": "Karaköy", "Makineler": "MTU, Caterpillar", "Haftalik_Izin": "Pazar"},
            {"Personel": "Selim", "Statu": "İzinci", "Gemi": "Yedek", "Makineler": "Wartsila", "Haftalik_Izin": "Cuma"},
            {"Personel": "Murat", "Statu": "Sabit", "Gemi": "Kadıköy", "Makineler": "MTU, Caterpillar", "Haftalik_Izin": "Pazartesi"},
        ])

        # Bugün ve yarın için örnek vardiya/izin durumu
        bugun = datetime.now().strftime("%Y-%m-%d")
        vardiya_df = pd.DataFrame([
            {"Tarih": bugun, "Personel": "Uğur", "Durum": "İzinli", "Vardiya": "Pzt-Çar-Cum", "Gemi": "Beykoz"},
            {"Tarih": bugun, "Personel": "Ahmet", "Durum": "Müsait", "Vardiya": "Yok", "Gemi": "Yedek"},
            {"Tarih": bugun, "Personel": "Mehmet", "Durum": "Müsait", "Vardiya": "Yok", "Gemi": "Yedek"},
            {"Tarih": bugun, "Personel": "Can", "Durum": "Çalışıyor", "Vardiya": "08-17", "Gemi": "Beşiktaş"},
            {"Tarih": bugun, "Personel": "Emre", "Durum": "Vardiya Çıkışı", "Vardiya": "Gece Çıkışı", "Gemi": "Yedek"},
            {"Tarih": bugun, "Personel": "Burak", "Durum": "Çalışıyor", "Vardiya": "08-17", "Gemi": "Karaköy"},
            {"Tarih": bugun, "Personel": "Selim", "Durum": "Müsait", "Vardiya": "Yok", "Gemi": "Yedek"},
            {"Tarih": bugun, "Personel": "Murat", "Durum": "Çalışıyor", "Vardiya": "Sabit", "Gemi": "Kadıköy"},
        ])

        gecmis_df = pd.DataFrame([
            {"Personel": "Burak", "Cekildigi_Gemi": "Beykoz"}, # Burak daha önce Beykoz'dan çekilmiş
        ])

        with pd.ExcelWriter(EXCEL_FILE, engine="openpyxl") as writer:
            personel_df.to_excel(writer, sheet_name="Personel", index=False)
            vardiya_df.to_excel(writer, sheet_name="Vardiya_ve_Izin", index=False)
            gecmis_df.to_excel(writer, sheet_name="Gecmis_Cekilme", index=False)

init_excel()

# --- VERİLERİ YÜKLE ---
@st.cache_data
def load_data():
    p_df = pd.read_excel(EXCEL_FILE, sheet_name="Personel")
    v_df = pd.read_excel(EXCEL_FILE, sheet_name="Vardiya_ve_Izin")
    g_df = pd.read_excel(EXCEL_FILE, sheet_name="Gecmis_Cekilme")
    return p_df, v_df, g_df

personel_df, vardiya_df, gecmis_df = load_data()

# Türkçe Gün İsimleri
GUNLER = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]

# --- ALGORİTMA: EN UYGUN 4 ADAYI BUL ---
def en_uygun_adaylari_bul(hedef_gemi, gerekli_makine, tarih_str, izinli_personel_statu):
    secilen_tarih = datetime.strptime(tarih_str, "%Y-%m-%d")
    gun_adi = GUNLER[secilen_tarih.weekday()]
    
    adaylar = []

    for _, row in personel_df.iterrows():
        ad = row["Personel"]
        statu = row["Statu"]
        bildigi_makineler = [m.strip().lower() for m in str(row["Makineler"]).split(",")]
        haftalik_izin = str(row["Haftalik_Izin"]).strip()

        # 1. KURAL: Sabit personel başka gemiye kaydırılmaz (Sadece İzinci veya 8-5 değerlendirilir)
        if statu == "Sabit":
            continue

        # Eğer izin alan kişi 8-5 ise yerine İzinci veya başka bir 8-5 gidebilir.
        # Eğer izin alan kişi Sabit ise öncelik İzinci'dir, yetmezse 8-5 kaydırılabilir.

        # 2. KURAL: Makine Bilgisi Eşleşmesi
        if gerekli_makine.lower() not in bildigi_makineler:
            continue

        # 3. KURAL: Haftalık İzin Kontrolü
        if haftalik_izin.lower() == gun_adi.lower():
            continue

        # 4. KURAL: Daha önce hedef gemiden çekilmemiş olacak
        cekilmis_mi = not gecmis_df[(gecmis_df["Personel"] == ad) & (gecmis_df["Cekildigi_Gemi"] == hedef_gemi)].empty
        if cekilmis_mi:
            continue

        # 5. KURAL: Günlük Durum Kontrolü (İzinde veya Vardiya Çıkışında olmayacak)
        gunluk_kayit = vardiya_df[(vardiya_df["Personel"] == ad) & (vardiya_df["Tarih"] == tarih_str)]
        durum = "Müsait"
        if not gunluk_kayit.empty:
            durum = gunluk_kayit.iloc[0]["Durum"]
            if durum in ["İzinli", "Vardiya Çıkışı", "Haftalık İzin"]:
                continue

        # --- PUANLAMA SİSTEMİ (Önceliklendirme) ---
        puan = 0
        aciklama = []

        # İzinci personel her zaman 1. önceliktir
        if statu == "İzinci":
            puan += 100
            aciklama.append("Asli görevi İzinci (+100)")
        elif statu == "8-5":
            puan += 50
            aciklama.append("8-5 Personeli - Kaydırılabilir (+50)")

        if durum == "Müsait":
            puan += 20
            aciklama.append("O gün boşta/müsait (+20)")

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

# --- ARAYÜZ (STREAMLIT UI) ---
st.title("🚢 Gemi Yağcı Ordino & İkame Planlayıcı")
st.markdown("İzin alan yağcının yerine kurallara en uygun **4 ikame personeli** otomatik listeler.")

col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("1. İzin / Eksik Bilgisi")
    izinli_kisi = st.selectbox("İzin Alan Personel", personel_df["Personel"].tolist())
    kisi_bilgi = personel_df[personel_df["Personel"] == izinli_kisi].iloc[0]
    
    hedef_gemi = st.text_input("Görev Yeri (Gemi)", value=kisi_bilgi["Gemi"])
    gemi_makinesi = st.selectbox("Gemi Makine Tipi", ["MTU", "Caterpillar", "Baudouin", "Wartsila"])
    plan_tarihi = st.date_input("Planlama Tarihi", value=datetime.now())
    
    st.info(f"**Seçilen Personel Statüsü:** {kisi_bilgi['Statu']} | **Haftalık İzni:** {kisi_bilgi['Haftalik_Izin']}")

with col2:
    st.subheader("2. Önerilen En Uygun 4 Aday")
    if st.button("Uygun Personelleri Bul", type="primary"):
        oneriler = en_uygun_adaylari_bul(
            hedef_gemi=hedef_gemi,
            gemi_makinesi=gemi_makinesi,
            tarih_str=plan_tarihi.strftime("%Y-%m-%d"),
            izinli_personel_statu=kisi_bilgi["Statu"]
        )
        
        if oneriler.empty:
            st.error("Belirtilen kriterlere uygun boşta personel bulunamadı!")
        else:
            st.success(f"**{hedef_gemi}** gemisi (**{gemi_makinesi}** makine) için en uygun {len(oneriler)} aday:")
            st.dataframe(oneriler, use_container_width=True, hide_index=True)

            # Ordino Onay ve Excel'e Yazma Simülasyonu
            secilen_ikame = st.selectbox("Ordino Yazılacak Personeli Seçin:", oneriler["Personel"].tolist())
            if st.button("Ordinoyu Onayla ve Kaydet"):
                st.toast(f"✅ {secilen_ikame}, {plan_tarihi.strftime('%d.%m.%Y')} tarihinde {hedef_gemi} gemisine atandı!")

st.divider()
with st.expander("📊 Mevcut Excel Veri Tablolarını Görüntüle"):
    t1, t2, t3 = st.tabs(["Personel Listesi", "Günlük Vardiya & İzin", "Geçmiş Gemi Çekilme"])
    with t1:
        st.dataframe(personel_df, use_container_width=True)
    with t2:
        st.dataframe(vardiya_df, use_container_width=True)
    with t3:
        st.dataframe(gecmis_df, use_container_width=True)

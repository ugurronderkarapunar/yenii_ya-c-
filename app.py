import streamlit as st
import pandas as pd
from datetime import datetime
import io

st.set_page_config(page_title="Gemi Yağcı Ordino & İkame Planlayıcı", layout="wide")

GUNLER = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]

st.title("🚢 Gemi Yağcı Ordino & İkame Planlayıcı (Boş Şablon)")
st.markdown("Kendi verilerinizi girebileceğiniz boş Excel şablonunu indirebilir veya kendi dosyanızı yükleyebilirsiniz.")

# --- KENAR ÇUBUĞU: EXCEL YÖNETİMİ ---
st.sidebar.header("📁 Veri Yönetimi")
uploaded_file = st.sidebar.file_uploader(
    "Excel Dosyanızı Yükleyin (.xlsx)", 
    type=["xlsx"],
    help="Personel, Gemiler, Gemi_Makineleri, Vardiya_ve_Izin, Gemi_Gecmisi, Raporlar sayfalarını içeren dosya."
)

# Tamamen Boş/Başlıkları Hazır Şablon Üretici
def create_empty_template():
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        # 1. Personel Sayfası (Boş)
        pd.DataFrame(columns=[
            "Ad_Soyad", "Sicil_No", "Statu", "Bildigi_Gemiler", 
            "Vardiya_Gunleri", "Haftalik_Izin", "Vardiya_Tipi"
        ]).to_excel(writer, sheet_name="Personel", index=False)

        # 2. Gemi Makineleri Sayfası (Boş)
        pd.DataFrame(columns=["Makine_Adi"]).to_excel(writer, sheet_name="Gemi_Makineleri", index=False)

        # 3. Gemiler Sayfası (Boş)
        pd.DataFrame(columns=["Gemi_Adi", "Makine_Bilgisi", "Konum"]).to_excel(writer, sheet_name="Gemiler", index=False)

        # 4. Gemi Kaptan & Baş Makinist Bilgileri (Boş)
        pd.DataFrame(columns=["Gemi_Adi", "Tarih", "Kaptan", "Bas_Makinist"]).to_excel(writer, sheet_name="Gemi_Kaptan_Bas_Mak", index=False)

        # 5. Vardiya ve İzin Durumları (Boş)
        pd.DataFrame(columns=["Tarih", "Ad_Soyad", "Durum"]).to_excel(writer, sheet_name="Vardiya_ve_Izin", index=False)

        # 6. Gemi Geçmişi (Boş)
        pd.DataFrame(columns=["Ad_Soyad", "Gemi_Adi"]).to_excel(writer, sheet_name="Gemi_Gecmisi", index=False)

        # 7. Rapor / Disiplin Cezası Tablosu (Boş)
        pd.DataFrame(columns=["Ad_Soyad", "Gemi_Adi", "Rapor_Durumu"]).to_excel(writer, sheet_name="Raporlar", index=False)

    return output.getvalue()

st.sidebar.download_button(
    label="📥 Boş Excel Şablonunu İndir",
    data=create_empty_template(),
    file_name="bos_ordino_sablonu.xlsx",
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
        st.sidebar.error(f"Excel sayfaları okunurken hata oluştu (Doğru sayfa isimlerinin olduğundan emin olun): {e}")
        st.stop()
else:
    # Yüklenmediyse tamamen boş şablon ile başla
    empty_buffer = create_empty_template()
    personel_df, gemiler_df, makineler_df, vardiya_df, gemi_gecmisi_df, raporlar_df = load_data(io.BytesIO(empty_buffer))
    st.sidebar.warning("⚠️ Lütfen kendi Excel dosyanızı yükleyin veya yukarıdan boş şablonu indirip doldurarak yükleyin.")

# --- ÖNERİ ALGORİTMASI ---
def en_uygun_adaylari_bul(hedef_gemi, tarih_str):
    if personel_df.empty:
        return pd.DataFrame(), ""
        
    secilen_tarih = datetime.strptime(tarih_str, "%Y-%m-%d")
    gun_adi = GUNLER[secilen_tarih.weekday()]
    
    gemi_row = gemiler_df[gemiler_df["Gemi_Adi"].astype(str) == hedef_gemi]
    gemi_makinesi = gemi_row.iloc[0]["Makine_Bilgisi"] if not gemi_row.empty else "Tanımsız"

    adaylar = []

    for _, row in personel_df.iterrows():
        ad = str(row["Ad_Soyad"])
        statu = str(row["Statu"])
        haftalik_izin = str(row["Haftalik_Izin"]).strip()

        # 1. KURAL: Sabit personel başka gemiye kaydırılmaz
        if statu.lower() == "sabit":
            continue

        # 2. KURAL: O gemiyi bilmiş olacak (Daha önce o gemide çalışmış mı?)
        daha_once_calisti_mi = not gemi_gecmisi_df[
            (gemi_gecmisi_df["Ad_Soyad"].astype(str) == ad) & 
            (gemi_gecmisi_df["Gemi_Adi"].astype(str).str.lower() == hedef_gemi.lower())
        ].empty if not gemi_gecmisi_df.empty else False

        if not daha_once_calisti_mi:
            continue

        # 3. KURAL: Haftalık İzin Kontrolü
        if haftalik_izin.lower() == gun_adi.lower():
            continue

        # 4. KURAL: Günlük Durum Kontrolü (İzinde veya Vardiya Çıkışında olmayacak)
        gunluk_kayit = vardiya_df[(vardiya_df["Ad_Soyad"].astype(str) == ad) & (vardiya_df["Tarih"].astype(str) == tarih_str)] if not vardiya_df.empty else pd.DataFrame()
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
        ].empty if not raporlar_df.empty else False

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
            "Vardiya Tipi": row["Vardiya_Tipi"],
            "Haftalık İzin": haftalik_izin,
            "O Günkü Durum": durum,
            "Uygunluk Puanı": puan,
            "Seçim Nedeni": " | ".join(aciklama)
        })

    sonuc_df = pd.DataFrame(adaylar)
    if not sonuc_df.empty:
        sonuc_df = sonuc_df.sort_values(by="Uygunluk Puanı", ascending=False).head(4)
    return sonuc_df, gemi_makinesi

# --- ARAYÜZ ---
if personel_df.empty:
  st.info("👈 Başlamak için sol menüden boş şablonu indirip doldurun ve Excel dosyanızı yükleyin.")
else:
  col1, col2 = st.columns([1, 2])

  with col1:
      st.subheader("1. İzin / Eksik Bilgisi")
      personel_listesi = personel_df["Ad_Soyad"].tolist() if "Ad_Soyad" in personel_df.columns else []
      gemi_listesi = gemiler_df["Gemi_Adi"].tolist() if "Gemi_Adi" in gemiler_df.columns else []
      
      if not personel_listesi or not gemi_listesi:
          st.warning("Personel veya Gemi listesi boş. Lütfen Excel dosyasına veri ekleyin.")
      else:
          izinli_kisi = st.selectbox("İzin Alan Personel", personel_listesi)
          kisi_bilgi = personel_df[personel_df["Ad_Soyad"] == izinli_kisi].iloc[0]
          
          hedef_gemi = st.selectbox("İzin Alınan Gemi", gemi_listesi)
          plan_tarihi = st.date_input("Planlama Tarihi", value=datetime.now())
          
          st.info(f"**Sicil No:** {kisi_bilgi.get('Sicil_No', '-') } | **Statü:** {kisi_bilgi.get('Statu', '-') }")

  with col2:
      st.subheader("2. Kurallara Uygun En İyi 4 İkame Adayı")
      if st.button("Adayları Filtrele ve Listele", type="primary"):
          if personel_df.empty or gemiler_df.empty:
              st.error("Veri tabanları boş! Lütfen verilerinizi kontrol edin.")
          else:
              oneriler, gemi_makinesi = en_uygun_adaylari_bul(
                  hedef_gemi=hedef_gemi,
                  tarih_str=plan_tarihi.strftime("%Y-%m-%d")
              )
              
              st.write(f"⚙️ **Gemi Makine Altyapısı:** {gemi_makinesi}")
              
              if oneriler.empty:
                  st.error("Kriterlere uyan uygun personel bulunamadı! (Personelin geçmişte o gemide çalışmış olması, cezası olmaması ve o gün izinli/hafta izinli olmaması gerekir).")
              else:
                  st.success(f"**{hedef_gemi}** gemisi için en uygun {len(oneriler)} aday:")
                  st.dataframe(oneriler, use_container_width=True, hide_index=True)

                  st.markdown("---")
                  st.subheader("3. Ordino Onayı ve Rapor İndir")
                  secilen_ikame = st.selectbox("Görevlendirilecek Personel:", oneriler["Personel"].tolist())
                  
                  if st.button("Ordinoyu Onayla ve Excel İndir"):
                      output = io.BytesIO()
                      with pd.ExcelWriter(output, engine="openpyxl") as writer:
                          rapor_df = pd.DataFrame([{
                              "Tarih": plan_tarihi.strftime("%Y-%m-%d"),
                              "İzin Alan": izinli_kisi,
                              "Gemi": hedef_gemi,
                              "Makine": gemi_makinesi,
                              "Atanan İkame": secilen_ikame,
                              "Onay Durumu": "Kesinleşti"
                          }])
                          rapor_df.to_excel(writer, sheet_name="Atama_Sonucu", index=False)
                          oneriler.to_excel(writer, sheet_name="Uygun_Adaylar", index=False)
                          personel_df.to_excel(writer, sheet_name="Guncel_Personel", index=False)
                      
                      processed_data = output.getvalue()
                      
                      st.download_button(
                          label="📥 Ordino Excel Raporunu İndir (.xlsx)",
                          data=processed_data,
                          file_name=f"Ordino_{plan_tarihi.strftime('%Y%m%d')}_{hedef_gemi}.xlsx",
                          mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                      )
                      st.success(f"✅ {secilen_ikame}, {hedef_gemi} gemisi için başarıyla atandı!")

st.divider()
with st.expander("📊 Yüklü Tabloları İncele"):
    t1, t2, t3, t4, t5, t6 = st.tabs(["Personel", "Gemiler & Makineler", "Vardiya ve İzin", "Gemi Geçmişi", "Raporlar/Cezalar", "Kaptan/Baş Makinist"])
    with t1:
        st.dataframe(personel_df, use_container_width=True)
    with t2:
        st.dataframe(gemiler_df, use_container_width=True)
    with t3:
        st.dataframe(vardiya_df, use_container_width=True)
    with t4:
        st.dataframe(gemi_gecmisi_df, use_container_width=True)
    with t5:
        st.dataframe(raporlar_df, use_container_width=True)
    with t6:
        st.dataframe(gemiler_df, use_container_width=True)

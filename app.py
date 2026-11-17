import streamlit as st
import pandas as pd
from datetime import datetime
import io

st.set_page_config(page_title="Gemi Yağcı Ordino & İkame Planlayıcı", layout="wide")

GUNLER = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]

st.title("🚢 Gemi Yağcı Ordino & İkame Planlayıcı (Manuel Yönetim)")
st.markdown("Personel, Gemi Makineleri, Kaptan/Baş Makinist ve İzin Takibi ile Akıllı Öneri Sistemi.")

# --- SESSION STATE (Hafızada Tutma) ---
if "makineler_listesi" not in st.session_state:
    st.session_state.makineler_listesi = ["MTU 16V", "Caterpillar 3512", "Baudouin 12M", "Wartsila 6L20"]

if "gemiler_df" not in st.session_state:
    st.session_state.gemiler_df = pd.DataFrame(columns=["Gemi_Adi", "Makine_Bilgisi", "Konum", "Kaptan", "Bas_Makinist"])

if "personel_df" not in st.session_state:
    st.session_state.personel_df = pd.DataFrame(columns=[
        "Ad_Soyad", "Sicil_No", "Statu", "Bildigi_Gemiler", 
        "Vardiya_Gunleri", "Haftalik_Izin", "Vardiya_Tipi", "Izin_Tarihleri"
    ])

if "vardiya_df" not in st.session_state:
    st.session_state.vardiya_df = pd.DataFrame(columns=["Tarih", "Ad_Soyad", "Durum"])

if "gemi_gecmisi_df" not in st.session_state:
    st.session_state.gemi_gecmisi_df = pd.DataFrame(columns=["Ad_Soyad", "Gemi_Adi"])

if "raporlar_df" not in st.session_state:
    st.session_state.raporlar_df = pd.DataFrame(columns=["Ad_Soyad", "Gemi_Adi", "Rapor_Durumu"])

# --- KENAR ÇUBUĞU: MANUEL VERİ GİRİŞİ ---
st.sidebar.header("📝 Manuel Veri Girişi")
veri_tipi = st.sidebar.selectbox(
    "Eklenecek Veri Türü", 
    ["1. Gemi Makinesi Ekle", "2. Gemi Ekle", "3. Personel Ekle", "4. Günlük Vardiya/İzin", "5. Gemi Geçmişi Ekle", "6. Kaptan/Baş Makinist Raporu"]
)

with st.sidebar.form(key="veri_formu"):
    if veri_tipi == "1. Gemi Makinesi Ekle":
        st.subheader("Gemi Makinesi Tanımla")
        yeni_makine = st.text_input("Makine Adı / Modeli")
        submit = st.form_submit_button("Makineyi Ekle")
        if submit and yeni_makine:
            if yeni_makine not in st.session_state.makineler_listesi:
                st.session_state.makineler_listesi.append(yeni_makine)
                st.sidebar.success(f"✅ Makine eklendi: {yeni_makine}")

    elif veri_tipi == "2. Gemi Ekle":
        st.subheader("Gemi Tanımlama")
        gemi_adi = st.text_input("Gemi Adı")
        makine_secimi = st.selectbox("Makine Bilgisi", st.session_state.makineler_listesi if st.session_state.makineler_listesi else ["Önce Makine Ekleyin"])
        konum = st.text_input("Gemi Nerede (Konum / İskele)")
        kaptan = st.text_input("Gemi Kaptanı")
        bas_makinist = st.text_input("Baş Makinist")
        
        submit = st.form_submit_button("Gemi Kaydet")
        if submit and gemi_adi:
            yeni_satir = pd.DataFrame([{
                "Gemi_Adi": gemi_adi, "Makine_Bilgisi": makine_secimi, 
                "Konum": konum, "Kaptan": kaptan, "Bas_Makinist": bas_makinist
            }])
            st.session_state.gemiler_df = pd.concat([st.session_state.gemiler_df, yeni_satir], ignore_index=True)
            st.sidebar.success(f"✅ Gemi eklendi: {gemi_adi}")

    elif veri_tipi == "3. Personel Ekle":
        st.subheader("Personel Tanımlama")
        ad_soyad = st.text_input("Ad Soyad")
        sicil_no = st.text_input("Sicil No")
        statu = st.selectbox("Statü", ["Sabit", "İzinci", "8-5"])
        
        gemi_secenekleri = st.session_state.gemiler_df["Gemi_Adi"].tolist() if not st.session_state.gemiler_df.empty else ["Önce Gemi Ekleyin"]
        bildigi_gemiler = st.multiselect("Bildiği Gemiler (Çoklu Seçim)", gemi_secenekleri)
        
        vardiya_gunleri = st.multiselect("Vardiya Günleri", GUNLER)
        haftalik_izin = st.selectbox("Haftaizni Günü", GUNLER)
        
        st.markdown("---")
        st.write("📅 **İzin Tarihleri (Varsa Planlı İzin Aralığı)**")
        izin_baslangic = st.date_input("İzin Başlangıç Tarihi", value=None)
        izin_bitis = st.date_input("İzin Bitiş Tarihi", value=None)
        
        vardiya_tipi = st.selectbox("Vardiya Tipi", ["08-16 Sabit", "08-17 Sabit", "Vardiyalı / Posta", "8-5"])
        
        submit = st.form_submit_button("Personeli Kaydet")
        if submit and ad_soyad:
            izin_str = f"{izin_baslangic} ile {izin_bitis}" if izin_baslangic and izin_bitis else "Yok"
            yeni_satir = pd.DataFrame([{
                "Ad_Soyad": ad_soyad, "Sicil_No": sicil_no, "Statu": statu,
                "Bildigi_Gemiler": ", ".join(bildigi_gemiler),
                "Vardiya_Gunleri": ", ".join(vardiya_gunleri),
                "Haftalik_Izin": haftalik_izin, "Vardiya_Tipi": vardiya_tipi,
                "Izin_Tarihleri": izin_str
            }])
            st.session_state.personel_df = pd.concat([st.session_state.personel_df, yeni_satir], ignore_index=True)
            st.sidebar.success(f"✅ Personel kaydedildi: {ad_soyad}")

    elif veri_tipi == "4. Günlük Vardiya/İzin":
        st.subheader("Günlük Durum (İzinli / Vardiya Çıkışı vb.)")
        p_list = st.session_state.personel_df["Ad_Soyad"].tolist() if not st.session_state.personel_df.empty else []
        secilen_p = st.selectbox("Personel", p_list) if p_list else st.text_input("Personel Yok")
        tarih = st.date_input("Tarih")
        durum = st.selectbox("Günlük Durum", ["Müsait", "İzinli", "Vardiya Çıkışı", "Haftalık İzin"])
        
        submit = st.form_submit_button("Durumu Kaydet")
        if submit and secilen_p:
            yeni_satir = pd.DataFrame([{"Tarih": str(tarih), "Ad_Soyad": secilen_p, "Durum": durum}])
            st.session_state.vardiya_df = pd.concat([st.session_state.vardiya_df, yeni_satir], ignore_index=True)
            st.sidebar.success("✅ Günlük durum işlendi!")

    elif veri_tipi == "5. Gemi Geçmişi Ekle":
        st.subheader("Personelin Daha Önce Çalıştığı Gemiler")
        p_list = st.session_state.personel_df["Ad_Soyad"].tolist() if not st.session_state.personel_df.empty else []
        g_list = st.session_state.gemiler_df["Gemi_Adi"].tolist() if not st.session_state.gemiler_df.empty else []
        
        p_sec = st.selectbox("Personel", p_list) if p_list else st.text_input("Personel Yok")
        g_sec = st.selectbox("Gemi", g_list) if g_list else st.text_input("Gemi Yok")
        
        submit = st.form_submit_button("Geçmişi Kaydet")
        if submit and p_sec and g_sec:
            yeni_satir = pd.DataFrame([{"Ad_Soyad": p_sec, "Gemi_Adi": g_sec}])
            st.session_state.gemi_gecmisi_df = pd.concat([st.session_state.gemi_gecmisi_df, yeni_satir], ignore_index=True)
            st.sidebar.success("✅ Gemi geçmişi kaydedildi!")

    elif veri_tipi == "6. Kaptan/Baş Makinist Raporu":
        st.subheader("Kaptan veya Baş Makinitten Alınan Rapor/Ceza")
        p_list = st.session_state.personel_df["Ad_Soyad"].tolist() if not st.session_state.personel_df.empty else []
        g_list = st.session_state.gemiler_df["Gemi_Adi"].tolist() if not st.session_state.gemiler_df.empty else []
        
        p_sec = st.selectbox("Personel", p_list) if p_list else st.text_input("Personel Yok")
        g_sec = st.selectbox("Gemi", g_list) if g_list else st.text_input("Gemi Yok")
        rapor_durumu = st.selectbox("Rapor Durumu", ["Yok", "Var (Kaptan/Baş Makinist Raporu Var)"])
        
        submit = st.form_submit_button("Raporu Kaydet")
        if submit and p_sec and g_sec:
            yeni_satir = pd.DataFrame([{"Ad_Soyad": p_sec, "Gemi_Adi": g_sec, "Rapor_Durumu": rapor_durumu}])
            st.session_state.raporlar_df = pd.concat([st.session_state.raporlar_df, yeni_satir], ignore_index=True)
            st.sidebar.success("✅ Rapor kaydı işlendi!")

# --- ÖNERİ ALGORİTMASI (Görseldeki Kurallara Göre) ---
def en_uygun_adaylari_bul(hedef_gemi, tarih_str):
    if st.session_state.personel_df.empty:
        return pd.DataFrame(), ""
        
    secilen_tarih = datetime.strptime(tarih_str, "%Y-%m-%d")
    gun_adi = GUNLER[secilen_tarih.weekday()]
    
    gemi_row = st.session_state.gemiler_df[st.session_state.gemiler_df["Gemi_Adi"].astype(str) == hedef_gemi]
    gemi_makinesi = gemi_row.iloc[0]["Makine_Bilgisi"] if not gemi_row.empty else "Tanımsız"

    adaylar = []

    for _, row in st.session_state.personel_df.iterrows():
        ad = str(row["Ad_Soyad"])
        statu = str(row["Statu"])
        haftalik_izin = str(row["Haftalik_Izin"]).strip()

        # 1. Sabit personel başka gemiye kaydırılmaz
        if statu.lower() == "sabit":
            continue

        # KURAL 1: Önerilecek kişi izinde olmayacak
        # Günlük vardiya/izin tablosunda veya personel kartında izinliyse elenir
        gunluk_kayit = st.session_state.vardiya_df[
            (st.session_state.vardiya_df["Ad_Soyad"].astype(str) == ad) & 
            (st.session_state.vardiya_df["Tarih"].astype(str) == tarih_str)
        ] if not st.session_state.vardiya_df.empty else pd.DataFrame()
        
        durum = "Müsait"
        if not gunluk_kayit.empty:
            durum = str(gunluk_kayit.iloc[0]["Durum"])
            if durum in ["İzinli", "Haftalık İzin"]:
                continue

        # KURAL 2: Önerilecek kişi o gün haftaizni ya da vardiya çıkışı olmayacak
        if haftalik_izin.lower() == gun_adi.lower() or durum == "Vardiya Çıkışı":
            continue

        # KURAL 3: Kaptan ya da baş makinitten rapor yemiş olmayacak (O gemide raporu varsa elenir)
        rapor_var_mi = not st.session_state.raporlar_df[
            (st.session_state.raporlar_df["Ad_Soyad"].astype(str) == ad) & 
            (st.session_state.raporlar_df["Gemi_Adi"].astype(str).str.lower() == hedef_gemi.lower()) &
            (st.session_state.raporlar_df["Rapor_Durumu"].astype(str).str.lower().str.contains("var"))
        ].empty if not st.session_state.raporlar_df.empty else False

        if rapor_var_mi:
            continue

        # KURAL 4: O gemiyi bilmiş olacak (Daha önce o gemide çalışmış olacak)
        daha_once_calisti_mi = not st.session_state.gemi_gecmisi_df[
            (st.session_state.gemi_gecmisi_df["Ad_Soyad"].astype(str) == ad) & 
            (st.session_state.gemi_gecmisi_df["Gemi_Adi"].astype(str).str.lower() == hedef_gemi.lower())
        ].empty if not st.session_state.gemi_gecmisi_df.empty else False

        if not daha_once_calisti_mi:
            continue

        # --- PUANLAMA & SIRALAMA ---
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
            "Hafta İzni": haftalik_izin,
            "O Günkü Durum": durum,
            "Uygunluk Puanı": puan,
            "Kriter Uygunluk Nedenleri": " | ".join(aciklama)
        })

    sonuc_df = pd.DataFrame(adaylar)
    if not sonuc_df.empty:
        sonuc_df = sonuc_df.sort_values(by="Uygunluk Puanı", ascending=False).head(4)
    return sonuc_df, gemi_makinesi

# --- ANA EKRAN: PLANLAMA VE ÖNERİ ---
if st.session_state.personel_df.empty or st.session_state.gemiler_df.empty:
  st.info("👈 Sol menüden sırasıyla **Gemi Makinesi**, **Gemi** ve **Personel** kaydı ekleyerek başlayın.")
else:
  col1, col2 = st.columns([1, 2])

  with col1:
      st.subheader("1. İzin / Eksik Bilgisi Seçimi")
      p_list = st.session_state.personel_df["Ad_Soyad"].tolist()
      g_list = st.session_state.gemiler_df["Gemi_Adi"].tolist()
      
      izinli_kisi = st.selectbox("İzin Alan Personel", p_list)
      kisi_bilgi = st.session_state.personel_df[st.session_state.personel_df["Ad_Soyad"] == izinli_kisi].iloc[0]
      
      hedef_gemi = st.selectbox("İzin Alınan Gemi", g_list)
      plan_tarihi = st.date_input("Planlama Tarihi", value=datetime.now())
      
      st.info(f"**Sicil No:** {kisi_bilgi['Sicil_No']} | **Statü:** {kisi_bilgi['Statu']} | **Hafta İzni:** {kisi_bilgi['Haftalik_Izin']}")

  with col2:
      st.subheader("2. Kurallara Göre En Uygun 4 İkame Adayı")
      if st.button("Adayları Filtrele ve Listele", type="primary"):
          oneriler, gemi_makinesi = en_uygun_adaylari_bul(
              hedef_gemi=hedef_gemi,
              tarih_str=plan_tarihi.strftime("%Y-%m-%d")
          )
          
          st.write(f"⚙️ **Gemi Makine Altyapısı:** {gemi_makinesi}")
          
          if oneriler.empty:
              st.error("⚠️ Tüm kuralları sağlayan uygun personel bulunamadı! (Adayların izinde olmaması, o gün haftaizni/vardiya çıkışı olmaması, kaptan raporu olmaması ve o gemide daha önce çalışmış olması şarttır).")
          else:
              st.success(f"✨ **{hedef_gemi}** gemisi için kurallara uyan en uygun {len(oneriler)} aday:")
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
                      st.session_state.personel_df.to_excel(writer, sheet_name="Guncel_Personel", index=False)
                  
                  processed_data = output.getvalue()
                  
                  st.download_button(
                      label="📥 Ordino Excel Raporunu İndir (.xlsx)",
                      data=processed_data,
                      file_name=f"Ordino_{plan_tarihi.strftime('%Y%m%d')}_{hedef_gemi}.xlsx",
                      mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                  )
                  st.success(f"✅ {secilen_ikame}, {hedef_gemi} gemisi için başarıyla atandı!")

st.divider()
with st.expander("📊 Girilen Tüm Verileri ve Tabloları İncele"):
    t1, t2, t3, t4, t5 = st.tabs(["Personel Listesi", "Gemiler", "Vardiya ve İzin", "Gemi Geçmişi", "Raporlar"])
    with t1:
        st.dataframe(st.session_state.personel_df, use_container_width=True)
    with t2:
        st.dataframe(st.session_state.gemiler_df, use_container_width=True)
    with t3:
        st.dataframe(st.session_state.vardiya_df, use_container_width=True)
    with t4:
        st.dataframe(st.session_state.gemi_gecmisi_df, use_container_width=True)
    with t5:
        st.dataframe(st.session_state.raporlar_df, use_container_width=True)

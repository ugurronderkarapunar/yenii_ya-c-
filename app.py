import streamlit as st
import pandas as pd
from datetime import datetime
import io

st.set_page_config(page_title="Gemi Yağcı Ordino & İkame Planlayıcı", layout="wide")

GUNLER = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]

st.title("🚢 Gemi Yağcı Ordino & İkame Planlayıcı (Manuel Veri Girişi)")
st.markdown("Verileri Excel yüklemeden, tamamen arayüz üzerinden elle girerek yönetebileceğiniz ve ordino planlayabileceğiniz sistem.")

# --- SESSION STATE (Verileri Hafızada Tutma) ---
if "personel_df" not in st.session_state:
    st.session_state.personel_df = pd.DataFrame(columns=["Ad_Soyad", "Sicil_No", "Statu", "Bildigi_Gemiler", "Vardiya_Gunleri", "Haftalik_Izin", "Vardiya_Tipi"])

if "gemiler_df" not in st.session_state:
    st.session_state.gemiler_df = pd.DataFrame(columns=["Gemi_Adi", "Makine_Bilgisi", "Konum"])

if "vardiya_df" not in st.session_state:
    st.session_state.vardiya_df = pd.DataFrame(columns=["Tarih", "Ad_Soyad", "Durum"])

if "gemi_gecmisi_df" not in st.session_state:
    st.session_state.gemi_gecmisi_df = pd.DataFrame(columns=["Ad_Soyad", "Gemi_Adi"])

if "raporlar_df" not in st.session_state:
    st.session_state.raporlar_df = pd.DataFrame(columns=["Ad_Soyad", "Gemi_Adi", "Rapor_Durumu"])

# --- KENAR ÇUCUĞU: VERİ EKLEME PANELİ ---
st.sidebar.header("📝 Manuel Veri Girişi")
veri_tipi = st.sidebar.selectbox(
    "Eklenecek Veri Türü", 
    ["Personel Ekle", "Gemi Ekle", "Günlük Vardiya/İzin Durumu", "Gemi Geçmişi Ekle", "Rapor/Disiplin Ekle"]
)

with st.sidebar.form(key="veri_giris_formu"):
    if veri_tipi == "Personel Ekle":
        st.subheader("Personel Tanımlama")
        ad_soyad = st.text_input("Ad Soyad")
        sicil_no = st.text_input("Sicil No")
        statu = st.selectbox("Statü", ["Sabit", "İzinci", "8-5"])
        bildigi_gemiler = st.text_input("Bildiği Gemiler (Virgülle ayırın, örn: Beykoz, Kadıköy)")
        vardiya_gunleri = st.text_input("Çalıştığı Günler (örn: Pzt, Çar, Cum)")
        haftalik_izin = st.selectbox("Haftalık İzin Günü", GUNLER)
        vardiya_tipi = st.text_input("Vardiya Tipi (örn: 08-16 / Vardiyalı)")
        
        submit_btn = st.form_submit_button("Personeli Kaydet")
        if submit_btn and ad_soyad:
            yeni_satir = pd.DataFrame([{
                "Ad_Soyad": ad_soyad, "Sicil_No": sicil_no, "Statu": statu,
                "Bildigi_Gemiler": bildigi_gemiler, "Vardiya_Gunleri": vardiya_gunleri,
                "Haftalik_Izin": haftalik_izin, "Vardiya_Tipi": vardiya_tipi
            }])
            st.session_state.personel_df = pd.concat([st.session_state.personel_df, yeni_satir], ignore_index=True)
            st.sidebar.success(f"✅ {ad_soyad} eklendi!")

    elif veri_tipi == "Gemi Ekle":
        st.subheader("Gemi Tanımlama")
        gemi_adi = st.text_input("Gemi Adı")
        makine_bilgisi = st.text_input("Makine Bilgisi (örn: MTU 16V)")
        konum = st.text_input("Bulunduğu Konum / İskele")
        
        submit_btn = st.form_submit_button("Gemiye Kaydet")
        if submit_btn and gemi_adi:
            yeni_satir = pd.DataFrame([{"Gemi_Adi": gemi_adi, "Makine_Bilgisi": makine_bilgisi, "Konum": konum}])
            st.session_state.gemiler_df = pd.concat([st.session_state.gemiler_df, yeni_satir], ignore_index=True)
            st.sidebar.success(f"✅ {gemi_adi} gemisi eklendi!")

    elif veri_tipi == "Günlük Vardiya/İzin Durumu":
        st.subheader("Vardiya ve İzin Girişi")
        p_listesi = st.session_state.personel_df["Ad_Soyad"].tolist() if not st.session_state.personel_df.empty else []
        p_secilen = st.selectbox("Personel", p_listesi) if p_listesi else st.text_input("Personel Adı")
        tarih = st.date_input("Tarih")
        durum = st.selectbox("Durum", ["Müsait", "İzinli", "Vardiya Çıkışı", "Haftalık İzin"])
        
        submit_btn = st.form_submit_button("Durumu Kaydet")
        if submit_btn and p_secilen:
            yeni_satir = pd.DataFrame([{"Tarih": str(tarih), "Ad_Soyad": p_secilen, "Durum": durum}])
            st.session_state.vardiya_df = pd.concat([st.session_state.vardiya_df, yeni_satir], ignore_index=True)
            st.sidebar.success("✅ Günlük durum kaydedildi!")

    elif veri_tipi == "Gemi Geçmişi Ekle":
        st.subheader("Hangi Gemiye Gitti (Geçmiş Çalışma)")
        p_listesi = st.session_state.personel_df["Ad_Soyad"].tolist() if not st.session_state.personel_df.empty else []
        g_listesi = st.session_state.gemiler_df["Gemi_Adi"].tolist() if not st.session_state.gemiler_df.empty else []
        
        p_sec = st.selectbox("Personel", p_listesi) if p_listesi else st.text_input("Personel Adı")
        g_sec = st.selectbox("Gemi", g_listesi) if g_listesi else st.text_input("Gemi Adı")
        
        submit_btn = st.form_submit_button("Geçmişi Kaydet")
        if submit_btn and p_sec and g_sec:
            yeni_satir = pd.DataFrame([{"Ad_Soyad": p_sec, "Gemi_Adi": g_sec}])
            st.session_state.gemi_gecmisi_df = pd.concat([st.session_state.gemi_gecmisi_df, yeni_satir], ignore_index=True)
            st.sidebar.success("✅ Gemi geçmişi işlendi!")

    elif veri_tipi == "Rapor/Disiplin Ekle":
        st.subheader("Kaptan / Baş Makinist Raporu")
        p_listesi = st.session_state.personel_df["Ad_Soyad"].tolist() if not st.session_state.personel_df.empty else []
        g_listesi = st.session_state.gemiler_df["Gemi_Adi"].tolist() if not st.session_state.gemiler_df.empty else []
        
        p_sec = st.selectbox("Personel", p_listesi) if p_listesi else st.text_input("Personel Adı")
        g_sec = st.selectbox("Gemi", g_listesi) if g_listesi else st.text_input("Gemi Adı")
        rapor_durumu = st.selectbox("Rapor Durumu", ["Yok", "Var (Disiplin/Rapor Yemiş)"])
        
        submit_btn = st.form_submit_button("Raporu Kaydet")
        if submit_btn and p_sec and g_sec:
            yeni_satir = pd.DataFrame([{"Ad_Soyad": p_sec, "Gemi_Adi": g_sec, "Rapor_Durumu": rapor_durumu}])
            st.session_state.raporlar_df = pd.concat([st.session_state.raporlar_df, yeni_satir], ignore_index=True)
            st.sidebar.success("✅ Rapor kaydı işlendi!")

# --- ÖNERİ ALGORİTMASI ---
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

        # 1. KURAL: Sabit personel başka gemiye kaydırılmaz
        if statu.lower() == "sabit":
            continue

        # 2. KURAL: O gemiyi bilmiş olacak (Daha önce o gemide çalışmış mı?)
        daha_once_calisti_mi = not st.session_state.gemi_gecmisi_df[
            (st.session_state.gemi_gecmisi_df["Ad_Soyad"].astype(str) == ad) & 
            (st.session_state.gemi_gecmisi_df["Gemi_Adi"].astype(str).str.lower() == hedef_gemi.lower())
        ].empty if not st.session_state.gemi_gecmisi_df.empty else False

        if not daha_once_calisti_mi:
            continue

        # 3. KURAL: Haftalık İzin Kontrolü
        if haftalik_izin.lower() == gun_adi.lower():
            continue

        # 4. KURAL: Günlük Durum Kontrolü (İzinde veya Vardiya Çıkışında olmayacak)
        gunluk_kayit = st.session_state.vardiya_df[
            (st.session_state.vardiya_df["Ad_Soyad"].astype(str) == ad) & 
            (st.session_state.vardiya_df["Tarih"].astype(str) == tarih_str)
        ] if not st.session_state.vardiya_df.empty else pd.DataFrame()
        
        durum = "Müsait"
        if not gunluk_kayit.empty:
            durum = str(gunluk_kayit.iloc[0]["Durum"])
            if durum in ["İzinli", "Vardiya Çıkışı", "Haftalık İzin"]:
                continue

        # 5. KURAL: Kaptan ya da Baş Makinitten Rapor / Cezası Olmayacak
        ceza_var_mi = not st.session_state.raporlar_df[
            (st.session_state.raporlar_df["Ad_Soyad"].astype(str) == ad) & 
            (st.session_state.raporlar_df["Gemi_Adi"].astype(str).str.lower() == hedef_gemi.lower()) &
            (st.session_state.raporlar_df["Rapor_Durumu"].astype(str).str.lower().str.contains("var"))
        ].empty if not st.session_state.raporlar_df.empty else False

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

# --- ANA EKRAN: ORDNIO PLANLAMA ---
if st.session_state.personel_df.empty or st.session_state.gemiler_df.empty:
  st.info("👈 Başlamak için sol menüyü kullanarak en az bir **Personel** ve bir **Gemi** kaydı ekleyin.")
else:
  col1, col2 = st.columns([1, 2])

  with col1:
      st.subheader("1. İzin / Eksik Bilgisi")
      personel_listesi = st.session_state.personel_df["Ad_Soyad"].tolist()
      gemi_listesi = st.session_state.gemiler_df["Gemi_Adi"].tolist()
      
      izinli_kisi = st.selectbox("İzin Alan Personel", personel_listesi)
      kisi_bilgi = st.session_state.personel_df[st.session_state.personel_df["Ad_Soyad"] == izinli_kisi].iloc[0]
      
      hedef_gemi = st.selectbox("İzin Alınan Gemi", gemi_listesi)
      plan_tarihi = st.date_input("Planlama Tarihi", value=datetime.now())
      
      st.info(f"**Sicil No:** {kisi_bilgi['Sicil_No']} | **Statü:** {kisi_bilgi['Statu']}")

  with col2:
      st.subheader("2. Kurallara Uygun En İyi 4 İkame Adayı")
      if st.button("Adayları Filtrele ve Listele", type="primary"):
          oneriler, gemi_makinesi = en_uygun_adaylari_bul(
              hedef_gemi=hedef_gemi,
              tarih_str=plan_tarihi.strftime("%Y-%m-%d")
          )
          
          st.write(f"⚙️ **Gemi Makine Altyapısı:** {gemi_makinesi}")
          
          if oneriler.empty:
              st.error("Kriterlere uyan uygun personel bulunamadı! (Personelin daha önce o gemide çalışmış olması, cezası olmaması ve o gün izinli/hafta izinli olmaması gerekir).")
          else:
              st.success(f"**{hedef_gemi}** gemisi için en uygun {len(oneriler)} aday:")
              st.dataframe(oneriler, use_container_width=True, hide_index=True)

              st.markdown("---")
              st.subheader("3. Ordino Onayı ve Excel Raporu")
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
with st.expander("📊 Girilen Tüm Verileri İncele"):
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

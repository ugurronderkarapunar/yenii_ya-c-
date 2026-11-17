import io
import json
import os
from datetime import date, timedelta

import pandas as pd
import streamlit as st

st.set_page_config(page_title="Gemi Yağcı Ordino & İkame Planlayıcı", layout="wide")

# =====================================================================
# SABİTLER
# =====================================================================
GUNLER = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]
STATULER = ["Sabit", "İzinci", "8-5"]
GUNLUK_DURUMLAR = ["Müsait", "İzinli", "Vardiya Çıkışı", "Haftalık İzin"]

VARSAYILAN_MAKINELER = ["MTU 16V", "Caterpillar 3512", "Baudouin 12M", "Wartsila 6L20"]
VARSAYILAN_ISKELELER = ["Eminönü", "Kadıköy", "Üsküdar", "Karaköy", "Beşiktaş", "Kabataş", "Bostancı", "Adalar", "Tersane"]

DOSYA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ordino_veri.json")

SEMA = {
    "gemiler_df": ["Gemi_Adi", "Makine_Bilgisi", "Konum"],
    "gemi_kadro_df": ["Gemi_Adi", "Gun", "Kaptan", "Bas_Makinist"],
    "personel_df": ["Sicil_No", "Ad_Soyad", "Statu", "Bildigi_Gemiler", "Vardiya_Gunleri", "Haftalik_Izin"],
    "izinler_df": ["Ad_Soyad", "Baslangic", "Bitis"],
    "vardiya_df": ["Tarih", "Ad_Soyad", "Durum"],
    "atamalar_df": ["Tarih", "Ikame", "Gemi", "Izin_Alan"],
    "raporlar_df": ["Ad_Soyad", "Rapor_Veren", "Aciklama"],
}
TARIH_KOLONLARI = {
    "izinler_df": ["Baslangic", "Bitis"],
    "vardiya_df": ["Tarih"],
    "atamalar_df": ["Tarih"],
}
LISTELER = {
    "makineler_listesi": VARSAYILAN_MAKINELER,
    "iskeleler_listesi": VARSAYILAN_ISKELELER,
}

ss = st.session_state


# =====================================================================
# ŞİFRE (isteğe bağlı: ORDINO_SIFRE ortam değişkeni veya st.secrets)
# =====================================================================
def giris_kontrol():
    sifre = os.environ.get("ORDINO_SIFRE")
    if not sifre:
        try:
            sifre = st.secrets.get("ORDINO_SIFRE")
        except Exception:
            sifre = None
    if not sifre or ss.get("giris"):
        return
    st.title("🔒 Giriş")
    girilen = st.text_input("Şifre", type="password")
    if st.button("Giriş Yap"):
        if girilen == sifre:
            ss["giris"] = True
            st.rerun()
        else:
            st.error("Şifre hatalı.")
    st.stop()


giris_kontrol()


# =====================================================================
# VERİ KATMANI (JSON ile kalıcı kayıt)
# =====================================================================
def tarihleri_duzelt(df, kolonlar):
    df = df.copy()
    for k in kolonlar:
        df[k] = pd.to_datetime(df[k], errors="coerce").dt.date
    if kolonlar:
        df = df.dropna(subset=kolonlar)
    return df


def veriyi_yukle():
    ham = {}
    if os.path.exists(DOSYA):
        try:
            with open(DOSYA, "r", encoding="utf-8") as f:
                ham = json.load(f)
        except Exception as e:
            st.warning(f"Kayıt dosyası okunamadı, boş başlatıldı: {e}")
    for ad, kolonlar in SEMA.items():
        df = pd.DataFrame(ham.get(ad, []), columns=kolonlar)
        df = tarihleri_duzelt(df, TARIH_KOLONLARI.get(ad, []))
        ss[ad] = df.reset_index(drop=True)
    for ad, varsayilan in LISTELER.items():
        ss[ad] = list(ham.get(ad, varsayilan))


def kaydet():
    veri = {}
    for ad in SEMA:
        df = ss[ad].copy()
        for k in TARIH_KOLONLARI.get(ad, []):
            df[k] = df[k].map(lambda d: d.isoformat() if hasattr(d, "isoformat") else "")
        veri[ad] = df.fillna("").astype(str).to_dict("records")
    for ad in LISTELER:
        veri[ad] = ss[ad]
    gecici = DOSYA + ".tmp"
    with open(gecici, "w", encoding="utf-8") as f:
        json.dump(veri, f, ensure_ascii=False, indent=2)
    os.replace(gecici, DOSYA)


def satir_ekle(ad, satir):
    ss[ad] = pd.DataFrame(ss[ad].to_dict("records") + [satir], columns=SEMA[ad])
    kaydet()


def liste(metin):
    return [x.strip() for x in str(metin).split(",") if x.strip()]


def norm(s):
    return str(s).strip().casefold()


def tr(d):
    return d.strftime("%d.%m.%Y")


if "yuklendi" not in ss:
    veriyi_yukle()
    ss["yuklendi"] = True


# =====================================================================
# ÖNERİ ALGORİTMASI
# =====================================================================
def adaylari_bul(hedef_gemi, bas, bit, izin_alan):
    """Döner: (1. kademe adaylar, 2. kademe adaylar, elenenler)"""
    gunler = [bas + timedelta(days=i) for i in range((bit - bas).days + 1)]

    izinler = {}
    for r in ss.izinler_df.to_dict("records"):
        izinler.setdefault(r["Ad_Soyad"], []).append((r["Baslangic"], r["Bitis"]))
    gunluk = {(r["Ad_Soyad"], r["Tarih"]): r["Durum"] for r in ss.vardiya_df.to_dict("records")}
    atamalar = ss.atamalar_df.to_dict("records")
    atanmis = {(r["Ikame"], r["Tarih"]) for r in atamalar}
    kadro = {(r["Gemi_Adi"], r["Gun"]): (r["Kaptan"], r["Bas_Makinist"]) for r in ss.gemi_kadro_df.to_dict("records")}
    raporlar = {}
    for r in ss.raporlar_df.to_dict("records"):
        raporlar.setdefault(r["Ad_Soyad"], set()).add(norm(r["Rapor_Veren"]))
    makine = {r["Gemi_Adi"]: r["Makine_Bilgisi"] for r in ss.gemiler_df.to_dict("records")}
    hedef_makine = makine.get(hedef_gemi, "")

    son30 = {}
    bu_gemide = {}
    for r in atamalar:
        if bas - timedelta(days=30) <= r["Tarih"] <= bas:
            son30[r["Ikame"]] = son30.get(r["Ikame"], 0) + 1
        if r["Gemi"] == hedef_gemi:
            bu_gemide[r["Ikame"]] = bu_gemide.get(r["Ikame"], 0) + 1

    def gun_kontrol(ad, p):
        haftalik = str(p["Haftalik_Izin"]).strip()
        calisma = liste(p["Vardiya_Gunleri"])
        for g in gunler:
            gun_adi = GUNLER[g.weekday()]
            # KURAL 1: izinde olmayacak
            for b1, b2 in izinler.get(ad, []):
                if b1 <= g <= b2:
                    return f"{tr(g)} tarihinde planlı izinde"
            durum = gunluk.get((ad, g), "Müsait")
            if durum in ("İzinli", "Haftalık İzin"):
                return f"{tr(g)} günlük kayıtta izinli"
            if (ad, g) in atanmis:
                return f"{tr(g)} tarihinde başka bir atamada"
            # KURAL 2: haftaizni / vardiya çıkışı / vardiya günü değil
            if haftalik == gun_adi:
                return f"{tr(g)} ({gun_adi}) haftaizni"
            if durum == "Vardiya Çıkışı":
                return f"{tr(g)} vardiya çıkışı"
            if calisma and gun_adi not in calisma:
                return f"{gun_adi} vardiya günü değil"
            # KURAL 3: o gün gemideki kaptan/baş makinistten raporu olmayacak
            yetkililer = kadro.get((hedef_gemi, gun_adi))
            if yetkililer and any(norm(y) in raporlar.get(ad, set()) for y in yetkililer if str(y).strip()):
                return f"{gun_adi} günü gemideki yetkiliden raporu var"
        return None

    def puanla(ad, p, kademe):
        statu = p["Statu"]
        puan, acik = 0, []
        if statu == "İzinci":
            puan += 100
            acik.append("Asli izinci (+100)")
        elif statu == "8-5":
            puan += 50
            acik.append("8-5 kaydırılabilir (+50)")
        tecrube = min(bu_gemide.get(ad, 0), 5) * 5
        if tecrube:
            puan += tecrube
            acik.append(f"Bu gemide {bu_gemide[ad]} kez ikame (+{tecrube})")
        yorgun = min(son30.get(ad, 0), 10) * 3
        if yorgun:
            puan -= yorgun
            acik.append(f"Son 30 günde {son30[ad]} gün atanmış (-{yorgun})")
        if kademe == 2:
            puan -= 50
            acik.append("Gemiyi bilmiyor, aynı makineli gemiyi biliyor (-50)")
        return {
            "Personel": ad, "Sicil No": p["Sicil_No"], "Statü": statu,
            "Kademe": kademe,
            "Uygunluk Puanı": puan, "Nedenler": " | ".join(acik) if acik else "-",
        }

    t1, t2, elenen = [], [], []
    for p in ss.personel_df.to_dict("records"):
        ad = p["Ad_Soyad"]
        if ad == izin_alan:
            elenen.append({"Personel": ad, "Eleme Nedeni": "İzin alan kişinin kendisi"})
            continue
        if p["Statu"] == "Sabit":
            elenen.append({"Personel": ad, "Eleme Nedeni": "Sabit personel kaydırılamaz"})
            continue
        bildigi = liste(p["Bildigi_Gemiler"])
        biliyor = hedef_gemi in bildigi
        ayni_makine = bool(hedef_makine) and any(makine.get(g) == hedef_makine for g in bildigi)
        if not biliyor and not ayni_makine:
            elenen.append({"Personel": ad, "Eleme Nedeni": "Gemiyi bilmiyor"})
            continue
        neden = gun_kontrol(ad, p)
        if neden:
            elenen.append({"Personel": ad, "Eleme Nedeni": neden})
        elif biliyor:
            t1.append(puanla(ad, p, 1))
        else:
            t2.append(puanla(ad, p, 2))

    def sirala(liste_):
        df = pd.DataFrame(liste_)
        if not df.empty:
            df = df.sort_values("Uygunluk Puanı", ascending=False).head(4).reset_index(drop=True)
        return df

    return sirala(t1), sirala(t2), pd.DataFrame(elenen, columns=["Personel", "Eleme Nedeni"])


def excel_olustur(atama_df, oneriler, elenenler):
    cikti = io.BytesIO()
    with pd.ExcelWriter(cikti, engine="openpyxl") as w:
        atama_df.to_excel(w, sheet_name="Atama_Sonucu", index=False)
        oneriler.to_excel(w, sheet_name="Uygun_Adaylar", index=False)
        elenenler.to_excel(w, sheet_name="Elenenler", index=False)
        ss.personel_df.to_excel(w, sheet_name="Guncel_Personel", index=False)
    return cikti.getvalue()


def tablo_duzenle(ad, anahtar_kolon, column_config=None, bos_none=()):
    """Düzenlenebilir tablo: satır ekle/sil/düzelt + kaydet."""
    surum = ss.get(f"surum_{ad}", 0)
    goster = ss[ad].copy()
    for k in bos_none:
        goster[k] = goster[k].map(lambda v: v if str(v).strip() else None)
    duzenlenen = st.data_editor(
        goster, num_rows="dynamic", hide_index=True,
        key=f"edit_{ad}_{surum}", column_config=column_config or {},
    )
    if st.button("💾 Değişiklikleri Kaydet", key=f"kaydet_btn_{ad}"):
        yeni = duzenlenen.copy()
        tkol = TARIH_KOLONLARI.get(ad, [])
        for k in yeni.columns:
            if k not in tkol:
                yeni[k] = yeni[k].fillna("").astype(str)
        yeni = tarihleri_duzelt(yeni, tkol)
        yeni = yeni[yeni[anahtar_kolon].astype(str).str.strip() != ""]
        ss[ad] = yeni.reset_index(drop=True)
        kaydet()
        ss[f"surum_{ad}"] = surum + 1
        st.rerun()


def sil_ui(ad, bos_mesaj="Kayıt yok."):
    """Tabloyu gösterir, işaretlenen satırları siler (personel silinirse izin/durum/rapor kayıtları da silinir)."""
    df = ss[ad]
    if df.empty:
        st.caption(bos_mesaj)
        return
    surum = ss.get(f"surum_{ad}", 0)
    goster = df.copy()
    goster.insert(0, "Sil", False)
    duz = st.data_editor(
        goster, hide_index=True, key=f"silduz_{ad}_{surum}",
        column_config={"Sil": st.column_config.CheckboxColumn("Sil", default=False)},
        disabled=[c for c in goster.columns if c != "Sil"],
    )
    secili = duz.index[duz["Sil"]].tolist()
    if st.button(f"🗑️ Seçilenleri Sil ({len(secili)})", key=f"silbtn_{ad}", disabled=not secili):
        silinen_adlar = df.loc[secili, "Ad_Soyad"].tolist() if ad == "personel_df" else []
        ss[ad] = df.drop(index=secili).reset_index(drop=True)
        if ad == "personel_df" and silinen_adlar:
            for diger in ("izinler_df", "vardiya_df", "raporlar_df"):
                ss[diger] = ss[diger][~ss[diger]["Ad_Soyad"].isin(silinen_adlar)].reset_index(drop=True)
                ss[f"surum_{diger}"] = ss.get(f"surum_{diger}", 0) + 1
        ss[f"surum_{ad}"] = surum + 1
        kaydet()
        st.rerun()


# =====================================================================
# ARAYÜZ
# =====================================================================
st.title("🚢 Gemi Yağcı Ordino & İkame Planlayıcı")
st.caption("Personel, gemi, kaptan/baş makinist kadrosu ve izin takibi ile akıllı ikame öneri sistemi.")

sekme_ordino, sekme_personel, sekme_gemi, sekme_izin, sekme_rapor, sekme_veri, sekme_tanim = st.tabs([
    "📋 Ordino / İkame Önerisi", "👥 Personel", "🚢 Gemiler & Kadro",
    "📅 İzin / Günlük Durum", "⚠️ Raporlar", "📊 Atamalar & Veri", "⚙️ Tanımlar",
])

# ---------------------------------------------------------------------
# 1) ORDİNO / ÖNERİ
# ---------------------------------------------------------------------
with sekme_ordino:
    if ss.get("basari"):
        st.success(ss.pop("basari"))

    if ss.personel_df.empty or ss.gemiler_df.empty:
        st.info("Önce **Gemiler & Kadro** ve **Personel** sekmelerinden kayıt ekleyin.")
    else:
        c1, c2 = st.columns([1, 2])
        p_adlari = ss.personel_df["Ad_Soyad"].tolist()
        g_adlari = ss.gemiler_df["Gemi_Adi"].tolist()

        with c1:
            st.subheader("1. İzin Bilgisi")
            izin_alan = st.selectbox("İzin Alan Personel", p_adlari, key="o_izin_alan")
            kisi = ss.personel_df[ss.personel_df["Ad_Soyad"] == izin_alan].iloc[0]
            hedef_gemi = st.selectbox("İzin Alınan Gemi", g_adlari, key="o_gemi")
            bas = st.date_input("İzin Başlangıç", value=date.today(), key="o_bas")
            bit = st.date_input("İzin Bitiş", value=date.today(), key="o_bit")
            ikinci_kademe = st.checkbox(
                "Gemiyi bilen çıkmazsa aynı makineli gemiyi bilenleri öner", value=True, key="o_ikinci"
            )
            st.info(f"**Sicil:** {kisi['Sicil_No']} | **Statü:** {kisi['Statu']} | **Hafta İzni:** {kisi['Haftalik_Izin'] or '-'}")

        with c2:
            st.subheader("2. Kurallara Göre En Uygun 4 İkame Adayı")
            if st.button("Adayları Filtrele ve Listele", type="primary"):
                if bit < bas:
                    st.error("İzin bitiş tarihi başlangıçtan önce olamaz.")
                else:
                    t1, t2, el = adaylari_bul(hedef_gemi, bas, bit, izin_alan)
                    if t1.empty and ikinci_kademe and not t2.empty:
                        oneriler = t2
                    else:
                        oneriler = t1
                        if not t2.empty:
                            ek = pd.DataFrame({
                                "Personel": t2["Personel"],
                                "Eleme Nedeni": "Gemiyi bilmiyor (aynı makineli gemiyi biliyor, ikinci kademe kullanılmadı)",
                            })
                            el = pd.concat([el, ek], ignore_index=True)
                    ss["oneriler"] = oneriler
                    ss["elenenler"] = el
                    ss["son_arama"] = {"gemi": hedef_gemi, "izin_alan": izin_alan, "bas": bas, "bit": bit}
                    ss.pop("son_excel", None)

            sa = ss.get("son_arama")
            if sa:
                st.write(
                    f"⚙️ **{sa['gemi']}** | İzin alan: **{sa['izin_alan']}** | "
                    f"{tr(sa['bas'])} – {tr(sa['bit'])}"
                )
                oneriler = ss["oneriler"]
                if oneriler.empty:
                    st.error(
                        "⚠️ Tüm kuralları sağlayan aday bulunamadı. "
                        "Nedenler için aşağıdaki 'Elenenler' bölümüne bakın."
                    )
                else:
                    if (oneriler["Kademe"] == 2).any():
                        st.warning("Gemiyi bilen uygun kimse yok; aynı makineli gemiyi bilenler listelendi (2. kademe).")
                    st.dataframe(oneriler, hide_index=True)

                    st.markdown("---")
                    st.subheader("3. Ordino Onayı")
                    secilen = st.selectbox("Görevlendirilecek Personel:", oneriler["Personel"].tolist(), key="secilen_ikame")
                    if st.button("✅ Ordinoyu Onayla"):
                        gunler = [sa["bas"] + timedelta(days=i) for i in range((sa["bit"] - sa["bas"]).days + 1)]
                        makine = ss.gemiler_df.loc[ss.gemiler_df["Gemi_Adi"] == sa["gemi"], "Makine_Bilgisi"]
                        makine = makine.iloc[0] if not makine.empty else ""
                        yeni = [{"Tarih": g, "Ikame": secilen, "Gemi": sa["gemi"], "Izin_Alan": sa["izin_alan"]} for g in gunler]
                        ss.atamalar_df = pd.DataFrame(ss.atamalar_df.to_dict("records") + yeni, columns=SEMA["atamalar_df"])
                        # izin alanın izni de kayda geçsin
                        mevcut = ss.izinler_df[
                            (ss.izinler_df["Ad_Soyad"] == sa["izin_alan"])
                            & (ss.izinler_df["Baslangic"] == sa["bas"])
                            & (ss.izinler_df["Bitis"] == sa["bit"])
                        ]
                        if mevcut.empty:
                            ss.izinler_df = pd.DataFrame(
                                ss.izinler_df.to_dict("records")
                                + [{"Ad_Soyad": sa["izin_alan"], "Baslangic": sa["bas"], "Bitis": sa["bit"]}],
                                columns=SEMA["izinler_df"],
                            )
                        kaydet()
                        atama_df = pd.DataFrame(yeni)
                        atama_df["Makine"] = makine
                        atama_df["Onay Durumu"] = "Kesinleşti"
                        veri = excel_olustur(atama_df, oneriler, ss["elenenler"])
                        ss["son_excel"] = (veri, f"Ordino_{sa['bas'].strftime('%Y%m%d')}_{sa['gemi']}.xlsx")
                        ss["basari"] = f"{secilen}, {sa['gemi']} gemisi için {len(gunler)} gün atandı. {sa['izin_alan']} izinli olarak işlendi."
                        ss.pop("oneriler", None)
                        ss.pop("son_arama", None)
                        ss.pop("elenenler", None)
                        st.rerun()

                with st.expander("🚫 Elenenler ve nedenleri"):
                    if ss["elenenler"].empty:
                        st.write("Elenen kimse yok.")
                    else:
                        st.dataframe(ss["elenenler"], hide_index=True)

            if ss.get("son_excel"):
                veri, dosya_adi = ss["son_excel"]
                st.download_button(
                    "📥 Ordino Excel Raporunu İndir (.xlsx)", data=veri, file_name=dosya_adi,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )

# ---------------------------------------------------------------------
# 2) PERSONEL
# ---------------------------------------------------------------------
with sekme_personel:
    st.subheader("Personel Ekle")
    gemi_secenekleri = ss.gemiler_df["Gemi_Adi"].tolist()
    if not gemi_secenekleri:
        st.info("Personel eklemeden önce en az bir gemi tanımlayın (Gemiler & Kadro sekmesi).")
    else:
        statu = st.selectbox("Statü / Vardiya Tipi", STATULER, key="p_statu")
        with st.form("personel_formu", clear_on_submit=True):
            a, b = st.columns(2)
            ad_soyad = a.text_input("Ad Soyad")
            sicil_no = b.text_input("Sicil No")
            bildigi = st.multiselect("Bildiği Gemiler", gemi_secenekleri)
            if statu == "İzinci":
                st.caption("İzinci personel için vardiya günü ve haftaizni gerekmez.")
                vardiya_gunleri, haftalik_izin = [], ""
            else:
                vardiya_gunleri = st.multiselect("Vardiya (Çalışma) Günleri", GUNLER, default=GUNLER[:5])
                haftalik_izin = st.selectbox("Haftaizni Günü", GUNLER, index=6)
            if st.form_submit_button("Personeli Kaydet"):
                ad_soyad, sicil_no = ad_soyad.strip(), sicil_no.strip()
                if not ad_soyad or not sicil_no:
                    st.error("Ad Soyad ve Sicil No zorunludur.")
                elif sicil_no in ss.personel_df["Sicil_No"].astype(str).tolist():
                    st.error("Bu sicil numarası zaten kayıtlı.")
                elif ad_soyad in ss.personel_df["Ad_Soyad"].tolist():
                    st.error("Bu isimde bir personel zaten kayıtlı.")
                else:
                    satir_ekle("personel_df", {
                        "Sicil_No": sicil_no, "Ad_Soyad": ad_soyad, "Statu": statu,
                        "Bildigi_Gemiler": ", ".join(bildigi), "Vardiya_Gunleri": ", ".join(vardiya_gunleri),
                        "Haftalik_Izin": haftalik_izin,
                    })
                    st.success(f"Personel kaydedildi: {ad_soyad}")
                    st.rerun()

    with st.expander("📤 Excel'den toplu personel yükle"):
        sablon = pd.DataFrame([{
            "Sicil_No": "1001", "Ad_Soyad": "Örnek Kişi", "Statu": "İzinci",
            "Bildigi_Gemiler": "Gemi A, Gemi B", "Vardiya_Gunleri": "Pazartesi, Salı, Çarşamba",
            "Haftalik_Izin": "Pazar",
        }])
        sb = io.BytesIO()
        sablon.to_excel(sb, index=False)
        st.download_button("Şablonu indir", sb.getvalue(), "personel_sablon.xlsx")
        yuklenen = st.file_uploader("Doldurulmuş Excel (.xlsx)", type=["xlsx"])
        if yuklenen is not None and st.button("Yüklenen personeli ekle"):
            try:
                ex = pd.read_excel(yuklenen, dtype=str).fillna("")
                eksik = [k for k in SEMA["personel_df"] if k not in ex.columns]
                if eksik:
                    st.error(f"Eksik kolonlar: {', '.join(eksik)}")
                else:
                    eklenen, atlanan = 0, 0
                    for r in ex[SEMA["personel_df"]].to_dict("records"):
                        r = {k: str(v).strip() for k, v in r.items()}
                        if (not r["Ad_Soyad"] or not r["Sicil_No"] or r["Statu"] not in STATULER
                                or r["Sicil_No"] in ss.personel_df["Sicil_No"].astype(str).tolist()
                                or r["Ad_Soyad"] in ss.personel_df["Ad_Soyad"].tolist()):
                            atlanan += 1
                            continue
                        ss.personel_df = pd.DataFrame(ss.personel_df.to_dict("records") + [r], columns=SEMA["personel_df"])
                        eklenen += 1
                    kaydet()
                    st.success(f"{eklenen} personel eklendi, {atlanan} satır atlandı (boş/mükerrer).")
            except Exception as e:
                st.error(f"Dosya okunamadı: {e}")

    st.subheader("Personel Listesi (silmek için 'Sil' kutusunu işaretleyin)")
    sil_ui("personel_df", "Henüz personel yok.")
    st.caption("Düzeltme için 'Atamalar & Veri' sekmesini kullanın.")

# ---------------------------------------------------------------------
# 3) GEMİLER & KADRO
# ---------------------------------------------------------------------
with sekme_gemi:
    g1, g2 = st.columns(2)
    with g1:
        st.subheader("Gemi Ekle")
        if not ss.iskeleler_listesi:
            st.info("Önce Tanımlar sekmesinden iskele ekleyin.")
        else:
            with st.form("gemi_formu", clear_on_submit=True):
                gemi_adi = st.text_input("Gemi Adı")
                makine_secimi = st.selectbox("Makine Bilgisi", ss.makineler_listesi) if ss.makineler_listesi else None
                yeni_makine = st.text_input("Listede yoksa yeni makine adı (isteğe bağlı)")
                konum = st.selectbox("Gemi Nerede (Konum / İskele)", ss.iskeleler_listesi)
                if st.form_submit_button("Gemiyi Kaydet"):
                    gemi_adi, yeni_makine = gemi_adi.strip(), yeni_makine.strip()
                    makine_final = yeni_makine or makine_secimi
                    if not gemi_adi:
                        st.error("Gemi adı zorunludur.")
                    elif not makine_final:
                        st.error("Bir makine seçin veya yeni makine adı yazın.")
                    elif gemi_adi.casefold() in [x.casefold() for x in ss.gemiler_df["Gemi_Adi"].tolist()]:
                        st.error("Bu gemi zaten kayıtlı.")
                    else:
                        if makine_final not in ss.makineler_listesi:
                            ss.makineler_listesi.append(makine_final)
                        satir_ekle("gemiler_df", {"Gemi_Adi": gemi_adi, "Makine_Bilgisi": makine_final, "Konum": konum})
                        st.success(f"Gemi eklendi: {gemi_adi}")
                        st.rerun()
    with g2:
        st.subheader("Günlük Kaptan / Baş Makinist")
        if ss.gemiler_df.empty:
            st.info("Önce gemi ekleyin.")
        else:
            with st.form("kadro_formu", clear_on_submit=True):
                k_gemi = st.selectbox("Gemi", ss.gemiler_df["Gemi_Adi"].tolist())
                k_gunler = st.multiselect("Günler", GUNLER, default=GUNLER)
                kaptan = st.text_input("Kaptan")
                bas_makinist = st.text_input("Baş Makinist")
                if st.form_submit_button("Kadroyu Kaydet"):
                    if not k_gunler or not (kaptan.strip() or bas_makinist.strip()):
                        st.error("En az bir gün ve bir isim girin.")
                    else:
                        eski = ss.gemi_kadro_df
                        eski = eski[~((eski["Gemi_Adi"] == k_gemi) & (eski["Gun"].isin(k_gunler)))]
                        yeni = [{"Gemi_Adi": k_gemi, "Gun": g, "Kaptan": kaptan.strip(), "Bas_Makinist": bas_makinist.strip()} for g in k_gunler]
                        ss.gemi_kadro_df = pd.DataFrame(eski.to_dict("records") + yeni, columns=SEMA["gemi_kadro_df"])
                        kaydet()
                        st.success("Kadro kaydedildi.")
                        st.rerun()

    st.subheader("Gemiler")
    st.dataframe(ss.gemiler_df, hide_index=True)
    st.subheader("Gemi Kadrosu: Kaptan / Baş Makinist (silmek için işaretleyin)")
    sil_ui("gemi_kadro_df", "Henüz kadro kaydı yok.")

# ---------------------------------------------------------------------
# 4) İZİN / GÜNLÜK DURUM
# ---------------------------------------------------------------------
with sekme_izin:
    if ss.personel_df.empty:
        st.info("Önce personel ekleyin.")
    else:
        p_adlari = ss.personel_df["Ad_Soyad"].tolist()
        i1, i2 = st.columns(2)
        with i1:
            st.subheader("Planlı İzin Aralığı Ekle")
            with st.form("izin_formu", clear_on_submit=True):
                izp = st.selectbox("Personel", p_adlari, key="izin_p")
                ib = st.date_input("Başlangıç", value=date.today(), key="izin_b")
                ie = st.date_input("Bitiş", value=date.today(), key="izin_e")
                if st.form_submit_button("İzni Kaydet"):
                    if ie < ib:
                        st.error("Bitiş tarihi başlangıçtan önce olamaz.")
                    else:
                        satir_ekle("izinler_df", {"Ad_Soyad": izp, "Baslangic": ib, "Bitis": ie})
                        st.success("İzin kaydedildi.")
                        st.rerun()
        with i2:
            st.subheader("Günlük Durum (İzinli / Vardiya Çıkışı vb.)")
            with st.form("gunluk_formu", clear_on_submit=True):
                gp = st.selectbox("Personel", p_adlari, key="gun_p")
                gt = st.date_input("Tarih", value=date.today(), key="gun_t")
                gd = st.selectbox("Durum", GUNLUK_DURUMLAR)
                if st.form_submit_button("Durumu Kaydet"):
                    eski = ss.vardiya_df
                    eski = eski[~((eski["Ad_Soyad"] == gp) & (eski["Tarih"] == gt))]
                    ss.vardiya_df = pd.DataFrame(
                        eski.to_dict("records") + [{"Tarih": gt, "Ad_Soyad": gp, "Durum": gd}],
                        columns=SEMA["vardiya_df"],
                    )
                    kaydet()
                    st.success("Günlük durum işlendi.")
                    st.rerun()
        st.subheader("Planlı İzinler (silmek için işaretleyin)")
        sil_ui("izinler_df", "Planlı izin yok.")
        st.subheader("Günlük Durum Kayıtları (silmek için işaretleyin)")
        sil_ui("vardiya_df", "Günlük durum kaydı yok.")

# ---------------------------------------------------------------------
# 5) RAPORLAR
# ---------------------------------------------------------------------
with sekme_rapor:
    st.subheader("Kaptan / Baş Makinistten Alınan Rapor")
    st.caption("Rapor kişiye bağlıdır: raporu veren kaptan/baş makinistin adı girilir. "
               "Algoritma, ikame günlerinde hedef gemide kim görevliyse (Gemi Kadrosu) onunla karşılaştırır.")
    if ss.personel_df.empty:
        st.info("Önce personel ekleyin.")
    else:
        with st.form("rapor_formu", clear_on_submit=True):
            rp = st.selectbox("Personel", ss.personel_df["Ad_Soyad"].tolist())
            rv = st.text_input("Raporu Veren (Kaptan / Baş Makinist adı)")
            ra = st.text_input("Açıklama (isteğe bağlı)")
            if st.form_submit_button("Raporu Kaydet"):
                if not rv.strip():
                    st.error("Raporu veren kişinin adı zorunludur.")
                else:
                    satir_ekle("raporlar_df", {"Ad_Soyad": rp, "Rapor_Veren": rv.strip(), "Aciklama": ra.strip()})
                    st.success("Rapor kaydı işlendi.")
                    st.rerun()
    sil_ui("raporlar_df", "Rapor kaydı yok.")

# ---------------------------------------------------------------------
# 6) ATAMALAR & VERİ (düzenle / sil)
# ---------------------------------------------------------------------
with sekme_veri:
    st.caption("Tabloları düzeltin, satır ekleyin/silin (satırı seçip Delete). "
               "Not: gemi veya personel adını değiştirirseniz diğer tablolardaki eski adları da güncelleyin.")
    gemi_secim = ss.gemiler_df["Gemi_Adi"].tolist()
    with st.expander("Atamalar (silmek için işaretleyin)", expanded=True):
        sil_ui("atamalar_df", "Henüz atama yok.")
    with st.expander("Personel"):
        tablo_duzenle("personel_df", "Ad_Soyad", {
            "Statu": st.column_config.SelectboxColumn(options=STATULER),
            "Haftalik_Izin": st.column_config.SelectboxColumn(options=GUNLER),
        }, bos_none=["Haftalik_Izin"])
    with st.expander("Gemiler"):
        tablo_duzenle("gemiler_df", "Gemi_Adi", {
            "Makine_Bilgisi": st.column_config.SelectboxColumn(options=sorted(set(ss.makineler_listesi) | set(ss.gemiler_df["Makine_Bilgisi"]))),
            "Konum": st.column_config.SelectboxColumn(options=sorted(set(ss.iskeleler_listesi) | set(ss.gemiler_df["Konum"]))),
        })
    with st.expander("Gemi Kadrosu"):
        tablo_duzenle("gemi_kadro_df", "Gemi_Adi", {"Gun": st.column_config.SelectboxColumn(options=GUNLER)})
    with st.expander("Planlı İzinler"):
        tablo_duzenle("izinler_df", "Ad_Soyad", {
            "Baslangic": st.column_config.DateColumn(format="DD.MM.YYYY"),
            "Bitis": st.column_config.DateColumn(format="DD.MM.YYYY"),
        })
    with st.expander("Günlük Durum"):
        tablo_duzenle("vardiya_df", "Ad_Soyad", {
            "Tarih": st.column_config.DateColumn(format="DD.MM.YYYY"),
            "Durum": st.column_config.SelectboxColumn(options=GUNLUK_DURUMLAR),
        })
    with st.expander("Raporlar"):
        tablo_duzenle("raporlar_df", "Ad_Soyad")

# ---------------------------------------------------------------------
# 7) TANIMLAR (makine & iskele listeleri)
# ---------------------------------------------------------------------
with sekme_tanim:
    t1c, t2c = st.columns(2)
    for kolon, anahtar, baslik in ((t1c, "makineler_listesi", "Gemi Makineleri"), (t2c, "iskeleler_listesi", "İskeleler / Konumlar")):
        with kolon:
            st.subheader(baslik)
            with st.form(f"form_{anahtar}", clear_on_submit=True):
                yeni = st.text_input("Yeni ekle")
                if st.form_submit_button("Ekle"):
                    yeni = yeni.strip()
                    if yeni and yeni not in ss[anahtar]:
                        ss[anahtar].append(yeni)
                        kaydet()
                        st.rerun()
            silinecek = st.multiselect("Silinecekler", ss[anahtar], key=f"sil_{anahtar}")
            if silinecek and st.button("🗑️ Seçilenleri Sil", key=f"silbtn_{anahtar}"):
                ss[anahtar] = [x for x in ss[anahtar] if x not in silinecek]
                kaydet()
                st.rerun()
            st.write(", ".join(ss[anahtar]) if ss[anahtar] else "Liste boş.")

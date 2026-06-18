"""
OULAD — Davranışsal Çekilme Analizi Pipeline
============================================
Çevrimiçi öğrencilerin bırakma öncesi davranışsal kopuş anatomisini
event-aligned PELT analizi ile inceler.

Veri Seti: https://analyse.kmi.open.ac.uk/open-dataset
Gerekli dosyalar (aynı klasörde olmalı):
    studentVle.csv, studentRegistration.csv, studentInfo.csv,
    vle.csv, courses.csv

Çıktılar (outputs/ klasörüne kaydedilir):
    s1_kirilma_dagilimi.png
    s2_aktivite_kopus_dagilimi.png
    s3_kontrol_grubu_dagilimi.png
    istatistiksel_test_sonuclari.csv
    modul_bazli_test_sonuclari.csv
"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import ruptures as rpt
import seaborn as sns
from scipy import stats
from statsmodels.stats.multitest import multipletests

# ── ÇIKTI KLASÖRÜ ────────────────────────────────────────────────────────────
OUTPUT_DIR = "outputs"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ── AYARLAR ──────────────────────────────────────────────────────────────────
PELT_PEN       = 10      # PELT ceza parametresi
SMOOTHING_WIN  = 7       # Hareketli ortalama penceresi (gün)
LOOKBACK_DAYS  = 60      # Bırakma öncesi kaç günlük pencere analiz edilsin
MIN_GROUP_SIZE = 10      # İstatistiksel test için minimum grup büyüklüğü


# =============================================================================
# 1. VERİ YÜKLEME
# =============================================================================
print("=" * 60)
print("ADIM 1: Veriler yükleniyor...")
print("=" * 60)

studentVle          = pd.read_csv("studentVle.csv")
studentRegistration = pd.read_csv("studentRegistration.csv")
studentInfo         = pd.read_csv("studentInfo.csv")
vle                 = pd.read_csv("vle.csv")
courses             = pd.read_csv("courses.csv")

print(f"  studentVle          : {len(studentVle):,} satır")
print(f"  studentRegistration : {len(studentRegistration):,} satır")
print(f"  studentInfo         : {len(studentInfo):,} satır")
print(f"  vle                 : {len(vle):,} satır")


# =============================================================================
# 2. AKTİVİTE KATEGORİZASYONU
# =============================================================================
print("\nADIM 2: Aktivite kategorileri eşleniyor...")

activity_map = {
    'resource': 'Pasif_Icerik', 'oucontent': 'Pasif_Icerik',
    'url': 'Pasif_Icerik', 'subpage': 'Pasif_Icerik',
    'page': 'Pasif_Icerik', 'homepage': 'Pasif_Icerik',
    'glossary': 'Pasif_Icerik', 'sharedsubpage': 'Pasif_Icerik',
    'folder': 'Pasif_Icerik',
    'forumng': 'Sosyal_Etkilesim', 'oucollaborate': 'Sosyal_Etkilesim',
    'ouwiki': 'Sosyal_Etkilesim', 'ouilluminate': 'Sosyal_Etkilesim',
    'quiz': 'Olcme_Degerlendirme', 'questionnaire': 'Olcme_Degerlendirme',
    'externalquiz': 'Olcme_Degerlendirme'
}
vle["activity_category"] = vle["activity_type"].map(activity_map).fillna("diger")


# =============================================================================
# 3. BIRAKANLAR — ANA VERİ HAZIRLIĞI
# =============================================================================
print("\nADIM 3: Bırakan öğrenciler filtreleniyor ve veri birleştiriliyor...")

# Günlük tıklama toplamı
tıklamalar = studentVle.groupby(
    ["code_module", "id_student", "code_presentation", "date", "id_site"]
)["sum_click"].sum().reset_index()

# final_result ekle
student_kesit = studentInfo[
    ['id_student', 'code_module', 'code_presentation', 'final_result']
]
tıklamalar = pd.merge(
    tıklamalar, student_kesit,
    on=['id_student', 'code_module', 'code_presentation'],
    how='left'
)

# Kayıt silme tarihi ekle
tıklamalar = pd.merge(
    tıklamalar,
    studentRegistration[
        ["id_student", "code_module", "code_presentation", "date_unregistration"]
    ],
    on=["id_student", "code_module", "code_presentation"],
    how="left"
)

cekilenler = tıklamalar[tıklamalar["final_result"] == "Withdrawn"].copy()
print(f"  Bırakan öğrenci tıklama kaydı: {len(cekilenler):,}")


# =============================================================================
# 4. YARDIMCI FONKSİYONLAR
# =============================================================================

def zaman_penceresi_hazirla(df, date_col, unregistration_col,
                             group_cols, lookback=60):
    """
    Bırakma tarihini t=0 alarak geriye doğru [0, lookback] günlük
    kesintisiz zaman serisi oluşturur; eksik günlere 0 yazar.
    """
    df = df.copy()
    df["t"] = df[unregistration_col] - df[date_col]
    df = df[(df["t"] >= 0) & (df["t"] <= lookback)].copy()
    df["t"] = df["t"].astype(int)

    agg = df.groupby(group_cols + ["t"])["sum_click"].sum().reset_index()

    pivot = agg.pivot_table(
        index=group_cols, columns="t",
        values="sum_click", fill_value=0
    )
    pivot = pivot.reindex(columns=range(lookback + 1), fill_value=0)

    long = pivot.stack().reset_index(name="sum_click")
    long = long.sort_values(group_cols + ["t"]).reset_index(drop=True)
    return long


def smoothing_uygula(df, group_cols, window=7):
    """Gruplar içinde hareketli ortalama uygular."""
    df = df.copy()
    df["smoothed_click"] = df.groupby(group_cols)["sum_click"].transform(
        lambda x: x.rolling(window=window, min_periods=1).mean()
    )
    return df


def pelt_calistir(df, group_cols, pen=10, lookback=60):
    """
    Her grup için PELT algoritması çalıştırır.
    Kırılma noktasını bırakma anına kalan gün cinsinden döner.
    """
    results = []
    for keys, group in df.groupby(group_cols):
        group = group.sort_values("t")
        signal = group["smoothed_click"].values

        if np.sum(signal) == 0:
            continue
        try:
            algo = rpt.Pelt(model="rbf").fit(signal)
            result = algo.predict(pen=pen)
            if len(result) > 1:
                days_before = lookback - result[0]
                row = dict(zip(group_cols, keys if isinstance(keys, tuple) else [keys]))
                row["days_before_dropout"] = days_before
                results.append(row)
        except Exception:
            continue

    return pd.DataFrame(results)


# =============================================================================
# S1: GENEL KOPUŞ ZAMANI
# =============================================================================
print("\n" + "=" * 60)
print("S1: Genel kopuş zamanı analizi başlatılıyor...")
print("=" * 60)

s1_group_cols = ["id_student", "code_module", "code_presentation"]

s1_long = zaman_penceresi_hazirla(
    cekilenler, "date", "date_unregistration",
    s1_group_cols, lookback=LOOKBACK_DAYS
)
s1_long = smoothing_uygula(s1_long, s1_group_cols, window=SMOOTHING_WIN)

s1_results_df = pelt_calistir(s1_long, s1_group_cols, pen=PELT_PEN,
                               lookback=LOOKBACK_DAYS)

result_series = s1_results_df["days_before_dropout"]
median_day    = result_series.median()

print(f"  Analiz edilen öğrenci: {len(result_series):,}")
print(f"  Medyan kopuş zamanı  : {median_day} gün (bırakmadan önce)")

# — Grafik
plt.figure(figsize=(10, 6))
sns.histplot(result_series, bins=30, kde=True, color="skyblue")
plt.axvline(median_day, color="red", linestyle="dashed", linewidth=2,
            label=f'Medyan: {median_day}. Gün')
plt.title('S1: Öğrencilerin Genel Etkileşim Kopuş (Kırılma) Dağılımı',
          fontsize=14)
plt.xlabel('Bırakma Anına Kalan Gün Sayısı (Geriye Doğru)', fontsize=12)
plt.ylabel('Öğrenci Sayısı', fontsize=12)
plt.legend()
plt.grid(axis='y', alpha=0.5)
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, "s1_kirilma_dagilimi.png"), dpi=150)
plt.close()
print(f"  Grafik kaydedildi → {OUTPUT_DIR}/s1_kirilma_dagilimi.png")


# =============================================================================
# S2: AKTİVİTE TÜRÜNE GÖRE KOPUŞ
# =============================================================================
print("\n" + "=" * 60)
print("S2: Aktivite türlerine göre kopuş analizi başlatılıyor...")
print("=" * 60)

# Bırakanlara aktivite kategorisi ekle
cekilenler_vle = pd.merge(
    cekilenler, vle[['id_site', 'activity_category']],
    on='id_site', how='left'
)

s2_group_cols = ["id_student", "code_module", "code_presentation",
                 "activity_category"]

s2_long = zaman_penceresi_hazirla(
    cekilenler_vle, "date", "date_unregistration",
    s2_group_cols, lookback=LOOKBACK_DAYS
)
s2_long = smoothing_uygula(s2_long, s2_group_cols, window=SMOOTHING_WIN)
s2_long = s2_long[s2_long["activity_category"] != "diger"].copy()

s2_results_df = pelt_calistir(s2_long, s2_group_cols, pen=PELT_PEN,
                               lookback=LOOKBACK_DAYS)

summary_s2 = (
    s2_results_df.groupby('activity_category')['days_before_dropout']
    .agg(['median', 'mean', 'count'])
    .reset_index()
    .sort_values('median', ascending=False)
)
print("\n  --- S2: Aktivite Kopuş Sıralaması ---")
print(summary_s2.to_string(index=False))

# — Grafik
plt.figure(figsize=(12, 7))
sns.kdeplot(
    data=s2_results_df, x='days_before_dropout',
    hue='activity_category', fill=True,
    common_norm=False, palette='Set2', alpha=0.4, linewidth=2
)
colors = ['#66c2a5', '#fc8d62', '#8da0cb']
for i, cat in enumerate(s2_results_df['activity_category'].unique()):
    cat_median = s2_results_df[
        s2_results_df['activity_category'] == cat
    ]['days_before_dropout'].median()
    plt.axvline(cat_median, color=colors[i % len(colors)],
                linestyle='--', linewidth=1.5,
                label=f'{cat} Medyan: {cat_median}. Gün')
plt.title('S2: Aktivite Türlerine Göre Platformdan Kopuş Dağılımları',
          fontsize=14, fontweight='bold')
plt.xlabel('Bırakma Anına Kalan Gün Sayısı (Geriye Doğru)', fontsize=12)
plt.ylabel('Yoğunluk (Öğrenci Sıklığı)', fontsize=12)
plt.legend(title="Aktivite Kategorileri")
plt.grid(axis='x', alpha=0.3)
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, "s2_aktivite_kopus_dagilimi.png"),
            dpi=150)
plt.close()
print(f"\n  Grafik kaydedildi → {OUTPUT_DIR}/s2_aktivite_kopus_dagilimi.png")


# =============================================================================
# S3: KONTROL GRUBU (BAŞARILI ÖĞRENCİLER)
# =============================================================================
print("\n" + "=" * 60)
print("S3: Kontrol grubu analizi başlatılıyor (uzun sürebilir)...")
print("=" * 60)

# Ham tıklamalara aktivite kategorisi ekle
ham_tıklamalar = pd.merge(
    studentVle, vle[['id_site', 'activity_category']],
    on='id_site', how='left'
)

# Başarılı öğrenciler
basarili = studentInfo[
    studentInfo['final_result'].isin(['Pass', 'Distinction'])
][['id_student', 'code_module', 'code_presentation']]

# Bırakanların ders/dönem bazı medyan bırakma günü → yapay çapa
medyan_birakma = (
    studentRegistration[studentRegistration['date_unregistration'].notna()]
    .merge(
        studentInfo[studentInfo['final_result'] == 'Withdrawn'],
        on=['id_student', 'code_module', 'code_presentation']
    )
    .groupby(['code_module', 'code_presentation'])['date_unregistration']
    .median()
    .reset_index()
    .rename(columns={'date_unregistration': 'dummy_date_unregistration'})
)

hedef_kontrol = pd.merge(
    basarili, medyan_birakma,
    on=['code_module', 'code_presentation'], how='inner'
)

# Kayıt öncesine denk gelen yapay tarihleri çıkar
kayit_tarihleri = studentRegistration[[
    "id_student", "code_module", "code_presentation", "date_registration"
]]
hedef_kontrol = pd.merge(
    hedef_kontrol, kayit_tarihleri,
    on=["id_student", "code_module", "code_presentation"], how="left"
)
hedef_kontrol = hedef_kontrol[
    hedef_kontrol["dummy_date_unregistration"] >= hedef_kontrol["date_registration"]
].copy()
print(f"  Geçerli kontrol grubu büyüklüğü: {len(hedef_kontrol):,}")

# Kontrol grubu tıklama verisi
kontrol_tıklamalar = pd.merge(
    ham_tıklamalar, hedef_kontrol,
    on=['id_student', 'code_module', 'code_presentation'], how='inner'
)

s3_group_cols = ["id_student", "code_module", "code_presentation",
                 "activity_category"]

s3_long = zaman_penceresi_hazirla(
    kontrol_tıklamalar, "date", "dummy_date_unregistration",
    s3_group_cols, lookback=LOOKBACK_DAYS
)
s3_long = smoothing_uygula(s3_long, s3_group_cols, window=SMOOTHING_WIN)
s3_long = s3_long[s3_long["activity_category"] != "diger"].copy()

s3_results_df = pelt_calistir(s3_long, s3_group_cols, pen=PELT_PEN,
                               lookback=LOOKBACK_DAYS)

summary_s3 = (
    s3_results_df.groupby('activity_category')['days_before_dropout']
    .agg(['median', 'mean', 'count'])
    .reset_index()
    .sort_values('median', ascending=False)
)
print("\n  --- S3: Kontrol Grubu Kopuş Sıralaması ---")
print(summary_s3.to_string(index=False))

# — Grafik
plt.figure(figsize=(12, 7))
sns.kdeplot(
    data=s3_results_df, x='days_before_dropout',
    hue='activity_category', fill=True,
    common_norm=False, palette='Set1', alpha=0.4, linewidth=2
)
plt.title(
    'S3 (Kontrol Grubu): Başarılı Öğrencilerin Yapay Zamana Göre Dağılımları',
    fontsize=14, fontweight='bold'
)
plt.xlabel('Yapay Bırakma Anına Kalan Gün Sayısı (Geriye Doğru)', fontsize=12)
plt.ylabel('Yoğunluk (Öğrenci Sıklığı)', fontsize=12)
plt.grid(axis='x', alpha=0.3)
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, "s3_kontrol_grubu_dagilimi.png"),
            dpi=150)
plt.close()
print(f"\n  Grafik kaydedildi → {OUTPUT_DIR}/s3_kontrol_grubu_dagilimi.png")


# =============================================================================
# 5. İSTATİSTİKSEL TEST — GENEL (MANN-WHITNEY U)
# =============================================================================
print("\n" + "=" * 60)
print("İstatistiksel Test: Mann-Whitney U (Olcme_Degerlendirme)")
print("=" * 60)

birakanlar_olcme = s2_results_df[
    s2_results_df["activity_category"] == "Olcme_Degerlendirme"
]["days_before_dropout"]

kontrol_olcme = s3_results_df[
    s3_results_df["activity_category"] == "Olcme_Degerlendirme"
]["days_before_dropout"]

stat, p_value = stats.mannwhitneyu(
    birakanlar_olcme, kontrol_olcme, alternative="less"
)
n1, n2 = len(birakanlar_olcme), len(kontrol_olcme)
effect_size = 1 - (2 * stat) / (n1 * n2)

p_yorum = (
    "p < 0.001 → Son derece anlamlı" if p_value < 0.001 else
    "p < 0.01  → Çok anlamlı"        if p_value < 0.01  else
    "p < 0.05  → Anlamlı"            if p_value < 0.05  else
    "p >= 0.05 → Anlamlı değil"
)
r_yorum = (
    "Büyük etki" if abs(effect_size) >= 0.5 else
    "Orta etki"  if abs(effect_size) >= 0.3 else
    "Küçük etki"
)

print(f"  Bırakanlar    : n={n1}, medyan={birakanlar_olcme.median():.1f} gün")
print(f"  Kontrol grubu : n={n2}, medyan={kontrol_olcme.median():.1f} gün")
print(f"  U istatistiği : {stat:.1f}")
print(f"  p-değeri      : {p_value:.4f}  → {p_yorum}")
print(f"  Effect size   : {effect_size:.3f}  → {r_yorum}")

genel_test = pd.DataFrame([{
    "grup": "Bırakanlar", "n": n1,
    "medyan_gun": birakanlar_olcme.median()
}, {
    "grup": "Kontrol", "n": n2,
    "medyan_gun": kontrol_olcme.median()
}])
genel_test["Mann_Whitney_U"] = stat
genel_test["p_degeri"] = round(p_value, 4)
genel_test["effect_size"] = round(effect_size, 3)
genel_test["yorum"] = p_yorum
genel_test.to_csv(
    os.path.join(OUTPUT_DIR, "istatistiksel_test_sonuclari.csv"), index=False
)
print(f"\n  Sonuç kaydedildi → {OUTPUT_DIR}/istatistiksel_test_sonuclari.csv")


# =============================================================================
# 6. MODÜL BAZLI TEST (BH DÜZELTMELİ)
# =============================================================================
print("\n" + "=" * 60)
print("Modül bazlı test: BH düzeltmeli Mann-Whitney U...")
print("=" * 60)

def modul_testi(modul, s2_df, s3_df,
                kategori="Olcme_Degerlendirme",
                min_n=MIN_GROUP_SIZE):
    b = s2_df[(s2_df["code_module"] == modul) &
              (s2_df["activity_category"] == kategori)]["days_before_dropout"]
    k = s3_df[(s3_df["code_module"] == modul) &
              (s3_df["activity_category"] == kategori)]["days_before_dropout"]
    if len(b) < min_n or len(k) < min_n:
        return None
    stat_, p_ = stats.mannwhitneyu(b, k, alternative="less")
    es_ = 1 - (2 * stat_) / (len(b) * len(k))
    return {
        "code_module"   : modul,
        "birakan_n"     : len(b),
        "birakan_medyan": b.median(),
        "kontrol_n"     : len(k),
        "kontrol_medyan": k.median(),
        "fark_gun"      : k.median() - b.median(),
        "p_degeri"      : round(p_, 4),
        "effect_size"   : round(es_, 3),
        "anlamlilik"    : ("***" if p_ < 0.001 else
                           "**"  if p_ < 0.01  else
                           "*"   if p_ < 0.05  else "ns")
    }

modul_sonuclari = [
    r for modul in sorted(s2_results_df["code_module"].unique())
    if (r := modul_testi(modul, s2_results_df, s3_results_df)) is not None
]
modul_df = pd.DataFrame(modul_sonuclari).sort_values("fark_gun", ascending=False)

_, p_duzeltilmis, _, _ = multipletests(
    modul_df["p_degeri"].values, method="fdr_bh"
)
modul_df["p_duzeltilmis"] = p_duzeltilmis.round(4)
modul_df["anlamlilik_duzeltilmis"] = modul_df["p_duzeltilmis"].apply(
    lambda p: "***" if p < 0.001 else "**" if p < 0.01 else
              "*"   if p < 0.05  else "ns"
)

print(modul_df[[
    "code_module", "birakan_n", "fark_gun",
    "p_degeri", "anlamlilik",
    "p_duzeltilmis", "anlamlilik_duzeltilmis"
]].to_string(index=False))

modul_df.to_csv(
    os.path.join(OUTPUT_DIR, "modul_bazli_test_sonuclari.csv"), index=False
)
print(f"\n  Sonuç kaydedildi → {OUTPUT_DIR}/modul_bazli_test_sonuclari.csv")


# =============================================================================
# ÖZET
# =============================================================================
print("\n" + "=" * 60)
print("ANALİZ TAMAMLANDI")
print("=" * 60)
print(f"  S1 Medyan kopuş zamanı    : {median_day} gün")
print(f"  S2 Olcme_Deg. medyanı     : "
      f"{s2_results_df[s2_results_df['activity_category']=='Olcme_Degerlendirme']['days_before_dropout'].median()} gün")
print(f"  S3 Kontrol Olcme_Deg.     : "
      f"{kontrol_olcme.median()} gün")
print(f"  Fark (kontrol - bırakan)  : "
      f"{kontrol_olcme.median() - birakanlar_olcme.median():.0f} gün")
print(f"  p-değeri                  : {p_value:.4f}  ({p_yorum})")
print(f"\n  Tüm çıktılar '{OUTPUT_DIR}/' klasöründe.")

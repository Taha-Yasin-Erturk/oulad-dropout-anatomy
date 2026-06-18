---
title: "Çevrimiçi Öğrencilerde Davranışsal Çekilmenin Anatomisi"
subtitle: "Bırakma Öncesi Aktivite Düşüşünün Zamansal ve Türsel Analizi"
dataset: "OULAD (Open University Learning Analytics Dataset)"
date: "Mayıs 2026"

---

## 

## 1. Proje Tanımı ve Motivasyon

Bu proje, çevrimiçi eğitimde yüksek bırakma oranını iki geleneksel yaklaşımdan farklı bir perspektifle ele alır. Mevcut literatür bırakmayı ya bir **tahmin problemi** (kim bırakacak?) ya da bir **zamanlama problemi** (ne zaman bırakacak?) olarak ele almaktadır. Bu çalışma ise bırakmayı bir **süreç** olarak incelemekte ve bu sürecin davranışsal yapısını bireysel düzeyde betimlemektedir.

OULAD veri setinin bu proje için kritik avantajı, bırakma tarihinin gün düzeyinde kayıtlı olmasıdır. Bu özellik, bırakma tarihine göre *event-aligned* analiz yapılmasını mümkün kılmakta ve projenin metodolojik özgünlüğünün temelini oluşturmaktadır.

> **Araştırma Sorusu:** Çevrimiçi öğrenciler platformdan davranışsal olarak ne zaman, hangi aktivite türünde ve hangi sırayla kopmaktadır?

---

## 2. Teorik Çerçeve ve Hipotez

### Tinto'nun Entegrasyon Modeli (1975, 1993)

Projenin teorik zemini Tinto'nun Entegrasyon Modeli'ne dayanmaktadır. Tinto, yükseköğretimde bırakmayı akademik ve sosyal entegrasyon eksikliğiyle açıklar. Modele göre sosyal entegrasyon (akranlarla, öğretim üyeleriyle bağ), akademik entegrasyondan önce kırılır.

Bu teori çevrimiçi ortama taşındığında şu hipotezi üretir:

> **H₀:** Forum (sosyal etkilesim) aktivitesi düşüşü, içerik tüketimi ve ölçme/değerlendirme aktivitelerinden önce gerçekleşir.

### Destekleyici Teoriler

**Fredricks, Blumenfeld ve Paris (2004)** davranışsal çekilmeyi platforma erişimin azalması olarak tanımlar. Bu boyut OULAD'da doğrudan tıklama loglarıyla ölçülmektedir.

**Bandura'nın Öz-Yeterlilik Teorisi (1997):** Akademik görevlerde başarısızlık beklentisi önce o görevden çekilmeye, ardından genel motivasyon kaybına yol açar.

**Eccles'ın Beklenti-Değer Teorisi:** Görevin değeri düştüğünde önce o görevden, sonra genel katılımdan çekilme başlar.

---

## 3. Metodoloji

### Veri Seti

Open University Learning Analytics Dataset (OULAD), 2013-2014 yıllarına ait 32.000'den fazla öğrencinin kayıt bilgilerini, demografik verilerini ve 10 milyonun üzerinde platform tıklama logunu içermektedir. Veri setine https://analyse.kmi.open.ac.uk/open-dataset adresinden erişilebilir.

### Kullanılan Teknikler

Analiz Python (pandas, ruptures, scipy, seaborn, matplotlib) ile Jupyter Notebook ortamında geliştirilmiştir.

| Teknik                        | Amaç                                                                              |
| ----------------------------- | --------------------------------------------------------------------------------- |
| Event-Aligned Zaman Serisi    | Bırakma tarihini t=0 alarak tüm öğrencileri ortak eksende hizalama                |
| 7 Günlük Hareketli Ortalama   | Ham tıklama verisindeki gürültüyü azaltarak PELT için temiz sinyal üretme         |
| PELT Algoritması (ruptures)   | Her öğrencinin bireysel tıklama serisinde istatistiksel kırılma noktası tespiti   |
| Aktivite Kategorizasyonu      | 20 farklı aktivite türünü 3 makro kategoriye indirgeme                            |
| Kontrol Grubu Karşılaştırması | Başarılı öğrencilere yapay bırakma tarihi atayarak sinyalin özgüllüğünü test etme |
| Mann-Whitney U Testi          | Bırakanlar ile kontrol grubu arasındaki farkın istatistiksel anlamlılığını ölçme  |

### Aktivite Kategorizasyonu

OULAD'daki 20 farklı aktivite türü, teorik çerçeveyle hizalı 3 makro kategoriye indirgendi. 'Diğer' olarak sınıflandırılan aktiviteler istatistiksel güç yetersizliği nedeniyle analizden çıkarıldı (n=14).

| Kategori            | Aktivite Türleri                                                                   |
| ------------------- | ---------------------------------------------------------------------------------- |
| Pasif_Icerik        | resource, oucontent, url, subpage, page, homepage, glossary, sharedsubpage, folder |
| Sosyal_Etkilesim    | forumng, oucollaborate, ouwiki, ouilluminate                                       |
| Olcme_Degerlendirme | quiz, questionnaire, externalquiz                                                  |

---

## 4. Analiz Sonuçları

### S1 — Genel Kopuş Zamanı

PELT algoritması, bırakmadan önceki 60 günlük bireysel tıklama serileri üzerinde çalıştırıldı. Kırılma tespit edilebilen 1.209 öğrenci analiz kapsamına alındı.

| Metrik                | Değer               |
| --------------------- | ------------------- |
| Medyan kırılma zamanı | 30 gün              |
| Dağılım tipi          | Bimodal (heterojen) |
| 1. tepe               | ~20-25. gün         |
| 2. tepe               | ~35-40. gün         |
| Analiz edilen öğrenci | 1.209               |

![Şekil 1](1781359872911_image.png)
*Şekil 1. S1: Öğrencilerin genel etkileşim kopuş (kırılma) dağılımı. Kırmızı kesikli çizgi medyan kırılma noktasını (30. gün) göstermektedir.*

Dağılım incelendiğinde kritik bir bulgu öne çıktı: dağılım tek tepeli (homojen) değil, belirgin biçimde iki tepeli (bimodal). Bu heterojenlik, öğrenciler arasında en az iki farklı kopuş profilinin var olduğuna işaret etmektedir — 'erken kopanlar' ve 'geç kopanlar'.

### S2 — Aktivite Türlerine Göre Kopuş Sırası

20 aktivite türü 3 makro kategoriye indirgendi ve her kategori için bağımsız PELT analizi yapıldı. Amaç, Tinto hipotezinin test edilmesiydi: forum aktivitesi diğerlerinden önce düşmeli.

| Kategori            | Medyan (gün) | Ortalama (gün) | Öğrenci Sayısı |
| ------------------- | ------------ | -------------- | -------------- |
| Pasif_Icerik        | 30           | 29.6           | 1.154          |
| Sosyal_Etkilesim    | 30           | 28.9           | 596            |
| Olcme_Degerlendirme | 25           | 24.0           | 163            |
| diger               | 30           | 29.3           | 14             |

![Şekil 2](1781359901158_image.png)
*Şekil 2. S2: Aktivite türlerine göre platformdan kopuş dağılımları. Kesikli dikey çizgiler her kategorinin medyan kırılma noktasını göstermektedir.*

**S2 Değerlendirmesi:** Tinto hipotezi bu veriyle desteklenmedi. Sosyal_Etkilesim medyanı (30 gün) Pasif_Icerik medyanıyla (30 gün) aynı; herhangi bir öncelik sıralaması gözlemlenmedi. Olcme_Degerlendirme ise tek ayrışan kategori olarak öne çıktı: bırakma anına 5 gün daha yakın noktada kırılıyor (25. gün).

### S3 — Sinyal Özgüllüğü: Kontrol Grubu Doğrulaması

Kursu başarıyla tamamlayan öğrencilerden oluşan kontrol grubuna, ders/dönem bazında bırakanların medyan bırakma günü yapay çapa olarak atandı ve aynı pipeline uygulandı. Kontrol grubunda 7.829 kırılma noktası tespit edildi.

| Kategori            | Bırakanlar Medyanı | Kontrol Grubu Medyanı | Fark        |
| ------------------- | ------------------ | --------------------- | ----------- |
| Pasif_Icerik        | 30 gün             | 30 gün                | 0 gün       |
| Sosyal_Etkilesim    | 30 gün             | 35 gün                | -5 gün      |
| Olcme_Degerlendirme | 25 gün             | 35 gün                | -10 gün (!) |
| diger               | 30 gün             | 30 gün                | 0 gün       |

![Şekil 3](1781359915554_image.png)
*Şekil 3. S3: Başarılı öğrencilerin yapay zamana göre aktivite kopuş dağılımları (kontrol grubu). Bırakanlarla karşılaştırıldığında Olcme_Degerlendirme kategorisindeki 10 günlük fark dikkat çekicidir.*

**S3'ün en kritik bulgusu:** Olcme_Degerlendirme kategorisinde bırakanlar 25. günde koparken, kontrol grubu 35. günde kopuyor. 10 günlük bu fark ve yönünün tamamen zıt olması tesadüfle açıklanamaz — bu sinyal bırakanlara özgüdür.

---

## 5. İstatistiksel Doğrulama

Olcme_Degerlendirme kategorisindeki 10 günlük farkın istatistiksel anlamlılığı Mann-Whitney U testi ile doğrulandı. Test, bırakanların daha erken koptuğu yönlü hipoteze (one-tailed) göre kurgulandı. Çoklu modül karşılaştırmalarında Benjamini-Hochberg (FDR) düzeltmesi uygulandı.

> **Mann-Whitney U: p < 0.001 (son derece anlamlı)** | Effect Size (rank-biserial): orta-büyük etki

---

## 6. Hipotez Değerlendirmesi ve Yorumu

### Tinto Hipotezi — Red

Tinto hipotezi üç gerekçeyle reddedilmektedir:

- Bırakanlarda Sosyal_Etkilesim medyanı (30 gün) Pasif_Icerik medyanıyla (30 gün) aynı; herhangi bir öncelik sıralaması gözlemlenmedi.
- Kontrol grubunda Sosyal_Etkilesim daha erken düşüyor (35 gün). Sosyal etkileşimden erken kopuş bırakanlara özgü değil; başarılı öğrencilerde de görülüyor.
- OULAD'da forum tıklamasının okuma mı, yazma mı, tepki mi içerdiği bilinmiyor. Tinto'nun modelindeki aktif sosyal katılım bu veriyle tam olarak ölçülemiyor.

### Alternatif Bulgu — Akademik Kopuş Önceliği

Tinto hipotezi reddedilirken veri beklenmedik ama tutarlı bir örüntü ortaya koydu: bırakanlar ölçme ve değerlendirme aktivitelerini (quiz, sınav) kontrol grubuna kıyasla 10 gün daha erken bırakıyor.

Bu bulgu iki teoriyle tutarlıdır:

- **Bandura'nın Öz-Yeterlilik Teorisi (1997):** Quiz ve sınavlar öğrencinin kendini ölçtüğü en doğrudan anlardır. Buradan çekilmek 'artık başaramayacağımı kabul ettim' sinyali olabilir.
- **Eccles'ın Beklenti-Değer Teorisi:** Görevin değeri düştüğünde önce o görevden, sonra genel katılımdan çekilme başlar.

---

## 7. Nihai Sonuç

Bırakmadan önce platformdan davranışsal kopuşun Tinto'nun sosyal entegrasyon modeli çerçevesinde forum aktivitesinde başladığı hipotezi bu veriyle desteklenmedi. Bunun yerine bırakanlara özgü sinyal ölçme ve değerlendirme aktivitelerinde gözlemlendi: bırakanlar quiz ve sınav aktivitelerini kontrol grubuna kıyasla 10 gün daha erken bırakıyor. Bu bulgu davranışsal kopuşun sosyal değil, akademik boyuttan başladığına işaret etmektedir.

| Araştırma Sorusu                 | Sonuç                                                                             |
| -------------------------------- | --------------------------------------------------------------------------------- |
| S1: Ne zaman kopuluyor?          | Medyan 30 gün; dağılım bimodal ve heterojen. Tek tip kopuş profili yok.           |
| S2: Hangi aktivite önce düşüyor? | Tinto hipotezi desteklenmedi. Olcme_Degerlendirme tek ayrışan kategori (25. gün). |
| S3: Sinyal bırakanlara özgü mü?  | Olcme_Degerlendirme'de evet: bırakanlar 10 gün daha erken kopuyor (25 vs 35 gün). |

---

## 8. Sınırlılıklar

- **Nedensellik yok:** Davranışsal düşüş ile bırakma kararı arasındaki yön belirlenemez; bulgular betimleyicidir.
- **Forum aktivitesinin niteliği bilinmiyor:** Tıklama verisi okuma mı, yazma mı, tepki mi içerdiğini ayırt etmiyor; aktif sosyal katılım tam olarak ölçülemiyor.
- **Veri dönemi:** 2013-2014 verisi güncelliğini yitirmiş olabilir; sayısal bulgular Open University VLE'sine özgü olsa da metodoloji genellenebilir niteliktedir.
- **Gözlemlenemeyen faktörler:** İş kaybı, sağlık sorunları gibi dışsal etkenler davranışsal sinyal üretemeyen 'sessiz bırakan' grubunu etkileyebilir.
- **Pen parametresi:** PELT algoritmasında kullanılan pen=10 değeri duyarlılık analizi ile doğrulanmış olmakla birlikte farklı veri setlerinde yeniden kalibre edilmesi gerekebilir.

---



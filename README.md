# Toolshop QA

Practice Software Testing Toolshop üzerinde ürün seçimi, stok kontrolü, sepet ve misafir ödeme akışını tarayıcı üzerinden doğrulayan Selenium + pytest projesi.

> **Demo ortamı:** Testler `https://practicesoftwaretesting.com` eğitim/demo sitesinde çalışır. Checkout testi, site tarafından kabul edilen örnek kart bilgileriyle demo siparişi tamamlar; gerçek kart veya gerçek ödeme bilgisi kullanmayın.

## Gereksinimler

- Python 3.10+
- Google Chrome
- ChromeDriver (Selenium Manager uygun sürücüyü otomatik yönetir)

## Kurulum (Windows PowerShell)

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

## Testleri çalıştırma

Tarayıcı görünür modda açılır ve uçtan uca senaryoyu yürütür:

```powershell
python -m pytest -v -s
```

Her çalıştırmada `reports\test-report.html` altında paylaşılabilir, tek dosyalık bir HTML raporu üretilir. Raporda pass/fail/skip grafiği, test süreleri, hedef URL, çalışma modu ve hata/skip detayları bulunur; dışarıdan görsel veya servis yüklemez. Raporu tarayıcıda aç:

```powershell
Start-Process .\reports\test-report.html
```

Başka bir dosya konumu seçmek için:

```powershell
python -m pytest -v -s --html-report reports\demo-run.html
```

Tek test dosyasını çalıştırmak için:

```powershell
python -m pytest -v -s tests\test_open.py
```

Ürün sayfasında `Stokta yok`/`Out of stock` görünürse test tıklamaya çalışmadan durur. Terminalde bunun test hatası değil, stok nedeniyle atlanan akış olduğu açıkça gösterilir. Pytest sonucu `SKIPPED` olur (başarısız `FAILED` değil); aynı sonuç ve açıklama HTML raporunda da görünür:

```powershell
python -m pytest -v -s
```

## Canlı ortamda güvenli kontrol

Hedef adresi `TOOLSHOP_BASE_URL` ile ver. Canlı kontrol kipinde test ürünü görüntüler, miktarı artırır, sepete ekler ve sepet miktarını doğrular; **checkout veya ödeme adımına ilerlemez**. Ürün sepete ekleme sepet oturumunu değiştirebilir; test yalnızca test hesabında/izinli test ortamında çalıştırılmalıdır.

```powershell
$env:TOOLSHOP_BASE_URL = "https://practicesoftwaretesting.com"
$env:TOOLSHOP_LIVE_MODE = "1"
python -m pytest -v -s -rs
```

`TOOLSHOP_LIVE_MODE` etkinse sepet doğrulamasından sonra pytest sonucu `skipped` görünür; skip nedeni checkout'un bilerek çalıştırılmadığını açıklar. `practicesoftwaretesting.com` eğitim/demo sitesidir, şirket üretim sitesi değildir. Gerçek üretim adresi ancak yetki ve güvenli test planı varsa kullanılmalıdır. Demo dışındaki adreslerde ödeme akışı ayrıca engellenir.

Ortam değişkenleri yalnızca geçerli PowerShell oturumu için ayarlanır. Varsayılan adres `https://practicesoftwaretesting.com`'dur.

## Test akışı

1. Ürün detay sayfasını doğrular.
2. Üründe stok yoksa terminal ve HTML raporuna anlaşılır skip nedeni yazar.
3. Stok varsa miktarı artırır, sepete ekler ve sepet toplamını/miktarını doğrular.
4. Varsayılan demo modunda misafir checkout, fatura adresi ve demo ödeme/sipariş onayını doğrular.
5. Canlı modda checkout ve ödeme adımlarını çalıştırmadan testi sonlandırır.

## Postman API testleri

`Toolshop API Tests.postman_collection.json` koleksiyonunu Postman'a içe aktararak aşağıdaki salt-okunur API senaryolarını çalıştırabilirsin:

- Ürün listesinin başarılı ve JSON formatında dönmesi
- `pliers` aramasının ürün listesi döndürmesi ve sonuçların arama terimiyle eşleşmesi
- Belirli bir ürünün detaylarının ve kimliğinin doğrulanması
- Geçersiz ürün kimliği için `404` ve hata mesajı doğrulaması

Koleksiyonu Postman arayüzünde seçip **Run** ile toplu çalıştırabilir veya Newman ile CLI'dan çalıştırabilirsin. Newman ve HTML raporlayıcısı kurulu olmalıdır:

```powershell
npm install -g newman newman-reporter-htmlextra
newman run ".\Toolshop API Tests.postman_collection.json" --reporters "cli,htmlextra,json" --reporter-htmlextra-export ".\Toolshop-QA-Report.html" --reporter-htmlextra-title "Toolshop-QA Report" --reporter-json-export ".\Toolshop-QA-Report.json"
```

Komut, terminal özetinin yanı sıra HTML ve JSON raporlarını proje kökünde üretir. Bu repodaki mevcut çalıştırma çıktıları: [Newman HTML raporu](Toolshop-QA-Report.html) ve [Newman JSON raporu](Toolshop-QA-Report.json). HTML raporu tarayıcıda açmak için:

```powershell
Start-Process .\Toolshop-QA-Report.html
```

## Proje yapısı

```text
config/
  config.py                 Ortam adresi ve güvenli çalışma modu
pages/
  base_page.py              Ortak Selenium işlemleri
  checkout_page.py          Misafir checkout, adres ve demo ödeme adımları
  login_page.py             Ürün kataloğundan ürüne geçiş
  product_basket_page.py    Ürün miktarı, stok bildirimi ve sepete ekleme
  product_control.py        Sepet kontrolleri
tests/
  test_open.py              Uçtan uca alışveriş testi
conftest.py                 Tarayıcı fixture'ı ve temizleme
reporting.py                Grafik özetli, bağımsız HTML test raporu
pytest.ini                  Test işaretleri
requirements.txt            Python bağımlılıkları
Toolshop API Tests.postman_collection.json
                            Postman API test koleksiyonu
Toolshop-QA-Report.html     Newman HTML raporu
Toolshop-QA-Report.json     Newman JSON raporu
.gitignore                  Üretilen raporlar ve yerel dosyalar
```

## Test verileri

Checkout'ta yalnızca demo için üretilmiş bilgiler kullanılır: `qa.checkout@example.com`, `Taylor Test`, örnek adres ve kart formunun doğrulamasını geçen yaygın test kartı numarası `4111-1111-1111-1111`. Bu verileri gerçek bir ödeme sisteminde kullanmayın.

## Paylaşım ve kapsam

HTML raporu `reports\test-report.html` konumunda yerel üretilir ve `.gitignore` ile repoya otomatik eklenmesi engellenir. GitHub issue/PR eki ya da LinkedIn paylaşımı öncesinde hedef adresi, hata ayrıntılarını ve raporda gösterilen diğer bilgileri gözden geçirip gerekirse anonimleştir. Ürün stokta olmadığında raporda `SKIPPED` görünmesi beklenen bir durumdur; `FAILED` ile karıştırılmamalıdır.

Postman/Newman API testleri Selenium UI otomasyonundan ayrı çalışır. Mevcut koleksiyon ürün listeleme, arama, ürün detayı ve geçersiz ürün yanıtlarını kapsar.

> **AI katkı notu:** Bu projedeki kod geliştirme ve dokümantasyon sürecinde GitHub Copilot'tan yardım alınmıştır. Senaryolar ve değişiklikler proje sahibi tarafından gözden geçirilip çalıştırılarak doğrulanmalıdır.

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

Her çalıştırmada `reports\test-report.html` altında paylaşılabilir, tek dosyalık bir HTML raporu ve `reports\test-results.xml` altında JUnit XML raporu üretilir. HTML raporunda pass/fail/skip grafiği, test süreleri, hedef URL, çalışma modu ve hata/skip detayları bulunur; dışarıdan görsel veya servis yüklemez. GitHub’da şu anki raporları [HTML raporu](reports/test-report.html) ve [JUnit XML raporu](reports/test-results.xml) bağlantılarından görebilirsin. Bu raporlar son test çalıştırmasının çıktıları olarak repoda paylaşılır; yeni çalıştırmadan sonra güncel raporu da göndermek için değişen rapor dosyalarını commit edip push et. Raporlarda oturum/sepet kimliği yer almaz. HTML raporunu tarayıcıda aç:

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

Koleksiyondaki ürün detayı isteği, önceki ürün listesi isteğinin `pliers01.avif` ürününden aldığı güncel kimliği kullanır; koleksiyonu baştan sırayla çalıştır.

Canlı Swagger dokümantasyonu `https://api.practicesoftwaretesting.com/api/documentation` adresindedir. Dokümantasyon ürün listeleme/detay endpoint’lerine ek olarak sepet oluşturma (`POST /carts`), sepete ürün ekleme (`POST /carts/{id}`), sepeti okuma (`GET /carts/{cartId}`), miktar güncelleme ve silme endpoint’lerini tanımlar. `TC-CART-UIAPI-001`, sepet oluşturma ve ürün ekleme işlemlerini Selenium UI üzerinden yapar; UI’nın kendi oturumunda oluşturduğu sepeti `GET /carts/{cartId}` ile doğrular. Test, bağımsız bir API sepeti oluşturup UI sepetiyle aynıymış gibi karşılaştırmaz.

## UI + API ürün tutarlılık testi

`tests/test_ui_api_product.py`, API ürün listesinden mevcut `LoginPage` POM’unun açtığı ürün görseliyle eşleşen ürünü bulur, ürün detay endpoint’ini çağırır ve Selenium ile aynı ürün sayfasındaki ürün adı, fiyat ve stok durumunu karşılaştırır. Stokta olmama bilgisi API/UI arasında tutarlıysa test başarılı olur; sepete ekleme yapılmaz. API bağlantı/servis hataları ürün tutarsızlığı olarak değerlendirilmez.

Mevcut UI ve API testlerini birlikte çalıştırmak, özel HTML raporu ile JUnit XML çıktısını üretmek için:

```powershell
python -m pytest -v -s
```

`reports\test-report.html` içinde test kimliği, adımlar, beklenen/gerçekleşen değerler ve hata ayrıntıları; `reports\test-results.xml` içinde JUnit sonuçları yer alır.

## UI + API sepet doğrulaması

`tests/test_cart_ui_api.py`, `TC-CART-UIAPI-001` senaryosunu uygular:

1. Salt-okunur ürün listeleme ve detay endpoint’lerinden stokta olan gerçek ürünü seçer. Ürün stokta değilse sepete ekleme yapmadan testi `SKIPPED` olarak raporlar.
2. `LoginPage.click_product_by_id()` ile Selenium üzerinden aynı ürünün sayfasını açar; POM stok durumunu kontrol etmeden sepete ekleme yapmaz.
3. Sepete eklemeyi mevcut `BasketPage.click_add_to_cart_page()` metodu ile tarayıcıdan gerçekleştirir.
4. Tarayıcı `sessionStorage` alanındaki gerçek `cart_id` değerini alır ve `GET /carts/{cartId}` çağrısıyla aynı sepetin ürün kimliği ve miktarını doğrular.

Sepet API'siyle UI oturumunun ilişkisi varsayılmaz: API isteğinde yeni sepet oluşturulmaz, kimlik doğrudan UI oturumundan okunur ve aynı kimlikle API sepeti sorgulanır. Test, tarayıcıda önceden sepet varsa mevcut veriyi değiştirmemek için sepet ekleme adımını atlar. API ortam/bağlantı hataları ürün veya sepet tutarsızlığı olarak değerlendirilmez.

Ürün bilgisi tutarlılık testi (`TC-UIAPI-001`), sepet testi (`TC-CART-UIAPI-001`) ve mevcut Selenium akışını birlikte çalıştır:

```powershell
python -m pytest -v -s -rs
```

Yalnızca sepet UI + API testini çalıştır:

```powershell
python -m pytest -v -s -rs tests\test_cart_ui_api.py
```

### Neden UI ve API aynı pytest çatısı altında?

UI testi kullanıcının gördüğü ve yaptığı işlemi, API kontrolü ise sunucunun gerçek ürün/sepet verisini doğrular. Aynı senaryo ve raporda birleştirildiklerinde test, yalnızca ekranın çalıştığını veya endpoint’in yanıt verdiğini değil, ikisinin aynı ürün ve aynı sepet durumu üzerinde uzlaştığını da denetler. Birleştirilmeselerdi bu iki test ayrı ayrı başarılı görünürken UI ile API arasındaki ürün kimliği veya sepet miktarı uyuşmazlığı fark edilmeyebilir; sonuçları ilişkilendirmek ve hatayı izlemek de daha zor olurdu. Ortak pytest çatısı, bu kontrolleri tek komut ve tek HTML/JUnit sonuç setiyle çalıştırır; mevcut Selenium ve Postman testlerinin yerini almaz.

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
  test_ui_api_product.py    TC-UIAPI-001 ürün/API tutarlılığı
  test_cart_ui_api.py       TC-CART-UIAPI-001 sepet/API doğrulaması
conftest.py                 Tarayıcı fixture'ı ve temizleme
reporting.py                Ortak adım detaylı HTML test raporu
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

HTML ve JUnit raporları `reports\test-report.html` ve `reports\test-results.xml` konumlarında üretilir ve repoda paylaşılır. GitHub issue/PR eki ya da LinkedIn paylaşımı öncesinde hedef adresi, hata ayrıntılarını ve raporda gösterilen diğer bilgileri gözden geçirip gerekirse anonimleştir. Ürün stokta olmadığında raporda `SKIPPED` görünmesi beklenen bir durumdur; `FAILED` ile karıştırılmamalıdır.

Postman/Newman koleksiyonu mevcut salt-okunur ürün listeleme, arama, ürün detayı ve geçersiz ürün yanıtlarını ayrı olarak kapsar. Python UI + API testleri ise aynı pytest çalıştırmasında ve aynı HTML/JUnit raporları altında yürütülür.

> **AI katkı notu:** Bu projedeki kod geliştirme ve dokümantasyon sürecinde GitHub Copilot'tan yardım alınmıştır. Senaryolar ve değişiklikler proje sahibi tarafından gözden geçirilip çalıştırılarak doğrulanmalıdır.

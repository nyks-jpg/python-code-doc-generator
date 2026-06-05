# Python Code Doc-Generator

**Python Code Doc-Generator**, Python projelerindeki fonksiyonları statik analiz ile tarayan ve her fonksiyon için okunabilir dokümantasyon üreten hafif bir komut satırı aracıdır.

Araç, bir `.py` dosyasını veya klasörü analiz eder; fonksiyon adlarını, imzaları, parametreleri, dönüş anotasyonlarını, dekoratörleri, doğrudan fırlatılan hataları ve mevcut docstring'leri çıkarır. Ardından bu bilgileri Markdown veya JSON formatında düzenli bir çıktıya dönüştürür.

## Neden Bu Proje?

Modern yazılım projelerinde dokümantasyon çoğu zaman koddan sonra gelir; bazen hiç gelmez. Bu proje, özellikle açık kaynak Python projelerinde fonksiyon seviyesinde başlangıç dokümantasyonu üretmeyi kolaylaştırmak için tasarlandı.

Python Code Doc-Generator şu amaçlara odaklanır:

- Yeni geliştiricilerin bir kod tabanını daha hızlı anlamasına yardımcı olmak.
- Mevcut Python dosyalarından otomatik ve tutarlı dokümantasyon üretmek.
- Açık kaynak projelerde bakım, inceleme ve katkı süreçlerini kolaylaştırmak.
- Hafif, bağımlılıksız ve terminal üzerinden kullanılabilir bir geliştirici aracı sunmak.

Bu araç bir yapay zeka servisinden yanıt almak zorunda değildir; ilk sürüm, Python'un yerleşik `ast` modülüyle statik analiz yapar. Bu sayede hızlı çalışır, çevrimdışı kullanılabilir ve hassas kodların üçüncü taraf servislere gönderilmesini gerektirmez.

## Özellikler

- Dosya veya klasör tarama desteği.
- Recursive klasör analizi.
- Fonksiyon, metot ve asenkron fonksiyon tespiti.
- Parametre, tip anotasyonu ve varsayılan değer çıkarımı.
- Dönüş tipi anotasyonu analizi.
- Dekoratör ve doğrudan `raise` kullanımı tespiti.
- Mevcut docstring'leri özetleme.
- Türkçe ve İngilizce açıklama üretimi.
- Markdown ve JSON çıktı formatları.
- Temiz hata yönetimi ve CI dostu çıkış kodları.

## Nasıl Kurulur?

Projeyi klonlayın:

```bash
git clone https://github.com/kullanici-adiniz/python-code-doc-generator.git
cd python-code-doc-generator
```

İsteğe bağlı olarak sanal ortam oluşturun:

```bash
python -m venv .venv
source .venv/bin/activate
```

Windows PowerShell için:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Bağımlılıkları kurun:

```bash
python -m pip install -r requirements.txt
```

> Not: İlk sürüm yalnızca Python standart kütüphanesini kullanır. `requirements.txt` dosyası, kurulum akışını standart tutmak için projede yer alır.

## Örnek Kullanım

Tek bir Python dosyasını analiz etmek:

```bash
python main.py path/to/example.py
```

Bir klasördeki tüm Python dosyalarını analiz etmek:

```bash
python main.py path/to/project
```

Markdown çıktısını dosyaya yazmak:

```bash
python main.py path/to/project --output DOCUMENTATION.md
```

JSON formatında çıktı almak:

```bash
python main.py path/to/project --format json --output docs.json
```

İngilizce açıklama üretmek:

```bash
python main.py path/to/project --language en
```

Private fonksiyonları da dahil etmek:

```bash
python main.py path/to/project --include-private
```

Sadece belirtilen klasörün üst seviyesindeki `.py` dosyalarını taramak:

```bash
python main.py path/to/project --no-recursive
```

## Örnek Çıktı

```markdown
### `build_signature`

- Tür: `bir fonksiyondur`
- Satır: `364-376`
- İmza: `def build_signature(name: str, parameters: Sequence[ParameterDoc], returns: str | None, *, is_async: bool) -> str`
- Özet: `build_signature` mevcut docstring'e göre şunu yapar: Build a compact function signature for documentation output.
- Parametreler:
  - `name` (kind `positional-or-keyword`, type `str`)
  - `parameters` (kind `positional-or-keyword`, type `Sequence[ParameterDoc]`)
  - `returns` (kind `positional-or-keyword`, type `str | None`)
- Dönüş: `str`
```

## Proje Yapısı

```text
.
|-- main.py
|-- requirements.txt
|-- README.md
|-- CONTRIBUTING.md
`-- LICENSE
```

## Yol Haritası

- Daha gelişmiş doğal dil açıklamaları.
- Sınıf seviyesinde dokümantasyon üretimi.
- Modül bağımlılık grafiği çıkarımı.
- Markdown şablon özelleştirme.
- GitHub Actions ile otomatik dokümantasyon güncelleme.
- İsteğe bağlı LLM entegrasyonu.

## Katkıda Bulunma

Katkılar memnuniyetle karşılanır. Hata bildirimi, özellik önerisi, dokümantasyon iyileştirmesi veya kod katkısı göndermek için lütfen önce `CONTRIBUTING.md` dosyasını okuyun.

Önerilen katkı alanları:

- Daha iyi fonksiyon açıklaması üreten heuristikler.
- Yeni çıktı formatları.
- Test kapsamının genişletilmesi.
- Örnek projeler ve kullanım senaryoları.
- Dokümantasyon kalitesinin artırılması.

## Lisans

Bu proje MIT lisansı ile lisanslanmıştır. Ayrıntılar için `LICENSE` dosyasına bakın.

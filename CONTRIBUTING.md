# Katkıda Bulunma Rehberi

Python Code Doc-Generator'a katkı vermek istediğiniz için teşekkürler. Bu proje, açık kaynak topluluğunun kolayca inceleyebileceği, geliştirebileceği ve kendi iş akışlarına uyarlayabileceği sade bir geliştirici aracı olmayı hedefler.

## Davranış Beklentisi

Lütfen tüm tartışmalarda saygılı, açık ve çözüm odaklı bir iletişim kurun. Fikir ayrılıkları normaldir; önemli olan teknik gerekçeleri net açıklamak ve projeyi birlikte daha iyi hale getirmektir.

## Katkı Türleri

Aşağıdaki katkılar değerlidir:

- Hata bildirimi.
- Yeni özellik önerisi.
- Kod iyileştirmesi.
- Dokümantasyon düzeltmesi.
- Örnek kullanım senaryosu.
- Test ekleme veya mevcut testleri iyileştirme.

## Geliştirme Ortamı

Projeyi kendi hesabınıza fork edin ve yerel makinenize klonlayın:

```bash
git clone https://github.com/kullanici-adiniz/python-code-doc-generator.git
cd python-code-doc-generator
```

Sanal ortam oluşturmanız önerilir:

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

## Branch Oluşturma

Her değişiklik için ayrı bir branch oluşturun:

```bash
git checkout -b feature/kisa-aciklama
```

Hata düzeltmeleri için:

```bash
git checkout -b fix/kisa-aciklama
```

## Kod Standartları

- Kod okunabilir, küçük fonksiyonlara ayrılmış ve tip ipuçlarıyla desteklenmiş olmalıdır.
- Yeni davranışlar mümkün olduğunca CLI üzerinden test edilebilir olmalıdır.
- Hata mesajları kullanıcıya ne olduğunu ve ne yapması gerektiğini açıkça anlatmalıdır.
- Gereksiz bağımlılık eklemekten kaçının.
- Değişiklikler dar kapsamlı ve amaca yönelik olmalıdır.

## Test ve Doğrulama

Pull request açmadan önce en azından aşağıdaki kontrolleri çalıştırın:

```bash
python main.py main.py
python main.py main.py --format json
python main.py main.py --language en
```

Yeni bir özellik eklediyseniz README içinde kısa bir kullanım örneği eklemeyi değerlendirin.

## Pull Request Süreci

1. Repository'yi fork edin.
2. Yeni bir branch oluşturun.
3. Değişikliklerinizi küçük, anlaşılır commit'ler halinde yapın.
4. Gerekli kontrolleri yerelde çalıştırın.
5. GitHub üzerinden pull request açın.
6. PR açıklamasında neyi değiştirdiğinizi ve neden değiştirdiğinizi net şekilde belirtin.

PR açıklamanızda şunlara yer vermeniz önerilir:

- Değişikliğin kısa özeti.
- Çözdüğü issue varsa bağlantısı.
- Test veya manuel doğrulama çıktısı.
- Geriye dönük uyumluluk riski varsa açıklaması.

## Issue Açma

Hata bildirirken lütfen şu bilgileri ekleyin:

- Kullandığınız Python sürümü.
- İşletim sistemi.
- Çalıştırdığınız komut.
- Beklenen davranış.
- Gerçekleşen davranış.
- Mümkünse küçük bir örnek Python dosyası.

Özellik önerilerinde, çözmek istediğiniz problemi ve önerdiğiniz davranışı kısa bir örnekle anlatmanız yeterlidir.

## Commit Mesajları

Kısa ve açıklayıcı commit mesajları tercih edilir:

```text
Add JSON output support
Fix private function filtering
Improve README examples
```

## Lisans

Bu projeye katkıda bulunarak katkılarınızın MIT lisansı kapsamında yayınlanmasını kabul etmiş olursunuz.

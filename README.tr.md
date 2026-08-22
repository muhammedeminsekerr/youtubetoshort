# Kliphane 🎬

[🇬🇧 English](README.md) | 🇹🇷 Türkçe

YouTube video bağlantısı yapıştır, **Kliphane** videoyu indirsin, dinlesin,
en ilgi çekici anları yapay zekâ ile bulsun ve bunları altyazılı, dikey
(9:16) shorts kliplerine dönüştürsün — paylaşmaya hazır.

- **İndirme:** [yt-dlp](https://github.com/yt-dlp/yt-dlp)
- **Transkript:** [faster-whisper](https://github.com/SYSTRAN/faster-whisper) (yerel, ücretsiz)
- **En iyi anları seçme:** [Groq](https://console.groq.com) (ücretsiz, varsayılan) veya [Claude API](https://console.anthropic.com) (ücretli, isteğe bağlı)
- **Kesim & dikey format:** ffmpeg (bulanık arka plan + ortalanmış görüntü + gömülü altyazı)
- **Arayüz:** FastAPI + Jinja2 + vanilla JS (framework yok, tek sayfa)

Her şey kendi bilgisayarınızda çalışır; videolar sadece `downloads/` ve
`outputs/` klasörlerinizde tutulur, hiçbir yere otomatik yüklenmez.

## Gereksinimler

- Python 3.10+
- [ffmpeg](https://ffmpeg.org/download.html) sisteminizde kurulu olmalı ve `PATH`'te olmalı
  - macOS: `brew install ffmpeg`
  - Ubuntu/Debian: `sudo apt install ffmpeg`
  - Windows: [ffmpeg.org](https://ffmpeg.org/download.html) üzerinden indirip PATH'e ekleyin
- Bir [Groq API anahtarı](https://console.groq.com/keys) — **tamamen ücretsiz**, kredi kartı istemiyor

## Kurulum

```bash
git clone <repo-url>
cd youtube-shorts-generator

python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

pip install -r requirements.txt

cp .env.example .env
# .env dosyasını açıp GROQ_API_KEY değerini kendi (ücretsiz) anahtarınızla değiştirin
```

## Çalıştırma

```bash
python run.py
```

Tarayıcıda [http://localhost:8000](http://localhost:8000) adresini açın.

İlk çalıştırmada `faster-whisper` seçtiğiniz Whisper modelini otomatik
indirir (varsayılan `small`, ~500 MB) — bu yalnızca bir kere olur.

## Nasıl çalışır

1. **İndir** — yt-dlp videoyu en yüksek uygun kalitede (≤1080p) indirir.
2. **Dinle & analiz et** — faster-whisper konuşmayı zaman damgalı metne
   çevirir; bu metin bir LLM'e (varsayılan: Groq, ücretsiz) gönderilir ve
   kendi başına anlaşılır, güçlü bir açılışla başlayan en fazla N klip
   önerisi (başlangıç/bitiş saniyesi, başlık, kanca cümlesi) JSON olarak
   geri alınır.
3. **Kes & formatla** — her öneri ffmpeg ile kesilir, 1080×1920 dikey
   formata (bulanıklaştırılmış arka plan + ortalanmış orijinal görüntü)
   dönüştürülür ve o aralığa denk gelen transkript otomatik altyazı olarak
   gömülür.

## Yapılandırma (`.env`)

| Değişken | Açıklama | Varsayılan |
|---|---|---|
| `LLM_PROVIDER` | `groq` (ücretsiz) veya `anthropic` (ücretli) | `groq` |
| `GROQ_API_KEY` | Groq API anahtarınız (LLM_PROVIDER=groq ise zorunlu) | — |
| `GROQ_MODEL` | Groq üzerindeki model adı | `openai/gpt-oss-120b` |
| `ANTHROPIC_API_KEY` | Claude API anahtarınız (LLM_PROVIDER=anthropic ise zorunlu) | — |
| `ANTHROPIC_MODEL` | Klip seçimi için kullanılacak Claude modeli | `claude-sonnet-5` |
| `WHISPER_MODEL` | `tiny`/`base`/`small`/`medium`/`large-v3` | `small` |
| `WHISPER_DEVICE` | `cpu` veya `cuda` | `cpu` |
| `WHISPER_COMPUTE_TYPE` | `int8`, `float16` vb. | `int8` |
| `BURN_SUBTITLES` | Kliplere altyazı gömülsün mü | `true` |

## Neden Groq (ücretsiz)?

Groq, açık kaynak modelleri (Llama ve GPT-OSS gibi) kendi özel donanımında
çalıştırıyor ve kredi kartı istemeden, gerçekten ücretsiz bir API sunuyor
(dakikada/günde belirli istek sınırları var ama bu proje için fazlasıyla
yeterli — video başına yalnızca bir istek atıyoruz). [console.groq.com](https://console.groq.com)
üzerinden sadece e-posta ile saniyeler içinde anahtar alabilirsiniz.

Groq'un model listesi zamanla değişiyor, eski modeller kaldırılabiliyor —
"model not found" gibi bir hata alırsanız
[console.groq.com/docs/models](https://console.groq.com/docs/models)
adresinden güncel listeye bakıp `.env`'deki `GROQ_MODEL` değerini ona göre
güncelleyin.

Daha yüksek kalite isterseniz `.env` dosyasında `LLM_PROVIDER=anthropic`
yapıp bir Claude API anahtarı ekleyerek istediğiniz zaman geçiş
yapabilirsiniz — kod tarafında hiçbir değişiklik gerekmez.

## Proje yapısı

app/
├── main.py # FastAPI rotaları
├── config.py # Ortam değişkenleri
├── models.py # İstek modelleri
├── services/
│ ├── downloader.py # yt-dlp ile video indirme
│ ├── transcriber.py # faster-whisper ile transkript
│ ├── analyzer.py # LLM (Groq/Claude) ile en iyi anları seçme
│ ├── clipper.py # ffmpeg ile kesim + dikey format + altyazı
│ └── jobs.py # İş durumu takibi ve pipeline orkestrasyonu
├── templates/index.html # Tek sayfa arayüz
└── static/ # CSS / JS


## Yol haritası fikirleri

- [ ] Yüz/obje takibi ile "akıllı kırpma" (şu an merkez kırpma + bulanık arka plan kullanılıyor)
- [ ] Otomatik başlık, açıklama ve hashtag önerileri
- [ ] Klipleri doğrudan YouTube/TikTok/Instagram'a paylaşma
- [ ] İş kuyruğunu bellek yerine SQLite'ta tutma (sunucu yeniden başlayınca kaybolmasın diye)
- [ ] Birden fazla videoyu kuyruğa alma

## Önemli not — telif hakları

Bu araç yalnızca **kendi içerikleriniz** veya **yeniden paylaşım izniniz
olan** videolar için tasarlanmıştır. Üçüncü taraflara ait videoları izinsiz
indirip yeniden paylaşmak, YouTube'un kullanım şartlarını ve telif hakkı
yasalarını ihlal edebilir. Sorumluluk kullanıcıya aittir.

## Lisans

MIT

# RFID Harava

## Lyhyt Kuvaus

RFID Harava on ohjelma, joka mahdollistaa RFID-tunnisteilla merkityn kirjastoaineiston massaskannauksen.
Se on suunniteltu käytettäväksi Koha-kirjastojärjestelmää käyttävissä kirjastoissa ja tukee kokoelmanhoidon tehtäviä.

![Screenshot](/docs/screenshot.PNG)

## Ohjelman lataaminen

Ohjelmapaketti löytyy tämän github sivun "Releases" -osiosta. Ohjelmapaketti pitää sisällään ohjelman ja ohjeet ohjelman käyttöönottoon, eri RFID-skannereiden konfigurointiin ja ohjelman käyttöön.

## Taustaa

Ohjelma kehitettiin alun perin Turun kaupunginkirjastossa opinnäytetyöprojektina toimivaksi prototyypiksi helpottamaan arkisia kokoelmanhoitoon liittyviä tehtäviä.

Ohjelmaa jatkokehitettiin myöhemmin Koha-Suomen projektissa toimimaan myös muissa kirjastokimpoissa ja lisäämällä siihen uusia ominaisuuksia. 

## Teknistä tietoa 

RFID Harava toimii FEIG ID ISC.PRH200 ja FEIG ID.PRH200-BW -skannereiden kanssa.

Ohjelma kommunikoi RFID-skannerin kanssa WiFi-verkon välityksellä portin 10001 kautta käyttäen TCP-protokollaa.

Ohjelma hakee nidetiedot Koha-kirjastojärjestelmästä REST-rajapinnan kautta käyttämällä kirjastojärjestelmässä tehtyjä API-tunnuksia.

Ohjelma tukee ISO 28560 ja Finnish Item -tietomallien mukaisesti kirjoitettuja RFID-tunnisteita joita käytetään kirjastoaineistossa.

## Ohjelmankääntäminen

Projektissa on mukana compiler.bat kääntöskripti, jolla saadaan käännettyä koodi suoritettavaksi tiedostoksi. Kääntöskripti vaatii toimiakseen pythonin ja projektissa käytetyt ulkoiset kirjastot. 

Kääntöskripti luo "Release" -kansion joka pitää sisällään ohjelman oikealla tiedostorakenteella ja "Ohjeet"-kansion. Kääntöskripti kopioi ohjelmaan liittyvät ohjeet "Ohjeet"-kansiosta. Jotta ohjelma saadaan toimimaan, täytyy ohjelman "Release\RfidHarava\Configs\config.ini" tiedostoon tehdä tarvittavat muutokset, tähän riittää tekstieditori esim. notepad.

Projektissa käytetty Python versio on 3.12

Projektissa käytetyt ulkoiset kirjastot:

| Kirjasto | Versio |
|-----------|--------|
| [PySide6](https://pypi.org/project/PySide6/) | 6.8.0.2 |
| [requests](https://pypi.org/project/requests/) | 2.31.0 |
| [pyinstaller](https://pypi.org/project/pyinstaller/) | 6.15.0 |



## Kehittäjän työkalut

`tools/`-hakemisto sisältää kehittäjän tarkistuksia, jotka eivät tarvitse
RFID-skanneria, Koha-yhteyttä eivätkä verkkoa. Ne toimivat millä tahansa
työpöytäkoneella, jossa on Python-tulkki, joten muutos voidaan tarkistaa ennen
kuin se päätyy skannerille.

| Tiedosto | Tarkoitus |
|----------|-----------|
| `tools/ttldedup_check.py` | Tarkistuksen aloituspiste. Suorittaa FetchTTL-dedup-tarkistuksen ja tulostaa tuloksen. |
| `tools/sim_run.py` | Tarkistuksen käynnistämä apuskripti. Älä suorita sitä suoraan. |

### Vaatimukset

Skriptit ajavat oikeaa käyttöliittymäkoodia, joten ne tarvitsevat `PySide6`:n,
jota tavallinen testisarja ei tarvitse. Ne ajetaan näytöttömänä (offscreen),
joten näyttöä ei tarvita:

```bash
python3 -m venv .venv
.venv/bin/pip install "PySide6==6.8.0.2" requests
```

### Tarkistuksen suorittaminen

```bash
python tools/ttldedup_check.py
```

Se ajaa ohjelman kahdesti ja tulostaa yhteenvedon:

```
                         scans   Koha requests   flashes
--------------------------------------------------------
fetchttl = 0 (before)       59              58         0
fetchttl = 60 (after)       59               1      4177

58 requests -> 1 request, while still flashing 4177 times.

PASS: dedup works and locate-by-flashing is preserved.
```

Argumentit ovat `[seconds] [python] [tags]`, kaikki valinnaisia:

| Argumentti | Oletus | Merkitys |
|----------|---------|---------|
| `seconds` | `20` | Kuinka kauan kumpikin kahdesta ajosta kestää. |
| `python` | nykyinen tulkki | Ohjelman ajamiseen käytettävä tulkki; osoita se venviin, jossa PySide6 on asennettuna. |
| `tags` | `1` | Kohteet, jotka simuloitu lukija ilmoittaa 250 ms välein. Käytä arvoa `16`, jos haluat mallintaa vilkkaampaa hyllyä. |

Esimerkki, 30 sekunnin ajo 16 kohteen hyllyllä:

```bash
python tools/ttldedup_check.py 30 .venv/bin/python 16
```

### Tuloksen tulkinta

**scans**-sarake laskee simuloidut luvut, **Koha requests** fake-rajapintaan
päätyneet raporttipyynnöt ja **flashes** paikannusominaisuuden kutsut.
Tarkistus menee läpi, kun TTL-suodatin kokoaa duplikaattipyynnöt yhdeksi ja
`flashes` pysyy selvästi nollan yläpuolella – viimeksi mainittu todistaa, ettei
vilkuttamalla tapahtuva paikannus kadonnut. Epäonnistunut ehto keskeyttää ajon
ja kertoo, mikä ehto rikkoutui.

### Miten se toimii

Loopback-osoitteeseen käynnistetään kertakäyttöinen fake-Koha-rajapinta.
`Configs/ConfigBase.ini` kopioidaan väliaikaishakemistoon ja siinä olevat
rajapintaosoitteet, tunnukset sekä `fetchttl` kirjoitetaan osoittamaan
fake-rajapintaan. Tämän jälkeen käynnistetään oikea `main.py` väliaikaisella
asetustiedostolla, ja skannaukset simuloidaan lisäämällä viivakoodeja
`main.barcodes`-listaan – täsmälleen sinne, minne lukijan silmukka ne
dekoodauksen jälkeen jättää. `flash_barcode`-kutsut lasketaan ja kaksi ajoa
(`fetchttl = 0` ja `fetchttl = 60`) vertaillaan keskenään.

Koska lukija- ja dekoodausvaiheet ohitetaan, tarkistus ei kata niitä. Se
ajetaan myös ilman näyttöä, joten se laskee `flash_barcode`-kutsut sen sijaan,
että näyttäisi rivin vilkkuvan.

### Ympäristömuuttujat

| Muuttuja | Käyttää | Merkitys |
|----------|---------|---------|
| `HARAVA_REPO` | molemmat | Repon juurihakemisto, jos automaattinen tunnistus epäonnistuu. |
| `HARAVA_WORK` | `sim_run.py` | Väliaikaishakemisto tilastotiedostolle. Tarkistus asettaa sen. |
| `SCAN_INTERVAL` | `sim_run.py` | Sekunnit simuloitujen lukujen välillä. Oletus `0.25`. |
| `SCAN_TAGS` | `sim_run.py` | Viivakoodien määrä yhtä simuloitua lukua kohden. Oletus `1`. |
| `QT_QPA_PLATFORM` | molemmat | Oletus `offscreen`; aseta toinen Qt-alusta, jos haluat seurata käyttöliittymää. |

Kaikki kirjoitetaan hakemistoon `$TMPDIR/harava-ttldedup`, joten työhakemistoon
ei kosketa. Hakemiston voi huoletta poistaa.

### Vianetsintä

- `Could not locate the repo root` – suorita komento repon sisältä tai aseta
  `HARAVA_REPO=/path/to/rfid-harava`.
- `ModuleNotFoundError: No module named 'PySide6'` – asenna se yllä kuvatulla
  tavalla ja anna kyseinen tulkki toisena argumenttina.
- CI ei kerää näitä tarkistuksia: `pyproject.toml` rajaa pytestin hakemistoon
  `tests/`, ja siellä oleva sarja käyttää vain Pythonin standardikirjastoa.

## Lisensonti

Lisensoitu EUPL:n nojalla.

Voit vapaasti käyttää, muokata ja jakaa ohjelmistoa lisenssin ehtojen mukaisesti.

## Kehittäjä

- **Robert Vallimägi** – Pääkehittäjä / Alkuperäinen tekijä  

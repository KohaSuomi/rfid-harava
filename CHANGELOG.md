# Changelog

Kaikki merkittävät muutokset RFID Harava -ohjelmaan. Otsikon versionumero vastaa
GitHub-julkaisun tagia (`v1.1`) ja `Configs/ConfigBase.ini`-tiedoston versiota.
Julkaisun tiedot luetaan tästä tiedostosta, joten lisää uusi osio ennen kuin
teet version mukaisen tagin.

## [1.1] - 2026-10-14

RFID Harava 1.1 -ohjelmapaketti sisältää ohjelman sekä ohjeet käyttöönottoon, RFID-skannereiden konfigurointiin ja ohjelman käyttöön. Paketissa ohjelma on omassa kansiossaan ja ohjeet omassaan.

### Mitä uutta

- **Koha-rajapinnan kuormitus pieneni merkittävästi.** RFID-lukija ilmoittaa jokaisen kentässään olevan tunnisteen uudelleen useita kertoja sekunnissa. Aiemmin jokainen ilmoitus aiheutti oman rajapintakutsun, joten kentässä paikallaan oleva nide sai aikaan jatkuvan rajapintapyyntöjen virran. Nyt sama viivakoodi haetaan uudelleen vasta, kun `fetchttl`-aika on kulunut (oletus 60 sekuntia). Uudelleen luettu nide vilkkuu edelleen paikannuksen merkiksi, vaikka hakua ei toisteta.

- **Ohjelma ei enää kaadu lukukelvottomaan RFID-tunnisteeseen.** Jos tunnisteen tiedot ovat puutteelliset tai niitä ei voi tulkita, kyseinen tunniste ohitetaan ja tapahtuma kirjataan lokiin sen sijaan, että ohjelma keskeytyisi kesken skannauksen.

- **Rivin vilkkuminen (paikannus) korjattu.** Vilkkuva rivi ei enää kokoa päällekkäisiä ajastimia eikä jää vilkkumaan loputtomiin. Kun rivejä poistetaan tai taulukko tyhjennetään, vilkkuminen ei enää siirry vahingossa väärälle riville.

- **Oma sovelluskuvake.** Ohjelmalla on nyt kuvake (harava.ico) tehtäväpalkissa ja pikakuvakkeissa.

### Asetukset

Versiossa 1.1 on uusi asetus `Configs/config.ini`-tiedoston `[Other]`-osiossa:

- `fetchttl` – kuinka monta sekuntia viivakoodia ei haeta uudelleen sen jälkeen, kun se on haettu. Oletus `60`. Arvo `0` poistaa eston käytöstä.

Vanha `config.ini` toimii sellaisenaan: jos `fetchttl` puuttuu, käytetään oletusarvoa 60 sekuntia.

**Full Changelog**: https://github.com/KohaSuomi/rfid-harava/compare/v1.0...v1.1

## [1.0] - 2025-11-11

RFID Harava 1.0 ohjelmapaketti joka pitää sisällään ohjelman sekä ohjeet käyttöönottoon, RFID-skannereiden konfigurointiin ja ohjelman käyttöön. Paketissa ohjelma on omassa kansiossaan ja ohjeet omassaan.

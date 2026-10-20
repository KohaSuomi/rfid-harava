# Changelog

Kaikki merkittävät muutokset RFID Harava -ohjelmaan. Otsikon versionumero vastaa
GitHub-julkaisun tagia (`v1.1`) ja `Configs/ConfigBase.ini`-tiedoston versiota.
Julkaisun tiedot luetaan tästä tiedostosta, joten lisää uusi osio ennen kuin
teet version mukaisen tagin.

## [1.1.2] - 2026-10-20

RFID Harava 1.1.2 on korjausjulkaisu, joka sisältää ohjelman sekä ohjeet käyttöönottoon, RFID-skannereiden konfigurointiin ja ohjelman käyttöön.

### Korjattu

- **Hakuehtojen muuttaminen ei enää jätä vanhoja tuloksia välimuistiin.** Aiemmin `fetchttl`-välimuisti esti saman viivakoodin hakemisen uudelleen vielä sen jälkeen, kun hakuehtoja oli muutettu, joten uudelleen luettu nide arvioitiin vanhoilla ehdoilla kunnes `fetchttl` ehti kulua. Nyt `Configs/UserSettings.ini`-tiedoston muutosaikaa seurataan ja välimuisti tyhjennetään heti, kun hakuehdot muuttuvat.

### Mitä uutta

- **Tulosten lista voidaan tyhjentää omalla painikkeella.** Hakuehtojen muuttaminen ei tyhjennä listaa, joten eri hakuehdoilla löytyneet tulokset voi kerätä samaan listaan. Kun lista halutaan tyhjentää, siihen on nyt oma **Tyhjennä lista** -painike, joka tyhjentää myös hakuvälimuistin.

**Full Changelog**: https://github.com/KohaSuomi/rfid-harava/compare/v1.1.1...v1.1.2

## [1.1.1] - 2026-10-19

RFID Harava 1.1.1 on korjausjulkaisu, joka sisältää ohjelman sekä ohjeet käyttöönottoon, RFID-skannereiden konfigurointiin ja ohjelman käyttöön.

### Korjattu

- **Rivin vilkkuminen (paikannus) ei enää jatku koko `fetchttl`-jaksoa.** Versiossa 1.1 vilkkuva rivi saattoi jäädä vilkkumaan lähes koko `fetchttl`-ajan, vaikka tunniste oli jo poistunut lukukentästä. Lisäksi uuden, välimuistissa olevan niteen lukeminen saattoi katkaista muiden rivien vilkkumisen kesken. Syynä oli, että viivakoodijonoa ei tyhjennetty joka kierroksella, jolloin lukijan toistuvasti ilmoittamat viivakoodit kertyivät jonoon ja sama rivi vilkkui uudelleen joka kierroksella. Nyt jono tyhjennetään joka kierroksella: rivi vilkkuu vain, kun tunniste on lukukentässä, ja himmenee pian sen jälkeen kun tunniste poistuu.

**Full Changelog**: https://github.com/KohaSuomi/rfid-harava/compare/v1.1...v1.1.1

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

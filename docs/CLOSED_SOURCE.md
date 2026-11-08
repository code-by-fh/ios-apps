# Eine App mit geschlossenem Quellcode aufnehmen

Der zentrale Katalog benötigt eine öffentliche Source-JSON und öffentlich herunterladbare IPAs. Dein Flutter-Projekt, seine Git-Historie und seine Build-Skripte können in einem privaten Repository bleiben. Für Downloads wird ein getrenntes öffentliches Release-Repository verwendet.

```text
Privates App-Repository
        ↓ iOS-Build auf macOS in GitHub Actions
Private Actions-Artefakte: unsignierte IPA
        ↓ bewusste Veröffentlichung der Download-Dateien
Öffentliches Release-Repository: IPA + JSON + Icon + Prüfsumme
        ↓ öffentliche Source-URL in apps.json registrieren
Zentraler Katalog code-by-fh/ios-apps
        ↓
SideStore / AltStore Classic
```

## 1. App privat entwickeln und bauen

Verwende für jede App eine eigene Bundle-ID, zum Beispiel `com.yourcompany.myprivateapp`. Erstelle in deinem privaten App-Repository einen unsignierten **Release-Build für ein echtes iOS-Gerät**. Lade die erzeugte IPA aus einem erfolgreichen Actions-Lauf herunter und prüfe sie vor der Veröffentlichung. Ein erfolgreiches Paketieren ersetzt keinen Installationstest auf einem iPhone.

Die IPA enthält die ausgelieferte App und ihre eingebetteten Ressourcen. Geheimnisse gehören nicht in den App-Code oder die Assets. Geschlossener Quellcode macht eine öffentlich ausgelieferte Binärdatei nicht vertraulich.

## 2. Öffentliches Download-Repository anlegen

Mit deiner vorhandenen GitHub-CLI-Anmeldung:

```powershell
gh auth status
gh repo create owner/my-private-app-releases --public --add-readme
```

Ersetze `owner` durch deinen GitHub-Namen beziehungsweise deine Organisation und wähle einen freien Repositorynamen. Dieses neue Repository wird ausdrücklich für öffentliche Binärdownloads angelegt. Das private Entwicklungsrepository behält seine Sichtbarkeit.

Ergänze im Download-Repository einen Hinweis auf die tatsächliche App-Lizenz, beispielsweise eine proprietäre Lizenz mit den von dir erlaubten Nutzungsrechten. Ein öffentlicher Download und die Aufnahme in diesen Katalog erteilen nicht automatisch eine Open-Source-Lizenz.

## 3. IPA und App-Quelle veröffentlichen

Wenn dein privates App-Projekt den vorbereiteten Publisher `scripts/publish_source.py` verwendet, führe dort aus:

```powershell
python scripts/publish_source.py --repository owner/my-private-app-releases --ipa downloads/my-private-app.ipa
```

Dieser explizite Zielparameter ist entscheidend: Er bezeichnet das öffentliche Download-Repository. Der Publisher lädt die IPA, die daraus erzeugte Source-JSON, ein Icon und die Prüfsumme hoch. Er kopiert keinen Projektquellcode und macht kein bestehendes privates Repository öffentlich. Die lokale GitHub-CLI-Anmeldung genügt; dafür werden keine zusätzlichen CI-Secrets eingerichtet.

Der vorbereitete Publisher unterstützt die minimale ARM64-App ohne zusätzliche App-Erweiterungen oder eingebettete Provisioning-Profile. Er liest den App-Namen aus `CFBundleDisplayName` der IPA; die Vorlage setzt diesen Namen über die App-Konfiguration beim Erzeugen der Plattformdateien. Beschreibung und Plus-Icon sind zunächst Vorlagenwerte und können für deine App angepasst werden. Bundle-ID, Version, Buildnummer, Mindest-iOS-Version, Paketgröße und Berechtigungen stammen ebenfalls aus der tatsächlichen IPA. Zusätzliche native Fähigkeiten müssen vor einer Erweiterung geprüft werden.

Die eigene App-Quelle muss anschließend ohne Anmeldung erreichbar sein:

```text
https://github.com/owner/my-private-app-releases/releases/latest/download/altstore-source.json
```

Prüfe auch den in dieser JSON enthaltenen IPA-Download und das Icon ohne GitHub-Anmeldung. Der Publisher prüft die öffentlichen URLs nach dem Upload; nur ein erfolgreicher Abschluss bestätigt diese Prüfung.

## 4. Im zentralen Katalog registrieren

Im lokalen Checkout von `code-by-fh/ios-apps`:

```powershell
python scripts/register_app.py --repository owner/my-private-app-releases --license closed-source
git add apps.json
git commit -m "Register closed-source app"
git push
```

Die Registrierung ergänzt den Link auf die öffentliche App-Quelle und die Lizenzkennzeichnung. Der Katalog-Workflow lädt Metadaten von diesem öffentlichen Endpunkt. Er benötigt keinen Zugriff auf das private App-Projekt.

## 5. Neue App-Versionen bereitstellen

Neue IPA im privaten App-Projekt bauen und herunterladen, Version beziehungsweise Buildnummer erhöhen und mit demselben öffentlichen Zielrepository veröffentlichen. Die Source-URL bleibt gleich. Der Katalog übernimmt die neue Version bei der nächsten erfolgreichen Aktualisierung; ein erneuter Registrierungseintrag ist nicht nötig.

Ein Push zum privaten App-Repository allein veröffentlicht die IPA noch nicht im öffentlichen Download-Repository. Die vorbereitete CI stellt dort Build-Artefakte bereit und überspringt die automatische Release-Veröffentlichung im privaten Repository. Der oben beschriebene lokale Veröffentlichungsbefehl ist ein eigener Schritt. Eine spätere automatische Veröffentlichung aus privater CI benötigt eine ausdrücklich eingerichtete Freigabe und passende Berechtigungen für das zweite Repository; das repositoryeigene `GITHUB_TOKEN` erhält diesen Zugriff nicht automatisch.

Die [Katalogwerkzeuge stehen unter MIT](../LICENSE); die Lizenz der App bestimmst du separat. Prüfe das Ergebnis außerdem im Sideloader und auf einem echten Gerät.

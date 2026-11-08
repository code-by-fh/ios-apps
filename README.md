# iOS Apps

Zentraler App-Katalog für SideStore und AltStore Classic. Der Katalog führt öffentlich erreichbare App-Quellen zusammen. Er unterstützt sowohl Open-Source-Apps als auch Apps mit geschlossenem Quellcode; die Veröffentlichung einer IPA verlangt keinen öffentlichen Quellcode.

Die vorgesehene Source-URL nach erfolgreicher Veröffentlichung dieses Repositories lautet:

```text
https://raw.githubusercontent.com/code-by-fh/ios-apps/main/altstore-source.json
```

Diese Adresse in SideStore unter **Sources / Quellen → + / Add Source** eintragen. Der Katalog ist vorbereitet, aber seine Veröffentlichung und die Erreichbarkeit dieser URL müssen nach dem Push geprüft werden. Eine lokal bereits erzeugte JSON-Datei beweist noch keine öffentliche Verfügbarkeit. Installation und Signierung übernimmt weiterhin dein Sideloader mit deinem eigenen Apple Account.

## Aufbau

`apps.json` enthält die registrierten Quellen. Jede aktivierte Quelle liefert ihre eigene Source-JSON mit App-Metadaten, Berechtigungen und versionsgebundenen IPA-Downloads. Der Katalog übernimmt diese Angaben und erzeugt daraus `altstore-source.json`. Er benötigt weder die privaten App-Repositories noch Apple-Anmeldedaten oder zusätzliche Zugriffstokens.

Die erste registrierte Quelle ist SideStart:

```json
{
  "sources": [
    {
      "url": "https://github.com/code-by-fh/sidestart/releases/latest/download/altstore-source.json",
      "license": "open-source",
      "enabled": true
    }
  ]
}
```

Jede App muss eine eindeutige Bundle-ID besitzen. Die App-Quelle und ihre Downloadlinks müssen ohne Anmeldung erreichbar sein. GitHub Actions-Artefakte aus privaten Repositories eignen sich deshalb nicht als öffentliche Downloadlinks.

## Eine App ergänzen

Wenn ein öffentliches Release-Repository bereits `altstore-source.json`, das Icon und die IPA bereitstellt:

```powershell
python scripts/register_app.py --repository owner/app-releases --license closed-source
git add apps.json
git commit -m "Register app source"
git push
```

Ersetze `owner/app-releases` durch das tatsächliche Release-Repository. Für eine Open-Source-App entsprechend `--license open-source` verwenden. Der Registrierungsbefehl bildet die Source-URL aus dem Repositorynamen; die Quelle muss als Datei des neuesten GitHub Releases verfügbar sein.

Die Kennzeichnung `open-source` beziehungsweise `closed-source` beschreibt das Lizenzmodell. Sie verändert keine iOS-Berechtigungen und veröffentlicht keinen App-Quellcode. Für geschlossene Apps mit privatem Entwicklungsrepository beschreibt [docs/CLOSED_SOURCE.md](docs/CLOSED_SOURCE.md) den vollständigen Weg.

## Aktualisierung

GitHub Actions aktualisiert den Katalog nach Änderungen an der Registrierung oder den Skripten, manuell über `workflow_dispatch` und geplant alle 15 Minuten. Geplante GitHub-Läufe können sich verzögern. Der Workflow liest ausschließlich öffentliche Quellen und verwendet das repositoryeigene `GITHUB_TOKEN`, um die erzeugte JSON auf `main` zu aktualisieren. Zusätzliche Secrets sind dafür nicht erforderlich.

Pull Requests führen Prüfungen aus und veröffentlichen keinen Katalog. Bei einer ungültigen beziehungsweise nicht erreichbaren aktivierten Quelle schlägt die Aktualisierung fehl; die letzte erfolgreiche Katalogdatei bleibt erhalten. Prüfe bei ausbleibenden Updates den Actions-Lauf sowie die betroffene App-Quelle.

## Lizenzen und Installation

Die MIT-Lizenz dieses Repositories betrifft dessen Katalogwerkzeuge und eigenen Code. Sie erteilt **keine Lizenz an den aufgeführten Apps oder IPA-Dateien**. Für jede App gelten die Bedingungen des jeweiligen Rechteinhabers. Eine öffentlich herunterladbare Binärdatei ist nicht vertraulich; die App kann trotzdem proprietär lizenziert bleiben.

Für die Installation gelten weiterhin die [SideStore-Voraussetzungen](https://docs.sidestore.io/docs/installation/prerequisites) und [Beschränkungen kostenloser Apple Accounts](https://docs.sidestore.io/docs/faq). Das Quellenformat orientiert sich an der [AltStore-Dokumentation](https://faq.altstore.io/developers/make-a-source).

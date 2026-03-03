# EnvCrypt CLI

![Python application CI](https://github.com/your-org/envcrypt-cli/actions/workflows/python-app.yml/badge.svg)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Ein leistungsstarkes und benutzerfreundliches Kommandozeilen-Dienstprogramm (CLI) zum sicheren Verschlüsseln und Entschlüsseln sensibler Umgebungsvariablen und ganzer `.env`-Dateien. EnvCrypt CLI wurde mit Blick auf Sicherheit und Benutzerfreundlichkeit entwickelt und hilft Entwicklern und Betriebsteams, Geheimnisse in verschiedenen Umgebungen effektiv zu verwalten.

## Funktionen

*   **Symmetrische Verschlüsselung**: Verwendet die symmetrische Fernet-Verschlüsselung aus der `cryptography`-Bibliothek, die einen starken und manipulationssicheren Datenschutz gewährleistet.
*   **Schlüsselverwaltung**: Unterstützt das Laden von Verschlüsselungsschlüsseln aus Umgebungsvariablen (`ENVCYPT_KEY`), angegebenen Schlüsseldateien oder einer Standarddatei `.envcrypt_key`. Enthält einen Befehl zum sicheren Generieren neuer Schlüssel.
*   **Verschlüsselung/Entschlüsselung einzelner Werte**: Einfaches Ver- oder Entschlüsseln einzelner Zeichenketten direkt über die Kommandozeile.
*   **`.env`-Dateiverarbeitung**: Verschlüsselt oder entschlüsselt alle Variablenwerte in einer Standard-`.env`-Datei, wobei Kommentare und nicht zugewiesene Zeilen erhalten bleiben.
*   **Zweisprachige Dokumentation**: Umfassende Dokumentation ist sowohl in Englisch als auch in Deutsch verfügbar.
*   **Enterprise-Ready**: Entwickelt mit Best Practices, einschließlich Typ-Hinweisen, Docstrings, Unit-Tests und CI/CD-Integration.

## Installation

### Voraussetzungen

*   Python 3.9+
*   `pip` (Python-Paketmanager)

### Schritte

1.  **Repository klonen**:
    ```bash
    git clone https://github.com/your-org/envcrypt-cli.git
    cd envcrypt-cli
    ```
2.  **Virtuelle Umgebung erstellen** (empfohlen):
    ```bash
    python -m venv venv
    source venv/bin/activate # Unter Windows: `venv\Scripts\activate`
    ```
3.  **Abhängigkeiten installieren**:
    ```bash
    pip install -r requirements.txt
    ```
4.  **CLI zugänglich machen** (optional, aber für die globale Nutzung empfohlen):
    Sie können Befehle entweder mit `python main.py <command>` ausführen oder einen Symlink/Alias erstellen.
    Für die Entwicklung können Sie auch im bearbeitbaren Modus installieren:
    ```bash
    pip install -e .
    ```
    Dadurch können Sie `envcrypt <command>` direkt ausführen, wenn Ihr `PATH` das `bin`-Verzeichnis der virtuellen Umgebung enthält.

## Verwendung

Zuerst benötigen Sie einen Verschlüsselungsschlüssel. **Halten Sie diesen Schlüssel absolut sicher!**

### 1. Einen Verschlüsselungsschlüssel generieren

Es wird dringend empfohlen, für jedes Projekt oder jede Umgebung einen neuen Schlüssel zu generieren.
```bash
envcrypt generate-key --output .envcrypt_key
```
Dieser Befehl erstellt eine Datei namens `.envcrypt_key` in Ihrem aktuellen Verzeichnis.
Alternativ können Sie den ausgegebenen Schlüsselstring kopieren und als Umgebungsvariable festlegen:
`export ENVCYPT_KEY="Ihr_generierter_base64_schlüssel"`

### 2. Einen einzelnen String verschlüsseln

```bash
envcrypt encrypt "mein_geheimer_api_schlüssel_123"
# Ausgabe: gAAAAABi... (ein Base64-kodierter verschlüsselter String)
```

### 3. Einen einzelnen String entschlüsseln

```bash
envcrypt decrypt "gAAAAABi..."
# Ausgabe: mein_geheimer_api_schlüssel_123
```

### 4. Eine `.env`-Datei verschlüsseln

Angenommen, Sie haben eine `input.env`-Datei:
```env
# Datenbank-Zugangsdaten
DB_HOST=localhost
DB_PORT=5432
DB_USER=admin
DB_PASS=supersicherespasswort123
API_KEY=mein_api_schlüsselwert
```

Zum Verschlüsseln:
```bash
envcrypt encrypt-file input.env output.env.encrypted
```
Die Datei `output.env.encrypted` enthält dann:
```env
# Datenbank-Zugangsdaten
DB_HOST=gAAAAABi...
DB_PORT=gAAAAABi...
DB_USER=gAAAAABi...
DB_PASS=gAAAAABi...
API_KEY=gAAAAABi...
```
Kommentare und Zeilen ohne `=` bleiben unverändert erhalten.

### 5. Eine verschlüsselte `.env`-Datei entschlüsseln

```bash
envcrypt decrypt-file output.env.encrypted decrypted.env
```
Die Datei `decrypted.env` enthält die ursprünglichen Klartextwerte.

### Schlüsselverwaltungsoptionen

EnvCrypt CLI sucht den Verschlüsselungsschlüssel in der folgenden Reihenfolge:

1.  **`--key-file <pfad>` Option**: Explizit angegebener Dateipfad.
2.  **`ENVCYPT_KEY` Umgebungsvariable**: Wenn die Umgebungsvariable `ENVCYPT_KEY` gesetzt ist.
3.  **`.envcrypt_key` Datei**: Eine Datei namens `.envcrypt_key` im aktuellen Arbeitsverzeichnis.

Es wird dringend empfohlen, in Produktionsumgebungen eine Umgebungsvariable (z.B. `ENVCYPT_KEY`) zu verwenden oder die Schlüsseldatei sicher mit entsprechenden Berechtigungen zu verwalten. **Geben Sie Ihren Verschlüsselungsschlüssel niemals in die Versionskontrolle!**

## Mitwirken

Wir freuen uns über Beiträge! Bitte lesen Sie unsere [CONTRIBUTING.md](CONTRIBUTING.md) für Richtlinien zum Melden von Problemen, Vorschlagen von Funktionen und Einreichen von Code.

## Lizenz

Dieses Projekt ist unter der MIT-Lizenz lizenziert – weitere Details finden Sie in der Datei [LICENSE](LICENSE).

---

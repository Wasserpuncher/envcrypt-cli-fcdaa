# EnvCrypt CLI Architektur im Detail

Dieses Dokument bietet einen detaillierten Überblick über das architektonische Design und die Kernkomponenten des EnvCrypt CLI-Dienstprogramms.

## 1. Einführung

EnvCrypt CLI wurde entwickelt, um eine sichere und bequeme Möglichkeit zur Verwaltung sensibler Umgebungsvariablen zu bieten, insbesondere solcher, die in `.env`-Dateien gespeichert sind. Es nutzt etablierte kryptographische Primitive, um die Vertraulichkeit und Integrität der Daten zu gewährleisten. Die Hauptziele der Architektur sind:

*   **Sicherheit**: Verwendung starker, branchenüblicher Verschlüsselung.
*   **Benutzerfreundlichkeit**: Bereitstellung einer einfachen, intuitiven Kommandozeilenschnittstelle.
*   **Flexibilität**: Unterstützung verschiedener Schlüsselverwaltungsstrategien.
*   **Wartbarkeit**: Einsatz von klarem, modularem und testbarem Code.

## 2. Kernkomponenten

Die Architektur konzentriert sich auf zwei Hauptlogikkomponenten: die `EnvCryptor`-Klasse und den Schlüsselverwaltungsmechanismus, die alle vom `click`-CLI-Framework orchestriert werden.

### 2.1. `EnvCryptor`-Klasse

Die `EnvCryptor`-Klasse ist das Herzstück der Verschlüsselungs- und Entschlüsselungslogik.

*   **Zweck**: Kapselt die symmetrischen Ver- und Entschlüsselungsoperationen.
*   **Technologie**: Sie verwendet `cryptography.fernet.Fernet` aus der Python-Bibliothek `cryptography`. Fernet ist ein meinungsstarkes symmetrisches Verschlüsselungsschema, das starke Garantien bietet:
    *   **Vertraulichkeit**: Daten werden mit AES im CBC-Modus mit einem 128-Bit-Schlüssel verschlüsselt.
    *   **Integrität und Authentizität**: Daten werden mit HMAC-SHA256 signiert, um Manipulationen zu verhindern.
    *   **Schlüsselableitung**: Verwendet PBKDF2 zur Schlüsselableitung.
    *   **Initialisierungsvektor (IV)-Verwaltung**: Handhabt die IV-Generierung und -Verwaltung automatisch.
    *   **Zeitstempel**: Enthält einen Zeitstempel im Token, der optionale Token-Ablaufrichtlinien ermöglicht (derzeit nicht in EnvCrypt CLI implementiert).
*   **Initialisierung**: Eine `EnvCryptor`-Instanz wird mit einem `bytes`-Objekt initialisiert, das den Fernet-Schlüssel darstellt. Dieser Schlüssel muss URL-sicher Base64-kodiert sein.
*   **Methoden**:
    *   `encrypt(plaintext: str) -> str`: Nimmt einen Klartext-String, kodiert ihn in UTF-8, verschlüsselt ihn mit der internen Fernet-Instanz und gibt den Base64-kodierten Chiffretext-String zurück.
    *   `decrypt(ciphertext: str) -> str`: Nimmt einen Base64-kodierten Chiffretext-String, dekodiert ihn, entschlüsselt ihn mit der internen Fernet-Instanz und gibt den UTF-8-dekodierten Klartext-String zurück. Es enthält eine Fehlerbehandlung für `InvalidToken`-Ausnahmen, die auftreten, wenn der Schlüssel falsch ist oder die Daten manipuliert wurden.

### 2.2. Schlüsselverwaltung (`_load_key`-Funktion)

Eine sichere Schlüsselverwaltung ist für jedes Verschlüsselungs-Dienstprogramm von größter Bedeutung. EnvCrypt CLI bietet einen flexiblen Schlüssel-Lademodus, der Sicherheit und Komfort priorisiert.

*   **Lade-Reihenfolge**: Die Funktion `_load_key` versucht, den Fernet-Schlüssel in einer bestimmten hierarchischen Reihenfolge zu laden:
    1.  **Umgebungsvariable (`ENVCYPT_KEY`)**: Dies hat die höchste Priorität. Wenn `ENVCYPT_KEY` gesetzt ist, wird dessen Wert (erwartet als URL-sicherer Base64-kodierter Schlüsselstring) dekodiert und verwendet. Dies ist ideal für CI/CD-Pipelines und Produktionsumgebungen, in denen Geheimnisse als Umgebungsvariablen injiziert werden.
    2.  **Explizite Schlüsseldatei (`--key-file`-Option)**: Wenn der Benutzer einen Pfad über die CLI-Option `--key-file` angibt, versucht das Tool, den Schlüssel direkt aus dieser Datei zu lesen. Dies ermöglicht die Verwendung spezifischer Schlüsseldateien für verschiedene Projekte oder Kontexte.
    3.  **Standard-Schlüsseldatei (`.envcrypt_key`)**: Als Fallback sucht das Tool nach einer Datei namens `.envcrypt_key` im aktuellen Arbeitsverzeichnis. Dies ist praktisch für die lokale Entwicklung, aber weniger sicher für gemeinsame Umgebungen.
*   **Fehlerbehandlung**: Wenn kein Schlüssel erfolgreich aus einer dieser Quellen geladen werden kann, wird eine `click.ClickException` ausgelöst, die den Benutzer über den fehlenden Schlüssel und die verfügbaren Optionen informiert.
*   **Schlüsselgenerierung**: Der Befehl `generate-key` verwendet `Fernet.generate_key()`, um einen neuen, zufälligen und kryptographisch sicheren Fernet-Schlüssel zu erstellen. Dieser Schlüssel wird dann in einer angegebenen Datei (Standard: `.envcrypt_key`) gespeichert und zusätzlich auf der Konsole ausgegeben, damit der Benutzer ihn als Umgebungsvariable festlegen kann.

## 3. CLI-Design (mit `click`)

Die Kommandozeilenschnittstelle wird mit der `click`-Bibliothek erstellt, die die Erstellung eleganter und robuster CLIs vereinfacht.

*   **`@click.group()`**: Die Hauptfunktion `cli` fungiert als Einstiegspunkt und als Gruppe für Unterbefehle.
*   **`@click.option('--key-file', ...)`**: Eine globale Option zur Angabe einer Schlüsseldatei, die auf alle Befehle innerhalb der Gruppe angewendet wird. Der Schlüssel wird einmal zu Beginn der `cli`-Ausführung geladen und in `ctx.obj` gespeichert, damit alle Unterbefehle darauf zugreifen können.
*   **Unterbefehle**:
    *   `generate-key`: Erstellt einen neuen Fernet-Schlüssel. Dieser Befehl benötigt **keinen** vorhandenen Schlüssel zur Ausführung.
    *   `encrypt <plaintext>`: Verschlüsselt einen einzelnen String.
    *   `decrypt <ciphertext>`: Entschlüsselt einen einzelnen String.
    *   `encrypt-file <input_file> <output_file>`: Liest eine `.env`-Datei, verschlüsselt den Wert jeder Variablen und schreibt sie in eine neue Datei.
    *   `decrypt-file <input_file> <output_file>`: Liest eine verschlüsselte `.env`-Datei, entschlüsselt den Wert jeder Variablen und schreibt sie in eine neue Datei.
*   **Dateiverarbeitung (`_process_env_file`)**: Eine gemeinsam genutzte interne Funktion handhabt die Logik zum Lesen von `.env`-Dateien, zum Parsen von Zeilen, zum Anwenden von Ver- oder Entschlüsselung auf Werte und zum Schreiben des geänderten Inhalts. Sie identifiziert und überspringt Kommentare korrekt und behält Zeilen bei, die keine Variablenzuweisungen enthalten. Sie behandelt auch Fälle, in denen die Entschlüsselung für einzelne Zeilen fehlschlagen könnte, wodurch der Prozess mit einer Warnung fortgesetzt werden kann.
*   **Typ-Hinweise und Docstrings**: Alle Funktionen und Methoden sind mit Typ-Hinweisen versehen und enthalten umfassende Docstrings, um die Lesbarkeit, Wartbarkeit des Codes zu verbessern und statische Analyse zu ermöglichen.

## 4. Sicherheitsaspekte

*   **Schlüsselgeheimnis**: Die Sicherheit von EnvCrypt CLI hängt vollständig von der Geheimhaltung des Fernet-Schlüssels ab. Benutzern wird dringend empfohlen:
    *   **Verschlüsselungsschlüssel niemals in die Versionskontrolle zu übernehmen.**
    *   Sichere Methoden (z.B. Umgebungsvariablen, Geheimnisverwaltungsdienste) zu verwenden, um Schlüssel in der Produktion bereitzustellen.
    *   Schlüsseldateien mit entsprechenden Dateisystemberechtigungen zu schützen.
*   **Fernet**: Die Wahl von Fernet stellt sicher, dass gängige kryptographische Fallstricke (wie unsachgemäße IV-Wiederverwendung oder schwache MACs) vermieden werden, da es sich um ein "Authenticated Encryption with Associated Data" (AEAD)-Schema handelt.
*   **Fehlerbehandlung**: Die explizite `InvalidToken`-Behandlung hilft, Manipulationen oder falsche Schlüssel zu erkennen und stille Fehler zu verhindern.

## 5. Zukünftige Erweiterungen

*   **Konfigurationsdatei**: Implementierung der Unterstützung für eine `config.json` oder `pyproject.toml`, um Standard-Schlüsselpfade, Ausgabeformate oder andere Einstellungen zu definieren. (Dies ist das vorgeschlagene initiale Issue).
*   **Schlüsselrotation**: Hinzufügen von Befehlen oder Funktionen zur Erleichterung der Schlüsselrotation.
*   **Vault-Integration**: Integration mit Geheimnisverwaltungsdiensten wie HashiCorp Vault, AWS Secrets Manager oder Azure Key Vault für eine robustere Schlüsselverwaltung.
*   **Nicht-interaktiver Modus**: Option zum Unterdrücken von Eingabeaufforderungen und Warnungen für die Skripterstellung.
*   **Rekursive Dateiverarbeitung**: Möglichkeit, mehrere `.env`-Dateien innerhalb einer Verzeichnisstruktur zu verarbeiten.
*   **Token-Ablauf**: Nutzung des eingebauten Zeitstempels von Fernet zur Implementierung optionaler Token-Ablaufzeiten.
*   **Docker-Unterstützung**: Bereitstellung einer Dockerfile für eine einfache Containerisierung.

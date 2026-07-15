import os
import json
import click
import base64
from typing import Any, Dict, Optional, Tuple
from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken

# Standardname der Konfigurationsdatei, die im aktuellen Verzeichnis gesucht wird.
DEFAULT_CONFIG_FILENAME = ".envcrypt.json"
# Umgebungsvariable, die auf eine alternative Konfigurationsdatei zeigen kann.
CONFIG_ENV_VAR = "ENVCRYPT_CONFIG"


def _discover_config_path(cli_config_path: Optional[str]) -> Tuple[str, bool]:
    """Ermittelt den Pfad zur Konfigurationsdatei und ob er explizit gewünscht ist.

    Vorrang der Fundstelle: ``--config``-Flag > Umgebungsvariable ``ENVCRYPT_CONFIG``
    > Standarddatei ``.envcrypt.json`` im aktuellen Verzeichnis.
    """
    if cli_config_path:
        return cli_config_path, True
    env_config = os.getenv(CONFIG_ENV_VAR)
    if env_config:
        return env_config, True
    return DEFAULT_CONFIG_FILENAME, False


def load_config(cli_config_path: Optional[str] = None) -> Dict[str, Any]:
    """Lädt die JSON-Konfigurationsdatei (nur Standardbibliothek).

    An explicitly requested file (via ``--config`` or ``ENVCRYPT_CONFIG``) must exist;
    the implicit default file may be absent (an empty dict is returned then).

    Raises:
        click.ClickException: If the file is missing (though explicitly requested),
                              contains invalid JSON or is not a JSON object.
    """
    path, explicit = _discover_config_path(cli_config_path)
    if not os.path.exists(path):
        if explicit:
            raise click.ClickException(f"Configuration file '{path}' not found.")
        return {}
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        raise click.ClickException(f"Could not read configuration file '{path}': {e}")
    if not isinstance(data, dict):
        raise click.ClickException(f"Configuration file '{path}' must contain a JSON object.")
    # Security: only paths/settings belong in the config, never the raw key material.
    if 'key' in data or 'secret_key' in data:
        raise click.ClickException(
            "Configuration file must not contain a raw key. Use 'key_file' to "
            "reference a key file or the ENVCYPT_KEY environment variable instead."
        )
    return data


def resolve_setting(cli_value: Optional[str], config: Dict[str, Any], key: str,
                    env_var: Optional[str], default: Optional[str]) -> Optional[str]:
    """Löst eine einzelne Einstellung nach der Vorrangregel auf.

    Precedence: CLI flag > config file > environment variable > built-in default.
    """
    if cli_value is not None:
        return cli_value
    if config.get(key) is not None:
        return config[key]
    if env_var:
        env_value = os.getenv(env_var)
        if env_value is not None:
            return env_value
    return default

class EnvCryptor:
    """
    Eine Klasse zum Verschlüsseln und Entschlüsseln von Daten mit Fernet-Symmetrie.
    This class handles encryption and decryption of data using Fernet symmetric encryption.
    """

    def __init__(self, key: bytes):
        """
        Initialisiert den EnvCryptor mit einem Fernet-Schlüssel.
        Initializes the EnvCryptor with a Fernet key.

        Args:
            key: Der symmetrische Fernet-Schlüssel als Bytes.
                 The symmetric Fernet key as bytes.
        """
        self.fernet = Fernet(key) # Erstellt eine Fernet-Instanz mit dem bereitgestellten Schlüssel.

    def encrypt(self, plaintext: str) -> str:
        """
        Verschlüsselt einen Klartext-String.
        Encrypts a plaintext string.

        Args:
            plaintext: Der zu verschlüsselnde Klartext-String.
                       The plaintext string to encrypt.

        Returns:
            Der verschlüsselte String (Base64-kodiert).
            The encrypted string (Base64 encoded).
        """
        encoded_text = plaintext.encode('utf-8') # Kodiert den Klartext in Bytes.
        encrypted_text = self.fernet.encrypt(encoded_text) # Verschlüsselt die Bytes.
        return encrypted_text.decode('utf-8') # Dekodiert die verschlüsselten Bytes zurück in einen String.

    def decrypt(self, ciphertext: str) -> str:
        """
        Entschlüsselt einen verschlüsselten String.
        Decrypts an encrypted string.

        Args:
            ciphertext: Der zu entschlüsselnde verschlüsselte String.
                        The encrypted string to decrypt.

        Returns:
            Der entschlüsselte Klartext-String.
            The decrypted plaintext string.

        Raises:
            click.ClickException: Wenn der Token ungültig ist (z.B. falscher Schlüssel oder manipulierte Daten).
                                  If the token is invalid (e.g., wrong key or tampered data).
        """
        try:
            encoded_text = ciphertext.encode('utf-8') # Kodiert den verschlüsselten String in Bytes.
            decrypted_text = self.fernet.decrypt(encoded_text) # Entschlüsselt die Bytes.
            return decrypted_text.decode('utf-8') # Dekodiert die entschlüsselten Bytes zurück in einen String.
        except InvalidToken as e:
            # Fängt InvalidToken ab, was auf einen falschen Schlüssel oder manipulierte Daten hinweist.
            raise click.ClickException(f"Decryption failed: Invalid key or corrupted data. ({e})")

def _load_key(key_path: Optional[str] = None) -> bytes:
    """
    Lädt den Fernet-Schlüssel aus verschiedenen Quellen:
    1. Umgebungsvariable 'ENVCYPT_KEY'
    2. Angegebener Schlüsselpfad
    3. Standard-Schlüsseldatei '.envcrypt_key' im aktuellen Verzeichnis
    Lädt den Schlüssel nicht, wenn er nicht existiert.

    Loads the Fernet key from various sources:
    1. Environment variable 'ENVCYPT_KEY'
    2. Specified key path
    3. Default key file '.envcrypt_key' in the current directory
    Does not load the key if it doesn't exist.

    Args:
        key_path: Optionaler Pfad zu einer Datei, die den Schlüssel enthält.
                  Optional path to a file containing the key.

    Returns:
        Der geladene Fernet-Schlüssel als Bytes.
        The loaded Fernet key as bytes.

    Raises:
        click.ClickException: Wenn kein Schlüssel gefunden werden kann.
                              If no key can be found.
    """
    key: Optional[bytes] = None # Initialisiert den Schlüssel als None.

    # 1. Schlüssel aus Umgebungsvariable laden
    env_key = os.getenv('ENVCYPT_KEY') # Holt den Schlüssel aus der Umgebungsvariable.
    if env_key:
        try:
            key = base64.urlsafe_b64decode(env_key) # Versucht, den Base64-kodierten Schlüssel zu dekodieren.
            click.echo("Key loaded from ENVCYPT_KEY environment variable.", err=True) # Info-Nachricht.
            return key
        except ValueError:
            # Fängt Fehler beim Dekodieren ab, falls der Schlüssel ungültig ist.
            click.echo("Warning: ENVCYPT_KEY environment variable contains an invalid Base64 key.", err=True)

    # 2. Schlüssel aus angegebener Datei laden
    if key_path:
        key_file_path = Path(key_path) # Erstellt ein Path-Objekt.
        if key_file_path.exists():
            try:
                key = key_file_path.read_bytes() # Liest den Schlüssel direkt aus der Datei.
                click.echo(f"Key loaded from file: {key_file_path}", err=True) # Info-Nachricht.
                return key
            except Exception as e:
                # Fängt allgemeine Dateilesefehler ab.
                click.echo(f"Error reading key from {key_file_path}: {e}", err=True)
        else:
            click.echo(f"Warning: Key file not found at {key_file_path}", err=True)

    # 3. Schlüssel aus Standarddatei laden
    default_key_file = Path.cwd() / '.envcrypt_key' # Definiert den Standard-Schlüsseldateipfad im aktuellen Verzeichnis.
    if default_key_file.exists():
        try:
            key = default_key_file.read_bytes() # Liest den Schlüssel aus der Standarddatei.
            click.echo(f"Key loaded from default file: {default_key_file}", err=True) # Info-Nachricht.
            return key
        except Exception as e:
            # Fängt allgemeine Dateilesefehler ab.
            click.echo(f"Error reading key from {default_key_file}: {e}", err=True)

    # Wenn kein Schlüssel gefunden wurde
    raise click.ClickException(
        "No encryption key found. Please provide a key via ENVCYPT_KEY environment variable, "
        "the --key-file option, or generate one using 'envcrypt generate-key'."
    )

@click.group()
@click.option('--key-file', type=click.Path(exists=True, dir_okay=False, readable=True),
              help="Path to the encryption key file. Overrides ENVCYPT_KEY env var if specified.",
              default=None)
@click.option('--config', 'config_path', type=click.Path(dir_okay=False), default=None,
              help="Path to a JSON config file (default: .envcrypt.json, if present).")
@click.pass_context
def cli(ctx: click.Context, key_file: Optional[str], config_path: Optional[str]) -> None:
    """
    EnvCrypt CLI utility for encrypting and decrypting environment variables and files.
    Ein CLI-Dienstprogramm zum Verschlüsseln und Entschlüsseln von Umgebungsvariablen und Dateien.

    Settings such as the key file path can be pre-defined in a JSON config file so they
    do not have to be passed on every call. Precedence: CLI flag > config file >
    environment variable > built-in default.
    """
    ctx.ensure_object(dict) # Stellt sicher, dass das Kontextobjekt ein Dict ist.
    try:
        config = load_config(config_path) # Lädt die (optionale) Konfigurationsdatei.
    except click.ClickException as e:
        click.echo(f"Error: {e}", err=True)
        ctx.exit(1)
        return
    ctx.obj['CONFIG'] = config # Config für Unterbefehle (z.B. generate-key) bereitstellen.
    if ctx.invoked_subcommand != 'generate-key': # Der Befehl 'generate-key' benötigt keinen Schlüssel zum Start.
        # Schlüsseldateipfad nach der Vorrangregel auflösen (Flag > Config > Env).
        resolved_key_file = resolve_setting(key_file, config, 'key_file',
                                            'ENVCRYPT_KEY_FILE', None)
        try:
            key = _load_key(resolved_key_file) # Versucht, den Schlüssel zu laden.
            ctx.obj['CRYPTOR'] = EnvCryptor(key) # Speichert die EnvCryptor-Instanz im Kontext.
        except click.ClickException as e:
            # Fängt ClickExceptions vom Schlüssel-Laden ab und gibt sie weiter.
            click.echo(f"Error: {e}", err=True)
            ctx.exit(1) # Beendet das Programm mit Fehlercode.


@cli.command('generate-key')
@click.option('--output', type=click.Path(dir_okay=False, writable=True),
              default=None, help="Output file to save the generated key "
                                  "(default: .envcrypt_key, or 'key_output' from the config).")
@click.pass_context
def generate_key_command(ctx: click.Context, output: Optional[str]) -> None:
    """
    Generates a new Fernet encryption key and saves it to a file.
    Erzeugt einen neuen Fernet-Verschlüsselungsschlüssel und speichert ihn in einer Datei.
    """
    config = ctx.obj.get('CONFIG', {}) if ctx.obj else {}
    # Ausgabepfad nach der Vorrangregel auflösen (Flag > Config > Env > Default).
    output = resolve_setting(output, config, 'key_output',
                             'ENVCRYPT_KEY_OUTPUT', '.envcrypt_key')
    key = Fernet.generate_key() # Generiert einen neuen Fernet-Schlüssel.
    output_path = Path(output) # Erstellt ein Path-Objekt für die Ausgabedatei.
    try:
        output_path.write_bytes(key) # Schreibt den Schlüssel in die Datei.
        click.echo(f"Successfully generated new Fernet key and saved to: {output_path}")
        click.echo(f"Please keep this key secure. You can also set it as an environment variable: ENVCYPT_KEY={key.decode('utf-8')}")
    except Exception as e:
        # Fängt Fehler beim Schreiben der Datei ab.
        raise click.ClickException(f"Failed to write key to {output_path}: {e}")

@cli.command('encrypt')
@click.argument('plaintext', type=str)
@click.pass_context
def encrypt_command(ctx: click.Context, plaintext: str) -> None:
    """
    Encrypts a single plaintext string.
    Verschlüsselt einen einzelnen Klartext-String.
    """
    cryptor: EnvCryptor = ctx.obj['CRYPTOR'] # Holt die EnvCryptor-Instanz aus dem Kontext.
    encrypted_text = cryptor.encrypt(plaintext) # Verschlüsselt den Text.
    click.echo(encrypted_text) # Gibt den verschlüsselten Text aus.

@cli.command('decrypt')
@click.argument('ciphertext', type=str)
@click.pass_context
def decrypt_command(ctx: click.Context, ciphertext: str) -> None:
    """
    Decrypts a single encrypted string.
    Entschlüsselt einen einzelnen verschlüsselten String.
    """
    cryptor: EnvCryptor = ctx.obj['CRYPTOR'] # Holt die EnvCryptor-Instanz aus dem Kontext.
    decrypted_text = cryptor.decrypt(ciphertext) # Entschlüsselt den Text.
    click.echo(decrypted_text) # Gibt den entschlüsselten Text aus.

def _process_env_file(cryptor: EnvCryptor, input_path: Path, output_path: Path, encrypt: bool) -> None:
    """
    Hilfsfunktion zum Ver- oder Entschlüsseln einer .env-Datei.
    Helper function to encrypt or decrypt an .env file.
    """
    try:
        lines = input_path.read_text('utf-8').splitlines() # Liest alle Zeilen der Eingabedatei.
        output_lines = [] # Liste für die Ausgabedatei.

        for line in lines:
            stripped_line = line.strip() # Entfernt Leerzeichen am Anfang und Ende.
            if not stripped_line or stripped_line.startswith('#'):
                # Überspringt leere Zeilen oder Kommentare.
                output_lines.append(line)
                continue

            parts = line.split('=', 1) # Teilt die Zeile am ersten '='.
            if len(parts) == 2:
                var_name, var_value = parts[0], parts[1] # Trennt Variablennamen und -wert.
                if encrypt:
                    processed_value = cryptor.encrypt(var_value) # Verschlüsselt den Wert.
                    output_lines.append(f"{var_name}={processed_value}") # Fügt die verschlüsselte Zeile hinzu.
                else:
                    try:
                        processed_value = cryptor.decrypt(var_value) # Entschlüsselt den Wert.
                        output_lines.append(f"{var_name}={processed_value}") # Fügt die entschlüsselte Zeile hinzu.
                    except click.ClickException as e:
                        # Fängt Entschlüsselungsfehler ab und warnt den Benutzer.
                        click.echo(f"Warning: Could not decrypt value for '{var_name}' in line '{line}': {e}", err=True)
                        output_lines.append(line) # Fügt die ursprüngliche Zeile hinzu, falls Entschlüsselung fehlschlägt.
            else:
                output_lines.append(line) # Fügt Zeilen ohne '=' unverändert hinzu.

        output_path.write_text('\n'.join(output_lines), 'utf-8') # Schreibt die verarbeiteten Zeilen in die Ausgabedatei.
        action = "encrypted" if encrypt else "decrypted" # Bestimmt die Aktion für die Erfolgsmeldung.
        click.echo(f"Successfully {action} file '{input_path}' to '{output_path}'")

    except FileNotFoundError:
        raise click.ClickException(f"File not found: {input_path}") # Fehler, wenn die Eingabedatei nicht existiert.
    except Exception as e:
        raise click.ClickException(f"Failed to process file {input_path}: {e}") # Allgemeine Fehler beim Verarbeiten der Datei.

@cli.command('encrypt-file')
@click.argument('input_file', type=click.Path(exists=True, dir_okay=False, readable=True))
@click.argument('output_file', type=click.Path(dir_okay=False, writable=True))
@click.pass_context
def encrypt_file_command(ctx: click.Context, input_file: str, output_file: str) -> None:
    """
    Encrypts all variable values in an .env file and saves to a new file.
    Verschlüsselt alle Variablenwerte in einer .env-Datei und speichert sie in einer neuen Datei.
    """
    cryptor: EnvCryptor = ctx.obj['CRYPTOR'] # Holt die EnvCryptor-Instanz aus dem Kontext.
    _process_env_file(cryptor, Path(input_file), Path(output_file), True) # Ruft die Hilfsfunktion zum Verschlüsseln auf.

@cli.command('decrypt-file')
@click.argument('input_file', type=click.Path(exists=True, dir_okay=False, readable=True))
@click.argument('output_file', type=click.Path(dir_okay=False, writable=True))
@click.pass_context
def decrypt_file_command(ctx: click.Context, input_file: str, output_file: str) -> None:
    """
    Decrypts all encrypted variable values in an .env file and saves to a new file.
    Entschlüsselt alle verschlüsselten Variablenwerte in einer .env-Datei und speichert sie in einer neuen Datei.
    """
    cryptor: EnvCryptor = ctx.obj['CRYPTOR'] # Holt die EnvCryptor-Instanz aus dem Kontext.
    _process_env_file(cryptor, Path(input_file), Path(output_file), False) # Ruft die Hilfsfunktion zum Entschlüsseln auf.

if __name__ == '__main__':
    cli(obj={})

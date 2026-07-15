import pytest
import os
import json
import base64
import click
from unittest.mock import patch, MagicMock
from pathlib import Path
from click.testing import CliRunner

from main import EnvCryptor, _load_key, cli, Fernet, load_config, resolve_setting

# Helper function to generate a valid Fernet key for testing
def generate_test_key() -> bytes:
    """Generiert einen gültigen Fernet-Testschlüssel."""
    return Fernet.generate_key()

@pytest.fixture
def fernet_key() -> bytes:
    """Fixture, die einen Fernet-Schlüssel für Tests bereitstellt."""
    return generate_test_key()

@pytest.fixture
def cryptor(fernet_key: bytes) -> EnvCryptor:
    """Fixture, die eine EnvCryptor-Instanz für Tests bereitstellt."""
    return EnvCryptor(fernet_key)

@pytest.fixture
def runner() -> CliRunner:
    """Fixture, die einen CliRunner für Tests bereitstellt."""
    # mix_stderr=False, damit stdout (Nutzdaten) und stderr (Info-/Warn-Meldungen
    # via err=True) getrennt geprüft werden können.
    return CliRunner(mix_stderr=False)

# --- Test EnvCryptor Class ---
def test_envcryptor_encrypt_decrypt(cryptor: EnvCryptor):
    """Testet die Verschlüsselungs- und Entschlüsselungsfunktionen der EnvCryptor-Klasse."""
    plaintext = "supersecretvalue123"
    encrypted = cryptor.encrypt(plaintext)
    assert plaintext != encrypted # Überprüft, ob der Klartext nicht gleich dem verschlüsselten Text ist.
    decrypted = cryptor.decrypt(encrypted)
    assert plaintext == decrypted # Überprüft, ob der entschlüsselte Text dem ursprünglichen Klartext entspricht.

def test_envcryptor_invalid_token(cryptor: EnvCryptor):
    """Testet die Fehlerbehandlung bei ungültigem Token während der Entschlüsselung."""
    with pytest.raises(click.ClickException, match="Invalid key or corrupted data"):
        # Versucht, einen ungültigen Token zu entschlüsseln.
        cryptor.decrypt("invalid_encrypted_string_that_is_not_base64_or_fernet")

    # Test mit einem anderen, aber gültigen Schlüssel
    other_key = generate_test_key()
    other_cryptor = EnvCryptor(other_key)
    plaintext = "another secret"
    encrypted_with_other_key = other_cryptor.encrypt(plaintext)
    with pytest.raises(click.ClickException, match="Invalid key or corrupted data"):
        # Versucht, mit dem falschen Schlüssel zu entschlüsseln.
        cryptor.decrypt(encrypted_with_other_key)

# --- Test _load_key function ---
def test_load_key_from_env_var(fernet_key: bytes):
    """Testet das Laden des Schlüssels aus einer Umgebungsvariable."""
    with patch.dict(os.environ, {'ENVCYPT_KEY': base64.urlsafe_b64encode(fernet_key).decode('utf-8')}):
        loaded_key = _load_key() # Lädt den Schlüssel.
        assert loaded_key == fernet_key # Überprüft, ob der geladene Schlüssel korrekt ist.

def test_load_key_from_env_var_invalid_base64():
    """Testet das Laden des Schlüssels aus einer Umgebungsvariable mit ungültigem Base64."""
    with patch.dict(os.environ, {'ENVCYPT_KEY': 'not-a-valid-base64-key'}):
        # Der Schlüssel sollte nicht geladen werden, aber es sollte keine Ausnahme ausgelöst werden,
        # da die Warnung nur ausgegeben wird und dann andere Quellen geprüft werden.
        # Da hier keine anderen Quellen vorhanden sind, schlägt es fehl.
        with pytest.raises(click.ClickException, match="No encryption key found"):
            _load_key()

def test_load_key_from_key_file(tmp_path: Path, fernet_key: bytes):
    """Testet das Laden des Schlüssels aus einer Schlüsseldatei."""
    key_file = tmp_path / "test_key.key" # Erstellt einen temporären Schlüsseldateipfad.
    key_file.write_bytes(fernet_key) # Schreibt den Schlüssel in die Datei.

    loaded_key = _load_key(key_path=str(key_file)) # Lädt den Schlüssel über den Pfad.
    assert loaded_key == fernet_key # Überprüft den geladenen Schlüssel.

def test_load_key_from_default_key_file(tmp_path: Path, fernet_key: bytes):
    """Testet das Laden des Schlüssels aus der Standard-Schlüsseldatei."""
    # Simuliert das aktuelle Arbeitsverzeichnis
    with patch('pathlib.Path.cwd', return_value=tmp_path):
        default_key_file = tmp_path / ".envcrypt_key" # Erstellt den Standard-Schlüsseldateipfad.
        default_key_file.write_bytes(fernet_key) # Schreibt den Schlüssel in die Datei.

        loaded_key = _load_key() # Lädt den Schlüssel.
        assert loaded_key == fernet_key # Überprüft den geladenen Schlüssel.

def test_load_key_precedence(tmp_path: Path, fernet_key: bytes):
    """Testet die Priorität beim Laden des Schlüssels (Env > Specific File > Default File)."""
    # Key in Umgebungsvariable
    env_key = base64.urlsafe_b64encode(b"env_key").decode('utf-8')
    # Key in spezifischer Datei
    specific_key_file = tmp_path / "specific.key"
    specific_key = b"specific_file_key"
    specific_key_file.write_bytes(specific_key)
    # Key in Standarddatei
    default_key_file = tmp_path / ".envcrypt_key"
    default_key = b"default_file_key"
    default_key_file.write_bytes(default_key)

    with patch.dict(os.environ, {'ENVCYPT_KEY': env_key}):
        # Env-Var sollte Priorität haben
        assert _load_key(key_path=str(specific_key_file)) == base64.urlsafe_b64decode(env_key)

    # Ohne Env-Var, spezifische Datei sollte Priorität haben
    with patch.dict(os.environ, clear=True):
        assert _load_key(key_path=str(specific_key_file)) == specific_key

    # Ohne Env-Var und spezifische Datei, Standarddatei sollte Priorität haben
    with patch('pathlib.Path.cwd', return_value=tmp_path):
        with patch.dict(os.environ, clear=True):
            assert _load_key() == default_key

def test_load_key_not_found():
    """Testet den Fall, wenn kein Schlüssel gefunden werden kann."""
    with patch.dict(os.environ, clear=True): # Löscht alle Umgebungsvariablen.
        with patch('pathlib.Path.exists', return_value=False): # Simuliert, dass keine Dateien existieren.
            with pytest.raises(click.ClickException, match="No encryption key found"):
                _load_key()

# --- Test CLI Commands ---
def test_cli_generate_key(runner: CliRunner, tmp_path: Path):
    """Testet den 'generate-key'-CLI-Befehl."""
    output_key_path = tmp_path / "generated.key" # Temporärer Pfad für den generierten Schlüssel.
    result = runner.invoke(cli, ['generate-key', '--output', str(output_key_path)])
    assert result.exit_code == 0 # Überprüft, ob der Befehl erfolgreich war.
    assert "Successfully generated new Fernet key" in result.output # Überprüft die Ausgabemeldung.
    assert output_key_path.exists() # Überprüft, ob die Schlüsseldatei erstellt wurde.
    key_content = output_key_path.read_bytes() # Liest den Schlüsselinhalt.
    assert Fernet.generate_key() != key_content # Der Schlüssel sollte nicht leer sein, aber auch nicht identisch mit einem neu generierten.
    # Versuche, den Schlüssel zu dekodieren, um seine Gültigkeit zu prüfen
    try:
        Fernet(key_content)
    except Exception:
        pytest.fail("Generated key is not a valid Fernet key.")

def test_cli_encrypt_decrypt_string(runner: CliRunner, tmp_path: Path, fernet_key: bytes):
    """Testet die 'encrypt' und 'decrypt'-CLI-Befehle für Strings."""
    # Save key to a file for CLI to pick up
    key_file = tmp_path / "cli_key.key" # Erstellt einen temporären Schlüsseldateipfad.
    key_file.write_bytes(fernet_key) # Schreibt den Schlüssel in die Datei.

    plaintext = "CLI_SECRET_VALUE" # Klartext für den Test.

    # Encrypt
    encrypt_result = runner.invoke(cli, ['--key-file', str(key_file), 'encrypt', plaintext])
    assert encrypt_result.exit_code == 0 # Überprüft den Exit-Code.
    encrypted_text = encrypt_result.output.strip() # Holt den verschlüsselten Text.
    assert encrypted_text != plaintext # Überprüft, dass es nicht der Klartext ist.

    # Decrypt
    decrypt_result = runner.invoke(cli, ['--key-file', str(key_file), 'decrypt', encrypted_text])
    assert decrypt_result.exit_code == 0 # Überprüft den Exit-Code.
    decrypted_text = decrypt_result.output.strip() # Holt den entschlüsselten Text.
    assert decrypted_text == plaintext # Überprüft, dass es dem ursprünglichen Klartext entspricht.

def test_cli_encrypt_decrypt_file(runner: CliRunner, tmp_path: Path, fernet_key: bytes):
    """Testet die 'encrypt-file' und 'decrypt-file'-CLI-Befehle."""
    key_file = tmp_path / "cli_file_key.key" # Erstellt einen temporären Schlüsseldateipfad.
    key_file.write_bytes(fernet_key) # Schreibt den Schlüssel in die Datei.

    # Erstellt eine Test-Env-Datei
    input_env_content = """
# This is a comment
VAR1=value1
VAR2=another_value_with_spaces
EMPTY_VAR=
VAR3=value3_with_special_chars!@#$%^&*()
"""
    input_file = tmp_path / "test.env" # Erstellt die Eingabedatei.
    input_file.write_text(input_env_content)

    encrypted_file = tmp_path / "test.env.encrypted" # Pfad für die verschlüsselte Datei.
    decrypted_file = tmp_path / "test.env.decrypted" # Pfad für die entschlüsselte Datei.

    # Encrypt file
    encrypt_result = runner.invoke(cli, ['--key-file', str(key_file), 'encrypt-file', str(input_file), str(encrypted_file)])
    assert encrypt_result.exit_code == 0 # Überprüft den Exit-Code.
    assert f"Successfully encrypted file '{input_file}' to '{encrypted_file}'" in encrypt_result.output # Überprüft die Ausgabemeldung.
    assert encrypted_file.exists() # Überprüft, ob die verschlüsselte Datei existiert.

    encrypted_content = encrypted_file.read_text() # Liest den Inhalt der verschlüsselten Datei.
    assert "value1" not in encrypted_content # Überprüft, dass der Klartext nicht mehr vorhanden ist.
    assert "VAR1=" in encrypted_content # Überprüft, dass der Variablenname noch vorhanden ist.
    assert "# This is a comment" in encrypted_content # Kommentare sollten unverändert bleiben.
    assert "EMPTY_VAR=" in encrypted_content # Leere Variablen sollten auch verarbeitet werden.

    # Decrypt file
    decrypt_result = runner.invoke(cli, ['--key-file', str(key_file), 'decrypt-file', str(encrypted_file), str(decrypted_file)])
    assert decrypt_result.exit_code == 0 # Überprüft den Exit-Code.
    assert f"Successfully decrypted file '{encrypted_file}' to '{decrypted_file}'" in decrypt_result.output # Überprüft die Ausgabemeldung.
    assert decrypted_file.exists() # Überprüft, ob die entschlüsselte Datei existiert.

    decrypted_content = decrypted_file.read_text() # Liest den Inhalt der entschlüsselten Datei.
    assert decrypted_content.strip() == input_env_content.strip() # Überprüft, ob der entschlüsselte Inhalt dem ursprünglichen entspricht.

def test_cli_decrypt_file_with_mixed_content_and_invalid_encrypted_value(runner: CliRunner, tmp_path: Path, fernet_key: bytes):
    """Testet das Entschlüsseln einer Datei mit gemischtem Inhalt und einem ungültigen verschlüsselten Wert."""
    key_file = tmp_path / "cli_mixed_key.key" # Temporärer Schlüsseldateipfad.
    key_file.write_bytes(fernet_key) # Schreibt den Schlüssel in die Datei.

    # Erstellt eine EnvCryptor-Instanz, um einen gültigen verschlüsselten Wert zu erzeugen
    cryptor = EnvCryptor(fernet_key)
    valid_encrypted_value = cryptor.encrypt("valid_secret")

    input_env_content = f"""
# This is a comment
VAR1=value1
VAR2={valid_encrypted_value}
VAR3=not_encrypted_value
VAR4=invalid_encrypted_value_xyz
"""
    input_file = tmp_path / "mixed.env" # Eingabedatei mit gemischtem Inhalt.
    input_file.write_text(input_env_content)

    output_file = tmp_path / "mixed.env.decrypted" # Ausgabedatei.

    decrypt_result = runner.invoke(cli, ['--key-file', str(key_file), 'decrypt-file', str(input_file), str(output_file)])

    assert decrypt_result.exit_code == 0 # Sollte immer noch erfolgreich sein, aber eine Warnung ausgeben.
    assert "Warning: Could not decrypt value for 'VAR4'" in decrypt_result.stderr # Überprüft die Warnung.
    assert output_file.exists() # Überprüft, ob die Ausgabedatei existiert.

    decrypted_content = output_file.read_text().strip() # Holt den entschlüsselten Inhalt.
    expected_content = f"""
# This is a comment
VAR1=value1
VAR2=valid_secret
VAR3=not_encrypted_value
VAR4=invalid_encrypted_value_xyz
""".strip()
    assert decrypted_content == expected_content # Überprüft, ob die gültigen Werte entschlüsselt wurden und die ungültigen unverändert blieben.

def test_cli_no_key_provided(runner: CliRunner):
    """Testet den Fall, wenn kein Schlüssel für Verschlüsselungs-/Entschlüsselungsbefehle bereitgestellt wird."""
    with patch.dict(os.environ, clear=True): # Stellt sicher, dass keine Umgebungsvariablen gesetzt sind.
        with patch('pathlib.Path.exists', return_value=False): # Stellt sicher, dass keine Schlüsseldateien existieren.
            result = runner.invoke(cli, ['encrypt', 'some_value']) # Versucht, ohne Schlüssel zu verschlüsseln.
            assert result.exit_code == 1 # Erwartet einen Fehler-Exit-Code.
            assert "Error: No encryption key found." in result.stderr # Überprüft die Fehlermeldung.


# --- Test JSON configuration file support ---
def test_load_config_reads_json_object(tmp_path: Path):
    """Eine gültige JSON-Config wird als Dictionary geladen."""
    cfg = tmp_path / "cfg.json"
    cfg.write_text(json.dumps({"key_file": "some.key", "key_output": "out.key"}))
    assert load_config(str(cfg)) == {"key_file": "some.key", "key_output": "out.key"}


def test_load_config_missing_explicit_raises(tmp_path: Path):
    """Eine explizit angeforderte, fehlende Config ist ein Fehler."""
    with pytest.raises(click.ClickException, match="not found"):
        load_config(str(tmp_path / "nope.json"))


def test_load_config_invalid_json_raises(tmp_path: Path):
    """Ungültiges JSON löst einen Fehler aus."""
    cfg = tmp_path / "bad.json"
    cfg.write_text("{not valid json}")
    with pytest.raises(click.ClickException, match="Could not read configuration file"):
        load_config(str(cfg))


def test_load_config_non_object_raises(tmp_path: Path):
    """Eine JSON-Datei, die kein Objekt ist, wird abgelehnt."""
    cfg = tmp_path / "list.json"
    cfg.write_text(json.dumps([1, 2, 3]))
    with pytest.raises(click.ClickException, match="must contain a JSON object"):
        load_config(str(cfg))


def test_load_config_rejects_raw_key(tmp_path: Path):
    """Ein roher Schlüssel in der Config wird aus Sicherheitsgründen abgelehnt."""
    cfg = tmp_path / "secret.json"
    cfg.write_text(json.dumps({"key": "leaked"}))
    with pytest.raises(click.ClickException, match="must not contain a raw key"):
        load_config(str(cfg))


def test_resolve_setting_precedence():
    """Vorrang: CLI > Config > Env > Default."""
    with patch.dict(os.environ, {"ENVCRYPT_X": "envv"}, clear=True):
        assert resolve_setting("cli", {"k": "cfg"}, "k", "ENVCRYPT_X", "def") == "cli"
        assert resolve_setting(None, {"k": "cfg"}, "k", "ENVCRYPT_X", "def") == "cfg"
        assert resolve_setting(None, {}, "k", "ENVCRYPT_X", "def") == "envv"
    with patch.dict(os.environ, {}, clear=True):
        assert resolve_setting(None, {}, "k", "ENVCRYPT_X", "def") == "def"


def test_cli_config_key_file_used(runner: CliRunner, tmp_path: Path, fernet_key: bytes):
    """Der Schlüsseldateipfad wird aus der Config gelesen (kein --key-file nötig)."""
    key_file = tmp_path / "cfg_key.key"
    key_file.write_bytes(fernet_key)
    cfg = tmp_path / ".envcrypt.json"
    cfg.write_text(json.dumps({"key_file": str(key_file)}))

    plaintext = "CONFIG_SECRET"
    with patch.dict(os.environ, {}, clear=True):
        enc = runner.invoke(cli, ['--config', str(cfg), 'encrypt', plaintext])
        assert enc.exit_code == 0, enc.output
        encrypted = enc.stdout.strip()
        assert encrypted != plaintext
        dec = runner.invoke(cli, ['--config', str(cfg), 'decrypt', encrypted])
        assert dec.exit_code == 0, dec.output
        assert dec.stdout.strip() == plaintext


def test_cli_flag_overrides_config_key_file(runner: CliRunner, tmp_path: Path, fernet_key: bytes):
    """--key-file hat Vorrang vor dem key_file aus der Config."""
    # Korrekte Schlüsseldatei (per Flag) und eine andere, falsche in der Config.
    right_key = tmp_path / "right.key"
    right_key.write_bytes(fernet_key)
    wrong_key = tmp_path / "wrong.key"
    wrong_key.write_bytes(Fernet.generate_key())
    cfg = tmp_path / ".envcrypt.json"
    cfg.write_text(json.dumps({"key_file": str(wrong_key)}))

    plaintext = "OVERRIDE_ME"
    with patch.dict(os.environ, {}, clear=True):
        # Verschlüsseln mit dem korrekten Schlüssel via Flag (überschreibt die Config).
        enc = runner.invoke(cli, ['--config', str(cfg), '--key-file', str(right_key),
                                  'encrypt', plaintext])
        assert enc.exit_code == 0, enc.output
        encrypted = enc.stdout.strip()
        # Entschlüsseln mit demselben Flag-Schlüssel muss gelingen.
        dec = runner.invoke(cli, ['--config', str(cfg), '--key-file', str(right_key),
                                  'decrypt', encrypted])
        assert dec.exit_code == 0, dec.output
        assert dec.stdout.strip() == plaintext


def test_cli_generate_key_output_from_config(runner: CliRunner, tmp_path: Path):
    """generate-key nutzt den Ausgabepfad aus der Config, wenn --output fehlt."""
    out_key = tmp_path / "from_config.key"
    cfg = tmp_path / ".envcrypt.json"
    cfg.write_text(json.dumps({"key_output": str(out_key)}))

    result = runner.invoke(cli, ['--config', str(cfg), 'generate-key'])
    assert result.exit_code == 0, result.output
    assert out_key.exists()
    Fernet(out_key.read_bytes())  # muss ein gültiger Fernet-Schlüssel sein


def test_cli_config_via_env_var(runner: CliRunner, tmp_path: Path, fernet_key: bytes):
    """ENVCRYPT_CONFIG kann die Config-Datei bereitstellen (ohne --config)."""
    key_file = tmp_path / "envcfg_key.key"
    key_file.write_bytes(fernet_key)
    cfg = tmp_path / "custom_config.json"
    cfg.write_text(json.dumps({"key_file": str(key_file)}))

    with patch.dict(os.environ, {"ENVCRYPT_CONFIG": str(cfg)}, clear=True):
        enc = runner.invoke(cli, ['encrypt', 'VIA_ENV'])
        assert enc.exit_code == 0, enc.output
        assert enc.stdout.strip() != "VIA_ENV"

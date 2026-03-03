# EnvCrypt CLI Architecture Deep Dive

This document provides a detailed overview of the architectural design and core components of the EnvCrypt CLI utility.

## 1. Introduction

EnvCrypt CLI is designed to provide a secure and convenient way to manage sensitive environment variables, particularly those stored in `.env` files. It leverages established cryptographic primitives to ensure data confidentiality and integrity. The primary goals of the architecture are:

*   **Security**: Utilize strong, industry-standard encryption.
*   **Usability**: Provide a simple, intuitive command-line interface.
*   **Flexibility**: Support various key management strategies.
*   **Maintainability**: Employ clear, modular, and testable code.

## 2. Core Components

The architecture is centered around two main logical components: the `EnvCryptor` class and the key management mechanism, all orchestrated by the `click` CLI framework.

### 2.1. `EnvCryptor` Class

The `EnvCryptor` class is the heart of the encryption and decryption logic.

*   **Purpose**: Encapsulates the symmetric encryption/decryption operations.
*   **Technology**: It uses `cryptography.fernet.Fernet` from the Python `cryptography` library. Fernet is an opinionated symmetric encryption scheme that provides strong guarantees:
    *   **Confidentiality**: Data is encrypted using AES in CBC mode with a 128-bit key.
    *   **Integrity and Authenticity**: Data is signed using HMAC-SHA256, preventing tampering.
    *   **Key Derivation**: Uses PBKDF2 for key derivation.
    *   **Initialization Vector (IV) Management**: Handles IV generation and management automatically.
    *   **Timestamping**: Includes a timestamp in the token, allowing for optional token expiration policies (though not currently implemented in EnvCrypt CLI).
*   **Initialization**: An `EnvCryptor` instance is initialized with a `bytes` object representing the Fernet key. This key must be URL-safe Base64 encoded.
*   **Methods**:
    *   `encrypt(plaintext: str) -> str`: Takes a plaintext string, encodes it to UTF-8, encrypts it using the internal Fernet instance, and returns the Base64-encoded ciphertext string.
    *   `decrypt(ciphertext: str) -> str`: Takes a Base64-encoded ciphertext string, decodes it, decrypts it using the internal Fernet instance, and returns the UTF-8 decoded plaintext string. It includes error handling for `InvalidToken` exceptions, which occur if the key is incorrect or the data has been tampered with.

### 2.2. Key Management (`_load_key` function)

Secure key management is paramount for any encryption utility. EnvCrypt CLI provides a flexible key loading mechanism, prioritizing security and convenience.

*   **Loading Order**: The `_load_key` function attempts to load the Fernet key in a specific hierarchical order:
    1.  **Environment Variable (`ENVCYPT_KEY`)**: This is the highest priority. If `ENVCYPT_KEY` is set, its value (expected to be a URL-safe Base64 encoded key string) is decoded and used. This is ideal for CI/CD pipelines and production environments where secrets are injected as environment variables.
    2.  **Explicit Key File (`--key-file` option)**: If the user provides a path via the `--key-file` CLI option, the tool attempts to read the key directly from this file. This allows for specific key files to be used for different projects or contexts.
    3.  **Default Key File (`.envcrypt_key`)**: As a fallback, the tool looks for a file named `.envcrypt_key` in the current working directory. This is convenient for local development but less secure for shared environments.
*   **Error Handling**: If no key can be successfully loaded from any of these sources, a `click.ClickException` is raised, informing the user about the missing key and available options.
*   **Key Generation**: The `generate-key` command uses `Fernet.generate_key()` to create a new, random, and cryptographically secure Fernet key. It then saves this key to a specified file (default `.envcrypt_key`) and also prints it to the console, allowing the user to set it as an environment variable.

## 3. CLI Design (using `click`)

The command-line interface is built using the `click` library, which simplifies the creation of elegant and robust CLIs.

*   **`@click.group()`**: The main `cli` function acts as the entry point and a group for subcommands.
*   **`@click.option('--key-file', ...)`**: A global option for specifying a key file, applied to all commands within the group. The key is loaded once at the start of the `cli` execution and stored in `ctx.obj` for all subcommands to access.
*   **Subcommands**:
    *   `generate-key`: Creates a new Fernet key. This command does **not** require an existing key to run.
    *   `encrypt <plaintext>`: Encrypts a single string.
    *   `decrypt <ciphertext>`: Decrypts a single string.
    *   `encrypt-file <input_file> <output_file>`: Reads an `.env` file, encrypts each variable's value, and writes to a new file.
    *   `decrypt-file <input_file> <output_file>`: Reads an encrypted `.env` file, decrypts each variable's value, and writes to a new file.
*   **File Processing (`_process_env_file`)**: A shared internal function handles the logic for reading `.env` files, parsing lines, applying encryption/decryption to values, and writing the modified content. It correctly identifies and skips comments and preserves lines that do not contain variable assignments. It also handles cases where decryption might fail for individual lines, allowing the process to continue with a warning.
*   **Type Hinting and Docstrings**: All functions and methods are type-hinted and include comprehensive docstrings to improve code readability, maintainability, and enable static analysis.

## 4. Security Considerations

*   **Key Secrecy**: The security of EnvCrypt CLI entirely depends on the secrecy of the Fernet key. Users are strongly advised to:
    *   **Never commit encryption keys to version control.**
    *   Use secure methods (e.g., environment variables, secret management services) to provide keys in production.
    *   Protect key files with appropriate file system permissions.
*   **Fernet**: The choice of Fernet ensures that common cryptographic pitfalls (like improper IV reuse or weak MACs) are avoided, as it's an "authenticated encryption with associated data" (AEAD) scheme.
*   **Error Handling**: The explicit `InvalidToken` handling helps detect tampering or incorrect keys, preventing silent failures.

## 5. Future Enhancements

*   **Configuration File**: Implement support for a `config.json` or `pyproject.toml` to define default key paths, output formats, or other settings. (This is the suggested initial issue).
*   **Key Rotation**: Add commands or features to facilitate key rotation.
*   **Vault Integration**: Integrate with secret management services like HashiCorp Vault, AWS Secrets Manager, or Azure Key Vault for more robust key management.
*   **Non-interactive Mode**: Option to suppress prompts and warnings for scripting.
*   **Recursive File Processing**: Ability to process multiple `.env` files within a directory structure.
*   **Token Expiration**: Leverage Fernet's built-in timestamping to implement optional token expiration.
*   **Docker Support**: Provide a Dockerfile for easy containerization.

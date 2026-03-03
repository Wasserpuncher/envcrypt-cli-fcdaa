# EnvCrypt CLI

![Python application CI](https://github.com/your-org/envcrypt-cli/actions/workflows/python-app.yml/badge.svg)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A powerful and user-friendly command-line interface (CLI) utility for securely encrypting and decrypting sensitive environment variables and entire `.env` files. Designed with security and ease of use in mind, EnvCrypt CLI helps developers and operations teams manage secrets effectively in various environments.

## Features

*   **Symmetric Encryption**: Uses Fernet symmetric encryption from the `cryptography` library, ensuring strong and tamper-proof data protection.
*   **Key Management**: Supports loading encryption keys from environment variables (`ENVCYPT_KEY`), specified key files, or a default `.envcrypt_key` file. Includes a command to securely generate new keys.
*   **Single Value Encryption/Decryption**: Easily encrypt or decrypt individual strings directly from the command line.
*   **`.env` File Processing**: Encrypt or decrypt all variable values within a standard `.env` file, preserving comments and unassigned lines.
*   **Bilingual Documentation**: Comprehensive documentation available in both English and German.
*   **Enterprise-Ready**: Built with best practices including type hints, docstrings, unit tests, and CI/CD integration.

## Installation

### Prerequisites

*   Python 3.9+
*   `pip` (Python package installer)

### Steps

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/your-org/envcrypt-cli.git
    cd envcrypt-cli
    ```
2.  **Create a virtual environment** (recommended):
    ```bash
    python -m venv venv
    source venv/bin/activate # On Windows use `venv\Scripts\activate`
    ```
3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
4.  **Make the CLI accessible** (optional, but recommended for global use):
    You can either run commands using `python main.py <command>` or create a symlink/alias.
    For development, you can also install in editable mode:
    ```bash
    pip install -e .
    ```
    This allows you to run `envcrypt <command>` directly if your `PATH` includes the virtual environment's `bin` directory.

## Usage

First, you need an encryption key. **Keep this key absolutely secure!**

### 1. Generate an Encryption Key

It's highly recommended to generate a new key for each project or environment.
```bash
envcrypt generate-key --output .envcrypt_key
```
This command will create a file named `.envcrypt_key` in your current directory.
Alternatively, you can copy the output key string and set it as an environment variable:
`export ENVCYPT_KEY="your_generated_base64_key"`

### 2. Encrypt a Single String

```bash
envcrypt encrypt "my_secret_api_key_123"
# Output: gAAAAABi... (a base64-encoded encrypted string)
```

### 3. Decrypt a Single String

```bash
envcrypt decrypt "gAAAAABi..."
# Output: my_secret_api_key_123
```

### 4. Encrypt an `.env` File

Let's say you have an `input.env` file:
```env
# Database Credentials
DB_HOST=localhost
DB_PORT=5432
DB_USER=admin
DB_PASS=supersecurepassword123
API_KEY=my_api_key_value
```

To encrypt it:
```bash
envcrypt encrypt-file input.env output.env.encrypted
```
The `output.env.encrypted` file will contain:
```env
# Database Credentials
DB_HOST=gAAAAABi...
DB_PORT=gAAAAABi...
DB_USER=gAAAAABi...
DB_PASS=gAAAAABi...
API_KEY=gAAAAABi...
```
Comments and lines without an `=` will be preserved as is.

### 5. Decrypt an Encrypted `.env` File

```bash
envcrypt decrypt-file output.env.encrypted decrypted.env
```
The `decrypted.env` file will contain the original plaintext values.

### Key Management Options

EnvCrypt CLI searches for the encryption key in the following order:

1.  **`--key-file <path>` option**: Explicitly specified file path.
2.  **`ENVCYPT_KEY` environment variable**: If the `ENVCYPT_KEY` environment variable is set.
3.  **`.envcrypt_key` file**: A file named `.envcrypt_key` in the current working directory.

It is highly recommended to use an environment variable (e.g., `ENVCYPT_KEY`) in production environments or to manage the key file securely with appropriate permissions. **Never commit your encryption key to version control!**

## Contributing

We welcome contributions! Please see our [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on how to report issues, suggest features, and submit code.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

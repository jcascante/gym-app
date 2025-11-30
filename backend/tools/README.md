# Backend Tools

This directory contains utility scripts and tools for the Gym App backend.

## Available Tools

### 1. Generate Secret Key (`generate_secret_key.py`)

Generate cryptographically secure SECRET_KEY values for JWT authentication.

#### Usage

**Basic usage** (generates a 32-byte key):
```bash
python tools/generate_secret_key.py
```

**Custom length**:
```bash
# Generate a 64-byte key
python tools/generate_secret_key.py --length 64
```

**Generate multiple keys**:
```bash
# Generate 5 keys (useful for multiple environments)
python tools/generate_secret_key.py --multiple 5
```

**Output formats**:
```bash
# Plain format (default)
python tools/generate_secret_key.py

# .env file format
python tools/generate_secret_key.py --format env

# Terraform tfvars format
python tools/generate_secret_key.py --format terraform
```

#### Quick Start Examples

**Add to .env file**:
```bash
cd backend
echo "SECRET_KEY=$(python tools/generate_secret_key.py)" >> .env
```

**Generate for Terraform**:
```bash
cd backend
python tools/generate_secret_key.py --format terraform
# Copy output to terraform/terraform.tfvars
```

**Generate keys for dev, staging, and production**:
```bash
cd backend
python tools/generate_secret_key.py --multiple 3 --format env
```

#### Security Notes

- Uses Python's `secrets` module (cryptographically secure)
- Minimum key length: 16 bytes (enforced)
- Recommended length: 32 bytes (default)
- Keys are URL-safe base64-encoded
- Safe to use in environment variables, config files, and URLs

#### Options

| Flag | Description | Default |
|------|-------------|---------|
| `-l, --length` | Key length in bytes (minimum 16) | 32 |
| `-m, --multiple` | Number of keys to generate | 1 |
| `-f, --format` | Output format: plain, env, terraform | plain |

## Adding New Tools

When adding new tools to this directory:

1. Create a Python script with a descriptive name
2. Add a shebang line: `#!/usr/bin/env python3`
3. Include a docstring explaining usage
4. Make it executable: `chmod +x tools/your_tool.py`
5. Document it in this README
6. Add command-line argument parsing if needed

### Example Tool Structure

```python
#!/usr/bin/env python3
"""
Brief description of the tool.

Usage:
    python tools/your_tool.py [options]
"""
import argparse

def main():
    parser = argparse.ArgumentParser(description="Tool description")
    # Add arguments
    args = parser.parse_args()
    # Tool logic here

if __name__ == "__main__":
    main()
```

## Running Tools with uv

Since this project uses `uv` for package management, you can run tools with:

```bash
# If tool uses dependencies from the project
uv run python tools/generate_secret_key.py

# For standalone tools (like generate_secret_key.py)
python tools/generate_secret_key.py
```

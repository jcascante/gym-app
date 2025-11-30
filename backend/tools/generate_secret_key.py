#!/usr/bin/env python3
"""
Generate a secure SECRET_KEY for JWT token signing.

This tool generates cryptographically secure random keys suitable for
production use in the Gym App backend.

Usage:
    python tools/generate_secret_key.py [--length LENGTH]

Examples:
    # Generate a 32-byte key (default)
    python tools/generate_secret_key.py

    # Generate a 64-byte key
    python tools/generate_secret_key.py --length 64

    # Use in .env file
    echo "SECRET_KEY=$(python tools/generate_secret_key.py)" >> .env
"""
import secrets
import argparse
import sys


def generate_secret_key(length: int = 32) -> str:
    """
    Generate a cryptographically secure random secret key.

    Args:
        length: Number of bytes for the key (default: 32)

    Returns:
        URL-safe base64-encoded random string

    Note:
        Uses secrets module which is designed for generating
        cryptographically strong random data suitable for security/secrets.
    """
    if length < 16:
        raise ValueError("Key length should be at least 16 bytes for security")

    # Generate URL-safe base64-encoded random bytes
    # This is safe to use in URLs, file names, and most configuration formats
    return secrets.token_urlsafe(length)


def main():
    parser = argparse.ArgumentParser(
        description="Generate a secure SECRET_KEY for JWT authentication",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    parser.add_argument(
        "--length",
        "-l",
        type=int,
        default=32,
        help="Length of the key in bytes (default: 32, minimum: 16)"
    )

    parser.add_argument(
        "--multiple",
        "-m",
        type=int,
        default=1,
        help="Generate multiple keys (default: 1)"
    )

    parser.add_argument(
        "--format",
        "-f",
        choices=["plain", "env", "terraform"],
        default="plain",
        help="Output format (default: plain)"
    )

    args = parser.parse_args()

    # Validate length
    if args.length < 16:
        print("Error: Key length must be at least 16 bytes", file=sys.stderr)
        sys.exit(1)

    # Generate keys
    keys = [generate_secret_key(args.length) for _ in range(args.multiple)]

    # Output based on format
    if args.format == "plain":
        for key in keys:
            print(key)

    elif args.format == "env":
        for key in keys:
            print(f"SECRET_KEY={key}")

    elif args.format == "terraform":
        for key in keys:
            print(f'SECRET_KEY = "{key}"')

    return 0


if __name__ == "__main__":
    sys.exit(main())

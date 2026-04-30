#!/usr/bin/env python3
"""
Compute RIO (Relevé d'Identité Opérateur) from MSISDN.

Based on: Algorithme Inter-opérateurs de calcul du RIO v1.1

The RIO is composed of 4 fields separated by dashes:
    <operator>-<flag>-<client_ref>-<key>

Where:
    operator   : 2 alphanumeric characters (operator code)
    flag       : 1 alphanumeric character  (contract type)
    client_ref : 6 alphanumeric characters (simplified client reference)
    key        : 3 alphanumeric characters (computed checksum)

The key is computed using the following steps:
  1. Concatenate the 4 input fields (19 chars for mobile, 23 for M2M).
  2. Convert each character to its numeric value using the RIO alphabet:
         A=0, B=1, ..., Z=25, 0=26, 1=27, ..., 9=35
  3. Apply iterative operations for i = 1..N (N=19 or 23):
         Res1(i) = (    Res1(i-1) + Xi) % 37
         Res2(i) = (2 * Res2(i-1) + Xi) % 37
         Res3(i) = (4 * Res3(i-1) + Xi) % 37
     with Res1(0) = Res2(0) = Res3(0) = 0
  4. Convert the three final results back to characters using the same alphabet.

Example (from specification):
    operator=01, flag=P, client_ref=EROY4P, msisdn=0612345678
    key=4TR  →  RIO=01-P-EROY4P-4TR
"""

import argparse
import sys

# RIO alphabet: A-Z at positions 0-25, digits 0-9 at positions 26-35
_ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"

# Modulus used in the iterative algorithm
_MODULUS = 37


def _char_to_value(char: str) -> int:
    """Convert a single alphanumeric character to its RIO alphabet index."""
    c = char.upper()
    idx = _ALPHABET.find(c)
    if idx == -1:
        raise ValueError(f"Character '{char}' is not in the RIO alphabet ({_ALPHABET})")
    return idx


def _value_to_char(value: int) -> str:
    """Convert a numeric value (0-35) back to its RIO alphabet character."""
    if not (0 <= value < len(_ALPHABET)):
        raise ValueError(f"Value {value} is out of the RIO alphabet range (0-{len(_ALPHABET) - 1})")
    return _ALPHABET[value]


def compute_key(sequence: str) -> str:
    """
    Compute the 3-character RIO checksum key for the given concatenated sequence.

    Args:
        sequence: The concatenated operator+flag+client_ref+msisdn string
                  (19 chars for mobile, 23 chars for M2M).

    Returns:
        3-character key string.
    """
    values = [_char_to_value(c) for c in sequence]
    res1 = res2 = res3 = 0
    for x in values:
        res1 = (res1 + x) % _MODULUS
        res2 = (2 * res2 + x) % _MODULUS
        res3 = (4 * res3 + x) % _MODULUS
    return _value_to_char(res1) + _value_to_char(res2) + _value_to_char(res3)


def compute_rio(operator: str, flag: str, client_ref: str, msisdn: str) -> str:
    """
    Compute the full RIO string.

    Args:
        operator  : 2-character alphanumeric operator code.
        flag      : 1-character alphanumeric contract-type flag.
        client_ref: 6-character alphanumeric simplified client reference.
        msisdn    : 10-character (mobile) or 14-character (M2M) numeric phone number.
                    Spaces are stripped automatically.

    Returns:
        Full RIO string in the form ``<operator>-<flag>-<client_ref>-<key>``.

    Raises:
        ValueError: If any argument has an unexpected length or contains invalid characters.
    """
    operator = operator.upper().strip()
    flag = flag.upper().strip()
    client_ref = client_ref.upper().strip()
    msisdn = msisdn.replace(" ", "").strip()

    if len(operator) != 2:
        raise ValueError(f"operator must be 2 characters, got {len(operator)}: '{operator}'")
    if len(flag) != 1:
        raise ValueError(f"flag must be 1 character, got {len(flag)}: '{flag}'")
    if len(client_ref) != 6:
        raise ValueError(f"client_ref must be 6 characters, got {len(client_ref)}: '{client_ref}'")
    if len(msisdn) not in (10, 14):
        raise ValueError(f"msisdn must be 10 (mobile) or 14 (M2M) digits, got {len(msisdn)}: '{msisdn}'")
    if not msisdn.isdigit():
        raise ValueError(f"msisdn must contain only digits, got: '{msisdn}'")

    sequence = operator + flag + client_ref + msisdn
    key = compute_key(sequence)
    return f"{operator}-{flag}-{client_ref}-{key}"


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Compute the RIO (Relevé d'Identité Opérateur) from MSISDN.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Example:\n"
            "  %(prog)s --operator 01 --flag P --client-ref EROY4P --msisdn 0612345678\n"
            "  → 01-P-EROY4P-4TR"
        ),
    )
    parser.add_argument(
        "--operator",
        required=True,
        help="Operator code (2 alphanumeric characters).",
    )
    parser.add_argument(
        "--flag",
        required=True,
        help="Contract-type flag (1 alphanumeric character).",
    )
    parser.add_argument(
        "--client-ref",
        required=True,
        dest="client_ref",
        help="Simplified client reference (6 alphanumeric characters).",
    )
    parser.add_argument(
        "--msisdn",
        required=True,
        help="Phone number in MSISDN format (10 digits for mobile, 14 for M2M). Spaces are accepted.",
    )
    return parser


def main(argv=None):
    parser = _build_parser()
    args = parser.parse_args(argv)
    try:
        rio = compute_rio(args.operator, args.flag, args.client_ref, args.msisdn)
        print(rio)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

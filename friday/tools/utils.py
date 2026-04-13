"""
Utility tools — text processing, formatting, calculations, etc.
"""

import json
import uuid
import base64
import hashlib
import difflib

def register(mcp):

    @mcp.tool()
    def format_json(data: str) -> str:
        """Pretty-print a JSON string."""
        try:
            parsed = json.loads(data)
            return json.dumps(parsed, indent=2)
        except json.JSONDecodeError as e:
            return f"Invalid JSON: {e}"

    @mcp.tool()
    def word_count(text: str) -> dict:
        """Count words, characters, and lines in a block of text."""
        lines = text.splitlines()
        words = text.split()
        return {
            "characters": len(text),
            "words": len(words),
            "lines": len(lines),
        }

    @mcp.tool()
    def diff_texts(text1: str, text2: str) -> str:
        """Compares two strings and returns the differences."""
        lines1 = text1.splitlines(keepends=True)
        lines2 = text2.splitlines(keepends=True)
        diff = difflib.unified_diff(lines1, lines2, fromfile='text1', tofile='text2')
        return "".join(diff)

    @mcp.tool()
    def generate_uuid() -> str:
        """Generates a random UUID (v4)."""
        return str(uuid.uuid4())

    @mcp.tool()
    def encode_decode(text: str, operation: str = "encode", format: str = "base64") -> str:
        """Encodes or decodes text. Formats: base64."""
        try:
            if format == "base64":
                if operation == "encode":
                    return base64.b64encode(text.encode('utf-8')).decode('utf-8')
                elif operation == "decode":
                    return base64.b64decode(text.encode('utf-8')).decode('utf-8')
            return "Unsupported format or operation."
        except Exception as e:
            return f"Error: {e}"

    @mcp.tool()
    def hash_text(text: str, algorithm: str = "sha256") -> str:
        """Hashes text using md5, sha1, or sha256."""
        try:
            h = hashlib.new(algorithm)
            h.update(text.encode('utf-8'))
            return h.hexdigest()
        except Exception as e:
            return f"Error: {e}"

    @mcp.tool()
    def convert_units(value: float, from_unit: str, to_unit: str) -> str:
        """Converts units (Temperature: C/F, Data: B/KB/MB/GB, Length: m/km). Basic implementations."""
        # A simple implementation for the most common ones
        units = f"{from_unit.lower()}_{to_unit.lower()}"
        try:
            if units == "c_f": return f"{(value * 9/5) + 32:.2f} F"
            if units == "f_c": return f"{(value - 32) * 5/9:.2f} C"
            if units == "c_k": return f"{value + 273.15:.2f} K"
            
            # Data
            if units == "kb_mb": return f"{value / 1024:.2f} MB"
            if units == "mb_gb": return f"{value / 1024:.2f} GB"
            
            # Length
            if units == "m_km": return f"{value / 1000:.2f} km"
            if units == "km_m": return f"{value * 1000:.2f} m"
            if units == "m_cm": return f"{value * 100:.2f} cm"
            if units == "cm_m": return f"{value / 100:.2f} m"
            
            return f"{value} (Conversion {from_unit} to {to_unit} not implemented)"
        except Exception as e:
            return f"Error: {e}"

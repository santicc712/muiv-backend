import re
import os
import binascii


def generate(length: int = 16) -> str:
    result = binascii.b2a_hex(
        os.urandom(length)
    )

    result = re.findall(r"\w'(\w+)'", str(result))[0]
    return result[:length]

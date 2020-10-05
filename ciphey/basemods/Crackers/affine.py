# community
# by https://github.com/Ozzyz


from distutils import util
from typing import Optional, Dict, Union, Set, List
from loguru import logger

import ciphey
from ciphey.iface import ParamSpec, Cracker, CrackResult, CrackInfo, T, registry, Config
from ciphey.common import fix_case

import re
from math import gcd


@registry.register
class Affine(Cracker[str]):
    def getInfo(self, ctext: str) -> CrackInfo:
        return CrackInfo(
            success_likelihood=0.1,
            success_runtime=1e-5,
            failure_runtime=1e-5,
        )

    @staticmethod
    def getTarget() -> str:
        return "Affine"

    def attemptCrack(self, ctext: str) -> List[CrackResult]:
        """
        Brute forces all the possible combinations of a and b to attempt to crack the cipher.
        Each character in the Affine Cipher is encoded with the rule E(x) = (ax + b) mod m
        m is the size of the alphabet, while a and b are the keys in the cipher. a must be coprime to b.
        The Caesar cipher is a specific case of the Affine Cipher, with a=1 and b being the shift of the cipher.
        Decrypton is performed by D(x) = a_inv (x - b) mod m where a_inv is the modular multiplicative inverse of a mod m.
        """
        logger.trace("Attempting Affine brute force.")
        candidates = []

        # Convert the ctext to all-lowercase
        ctext = ctext.lower()

        # a and b are coprime if gcd(a,b) is 1.
        possible_a = [
            a
            for a in range(1, self.ALPHABET_LENGTH)
            if gcd(a, self.ALPHABET_LENGTH) == 1
        ]
        logger.debug(
            f"Trying Affine Cracker with {len(possible_a)} a-values and {self.ALPHABET_LENGTH} b-values"
        )
        for a in possible_a:
            for b in range(self.ALPHABET_LENGTH):
                translated = self.decrypt(ctext, a, b, self.ALPHABET_LENGTH)
                logger.trace(f"Transated text: {translated}")
                candidates.append(
                    CrackResult(
                        value=fix_case(translated, ctext), key_info=f"a: {a}, b: {b}"
                    )
                )
        logger.debug(f"Affine Cipher returned {len(candidates)} candidates")
        return candidates

    def decrypt(self, text: str, a: int, b: int, m: int) -> Optional[str]:
        """
        Each letter is decrypted at D(x) = a_inv (x - b) mod m where x is the char
        We treat the char value as its index in the alphabet, so if
        the alphabet is 'abcd....' and the char is 'b', it has the value 1.
        """
        a_inv = self.modInv(a, m)
        if a_inv is None:
            return None
        return "".join([self.decryptChar(char, a, b, m) for char in text])

    def decryptChar(self, char, a_inv, b, m):
        # Preserve characters that are not in alphabet
        if char not in self.group:
            return char
        char_idx = self.group.index(char)
        decrypted_char_idx = (a_inv * (char_idx - b)) % m
        return self.group[decrypted_char_idx]

    def modInv(self, a: int, m: int) -> int:
        for i in range(1, m):
            if (m * i + 1) % a == 0:
                return (m * i + 1) // a
        return None

    @staticmethod
    def getParams() -> Optional[Dict[str, ParamSpec]]:
        return {
            "group": ciphey.iface.ParamSpec(
                desc="An ordered sequence of chars that make up the alphabet",
                req=False,
                default="abcdefghijklmnopqrstuvwxyz",
            )
        }

    def __init__(self, config: Config):
        super().__init__(config)
        self.group = list(self._params()["group"])
        self.ALPHABET_LENGTH = len(self.group)
        self.cache = config.cache

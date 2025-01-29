import os
import oqs
from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes

class CryptographicFunctions: 

    def __init__(self):
        self.kem = oqs.KeyEncapsulation("Kyber1024")
        self.publickey = None # transmission
        self.privatekey = None
        self.ciphertext = None # transmission
        self.payload = None
        self.plaintext = None
        self.shared_secret_key = None
        self.transmission_key = None # transmission
        self.tag = None # transmission
        self.mainkey = None

    def generate_key_pairs(self):

        """
        Generate the public, private key pair.

        Args:
            self:
        """

        self.publickey = self.kem.generate_keypair()
        self.privatekey = self.kem.export_secret_key()

    def key_generation(self, receiver_public_key):
        """
        Generate the transmission key and shared secret using the receiver's public key.

        Args:
            receiver_public_key: The public key of the receiver (Bob).
        """
        self.transmission_key, self.shared_secret_key = self.kem.encap_secret(receiver_public_key)
        self.tag = os.urandom(12)

    def key_prep(self):

        """
        Prepares the actual key for encrpytion and decrption converting key size compatable to ChaCha20-Poly1305

        Args: 
            self: 
        
        """

        hkdf = HKDF(
            algorithm=hashes.SHA256(),
            length=32,  # ChaCha20-Poly1305 requires a 256-bit key
            salt=None,  # Optionally, use a secure salt,
            info=b''  # Explicitly set info to an empty bytes object
        )
        return hkdf.derive(self.shared_secret_key)


    def encrypt_msg(self):

        """
        Encrypts the message using the main key derived from the shared secret key

        Args: 
            self:
        """

        # if self.encryption_key is None:
        #     raise ValueError("Encryption key has not been derived yet.")
        self.mainkey = self.key_prep()
        chacha = ChaCha20Poly1305(self.mainkey)
        self.ciphertext = chacha.encrypt(self.tag, self.payload.encode(), None)

    def decryption_message(self, ciphertext, transmission_key, tag):
        # recieves private key, performs key computation

        """
        Decrypts the message using the transmission key
        
        Args: 
            ciphertext: text which is obtained after the stegnographic decoding
            transmission_key: key transmitted to the reciever to generate shared secret key
            tag: nonce value to check authenticity and integrity

        """

        shared_secret_key = self.kem.decap_secret(transmission_key)
        mainkey = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=None,
            info=b''  # Explicitly set info to an empty bytes object
        ).derive(shared_secret_key)

        chacha = ChaCha20Poly1305(mainkey)

        try:
            plaintext = chacha.decrypt(tag, ciphertext, None)
            return plaintext.decode()
        except Exception as e:
            return f"Decryption failed (authenticity/integrity check failed): {str(e)}"
        
        
    


import os
import steganographic as stegano
from cryptographic import CryptographicFunctions
import datetime
import json
import time
import base64


class Engine:

    def __init__(self):
    
        # DS
        self.crypto = CryptographicFunctions()
        self.crypto.generate_key_pairs()
        self.key_received = None # recieved transmission key
        self.received_tag = None # tag from the reciever
        self.public_key_received = None # public key of reciever
        self.output_path = None
        self.transmission_key = None # key to send to receiver
        self.transmission_tag = None # tag to send to receiver


    def hide_data(self, payload_data:str, image_path:str, receiver_public_key) -> str:


        # print(self.crypto.privatekey)

        #1. Encrypt the data
        self.crypto.key_generation(receiver_public_key)
        self.crypto.payload = payload_data
        self.crypto.encrypt_msg()

        #2. Embed the encrypted data.
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        base_dir="stegnographic_images"
        if not os.path.exists(base_dir):
            os.makedirs(base_dir)
        # Append the timestamp to the file name
        timestamped_file_name = f"{timestamp}_stegano_image.png"
        stegano.embed_data_adaptive(image_path, self.crypto.ciphertext, timestamped_file_name)


        print(f"ciphertext: {self.crypto.ciphertext}, tag: {self.crypto.tag}, transmission_key: {self.crypto.transmission_key}")
        return timestamped_file_name, self.crypto.transmission_key, self.crypto.tag


    def extract_data(self, stego_image_path:str) -> str:

        
        data = {}
        with open("received_files/key.json", "r", encoding="utf-8") as file:
            data = json.load(file)  

        transmission_key = base64.b64decode(data["transmission_key"])
        tag = base64.b64decode(data["tag"])

        self.key_received, self.received_tag = transmission_key, tag

        #1. Decode the image for encrpyted data.
        time.sleep(15)
        self.crypto.ciphertext = stegano.extract_data_adaptive(stego_image_path)

        print(f"ciphertext: {self.crypto.ciphertext}, tag: {self.received_tag}, transmission_key: {self.key_received}")

        #2. Decrypt the extracted data.
        self.crypto.plaintext = self.crypto.decryption_message(self.crypto.ciphertext, self.key_received, self.received_tag)
        print(self.crypto.plaintext)




        # return self.crypto.plaintext






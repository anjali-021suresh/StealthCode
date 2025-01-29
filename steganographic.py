import cv2
import numpy as np


def calculate_edge_strength(image_array:np):
    """
    Calculate edge strength using a Sobel filter.

    Args: 
        image_array: numpy array of the image.
    """
    gradient_x = cv2.Sobel(image_array, cv2.CV_64F, 1, 0, ksize=3)
    gradient_y = cv2.Sobel(image_array, cv2.CV_64F, 0, 1, ksize=3)
    return np.sqrt(gradient_x**2 + gradient_y**2)


def embed_data_adaptive(image_path:str, encrypted_message:bytes, output_path:str):
    """
    Embed secret data in a color image using Adaptive LSB Steganography.
    
    Args:
        image_path: path of the image where data to be embedded.
        encrypted_message: the message to be embedded.
        output_path: image path where to save the image.


    """
    # Load image in RGB (BGR in OpenCV)
    image = cv2.imread(image_path)
    if image is None:
        # Handle a function of message box here.
        raise ValueError("Image not found or format not supported.")

    # Split image into channels (B, G, R)
    b_channel, g_channel, r_channel = cv2.split(image)

    # Calculate edge strength for each channel
    edge_strength_b = calculate_edge_strength(b_channel)
    edge_strength_g = calculate_edge_strength(g_channel)
    edge_strength_r = calculate_edge_strength(r_channel)

    # Combine edge strengths and normalize to adaptive levels
    combined_edge_strength = (edge_strength_b + edge_strength_g + edge_strength_r) / 3
    adaptive_levels = np.clip((combined_edge_strength / np.max(combined_edge_strength) * 3).astype(int), 1, 3)

    # Convert secret data to binary
    secret_binary = ''.join(format(byte, '08b') for byte in encrypted_message) + '11111111'  # Unique delimiter
    if len(secret_binary) > image.size * 3:
        # Handle a function of message box here.
        raise ValueError("Image not found or format not supported.")


    # Embed data in all channels (cycling through B, G, R)
    secret_index = 0
    channels = [b_channel, g_channel, r_channel]
    for i in range(image.shape[0]):
        for j in range(image.shape[1]):
            if secret_index >= len(secret_binary):
                break

            for channel_index, channel in enumerate(channels):
                if secret_index >= len(secret_binary):
                    break

                # Get adaptive level for the current pixel
                adaptive_level = adaptive_levels[i, j]

                # Modify pixel value
                pixel_value = int(channel[i, j])  # Start with the current channel
                for bit_position in range(adaptive_level):
                    if secret_index >= len(secret_binary):
                        break
                    pixel_value = (pixel_value & ~(1 << bit_position)) | (int(secret_binary[secret_index]) << bit_position)
                    secret_index += 1

                channel[i, j] = np.uint8(np.clip(pixel_value, 0, 255))

    # Merge channels back into an RGB image
    stego_image = cv2.merge((b_channel, g_channel, r_channel))

    # Save the stego image
    cv2.imwrite(output_path, stego_image)
    print(f"Data embedded successfully in {output_path}")


def extract_data_adaptive(stego_image_path:str):
    """
    Extract secret data from a color stego image.
    Args:
        stego_image_path: saved image path.
    """
    # Load stego image in RGB (BGR in OpenCV)
    image = cv2.imread(stego_image_path)
    if image is None:
        # Handle a function of message box here.
        raise ValueError("Image not found or format not supported.")

    # Extract channels
    b_channel, g_channel, r_channel = cv2.split(image)

    # Calculate edge strength for combined channels
    edge_strength_b = calculate_edge_strength(b_channel)
    edge_strength_g = calculate_edge_strength(g_channel)
    edge_strength_r = calculate_edge_strength(r_channel)
    combined_edge_strength = (edge_strength_b + edge_strength_g + edge_strength_r) / 3

    # Normalize edge strength to adaptive levels
    adaptive_levels = np.clip((combined_edge_strength / np.max(combined_edge_strength) * 3).astype(int), 1, 3)

    # Extract binary data
    secret_binary = ''
    channels = [b_channel, g_channel, r_channel]
    for i in range(b_channel.shape[0]):
        for j in range(b_channel.shape[1]):
            for channel in channels:
                pixel_value = channel[i, j]
                adaptive_level = adaptive_levels[i, j]

                for bit_position in range(adaptive_level):
                    secret_binary += str((pixel_value >> bit_position) & 1)

    # Convert binary to bytes
    byte_array = bytearray()
    for i in range(0, len(secret_binary), 8):
        byte = secret_binary[i:i+8]
        if byte == '11111111':  # Unique delimiter
            break
        byte_array.append(int(byte, 2))

    if not byte_array:
        # Handle a function of message box here.
        raise ValueError("Image not found or format not supported.")

    return bytes(byte_array)


# Example Workflow
# embed_data_adaptive(
#     "/home/abhipnair/abhipnair@pikachu/Projects.abhipnair@pikachu/StealthCode/StealthCode/123.png",
#     b'\x19\x8b\n2\xaf\xc6e\xf9\xcfSO\xf6\xe8]\xe58\xbdZ\xa5\xef\xf8\xc4\x16Z\x05\xc8\xdd\xfa',
#     "stegoimage.png"
# )



# extracted_data = extract_data_adaptive("stegoimage.png")
# if extracted_data:
#     print("Extracted Data:", extracted_data)
#     if b'\x19\x8b\n2\xaf\xc6e\xf9\xcfSO\xf6\xe8]\xe58\xbdZ\xa5\xef\xf8\xc4\x16Z\x05\xc8\xdd\xfa' == extracted_data:
#         print("hello")


# Differences and Robustness Metrics
# calculate_difference("/home/abhipnair/Mini_Project/123.png", "stegoimage.png")
# calculate_difference_percentage("/home/abhipnair/Mini_Project/123.png", "stegoimage.png")
# calculate_psnr("/home/abhipnair/Mini_Project/123.png", "stegoimage.png")
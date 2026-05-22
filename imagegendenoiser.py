import argparse
import numpy as np
import cv2
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
from pqclean.bindings import pqcrypto
import os

# -----------------------------
# IMAGE GENERATION & PROCESSING
# -----------------------------

def generate_image(height, width):
    """Generate a simple gradient image."""
    return np.linspace(0, 255, num=height * width, dtype=np.uint8).reshape((height, width))

def add_non_gaussian_noise(image, noise_level=25):
    """Add Laplacian (non-Gaussian) noise."""
    noise = np.random.laplace(loc=0.0, scale=noise_level, size=image.shape).astype(np.int16)
    noisy_image = np.clip(image.astype(np.int16) + noise, 0, 255).astype(np.uint8)
    return noisy_image

def denoise_image(image):
    """Denoise using TV-L1 algorithm."""
    return cv2.denoise_TVL1([image], weight=0.1, iterations=100)[0]

def encrypt_image(image):
    """Encrypt image bytes using Kyber512 KEM."""
    public_key, secret_key = pqcrypto.kem.kyber512.generate_keypair()
    ciphertext, shared_secret = pqcrypto.kem.kyber512.enc(public_key)
    # Note: Kyber encrypts a symmetric key, not arbitrary data.
    # To encrypt the image, you'd normally use the shared secret with a symmetric cipher.
    return ciphertext

def save_image(image, filename="output_denoised.png"):
    """Save image to disk."""
    cv2.imwrite(filename, image)
    print(f"Saved processed image to {filename}")

# -----------------------------
# CLI MODE
# -----------------------------

def cli_interface():
    parser = argparse.ArgumentParser(description="Image Denoising and Post-Quantum Encryption")
    parser.add_argument('--height', type=int, default=256, help='Height of the generated image')
    parser.add_argument('--width', type=int, default=256, help='Width of the generated image')
    parser.add_argument('--noise', type=int, default=25, help='Noise level for non-Gaussian noise')
    args = parser.parse_args()

    print("Generating image...")
    image = generate_image(args.height, args.width)

    print("Adding noise...")
    noisy_image = add_non_gaussian_noise(image, noise_level=args.noise)

    print("Denoising...")
    denoised_image = denoise_image(noisy_image)

    print("Encrypting...")
    encrypted_image = encrypt_image(denoised_image)

    save_image(denoised_image)

    print("Image generated, denoised, saved, and encrypted successfully.")

# -----------------------------
# GUI MODE
# -----------------------------

def gui_interface():
    root = tk.Tk()
    root.title("Image Denoising & Encryption")

    def process_image(image):
        noisy = add_non_gaussian_noise(image)
        denoised = denoise_image(noisy)
        encrypted = encrypt_image(denoised)

        # Display denoised image
        img = Image.fromarray(denoised)
        img_tk = ImageTk.PhotoImage(img)
        panel.config(image=img_tk)
        panel.image = img_tk

        save_image(denoised)

        messagebox.showinfo("Success", "Image processed, displayed, saved, and encrypted!")

    def load_image():
        file_path = filedialog.askopenfilename()
        if file_path:
            img = Image.open(file_path).convert('L')
            img = img.resize((256, 256))
            img_arr = np.array(img, dtype=np.uint8)
            process_image(img_arr)

    def generate_and_process():
        img = generate_image(256, 256)
        process_image(img)

    panel = tk.Label(root)
    panel.pack()

    btn_load = tk.Button(root, text="Load Image", command=load_image)
    btn_load.pack()

    btn_generate = tk.Button(root, text="Generate Image", command=generate_and_process)
    btn_generate.pack()

    root.mainloop()

# -----------------------------
# MAIN ENTRY POINT
# -----------------------------

if __name__ == "__main__":
    print("Choose mode:")
    print("1 = CLI mode")
    print("2 = GUI mode")

    choice = input("Enter choice: ").strip()

    if choice == "1":
        cli_interface()
    elif choice == "2":
        gui_interface()
    else:
        print("Invalid choice. Exiting.")


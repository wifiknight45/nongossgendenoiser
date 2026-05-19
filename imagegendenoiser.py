import argparse
import numpy as np
import cv2
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
from pqclean.bindings import pqcrypto

def generate_image(height, width):
    return np.linspace(0, 255, num=height*width, dtype=np.uint8).reshape((height, width))

def add_non_gaussian_noise(image, noise_level=25):
    noise = np.random.laplace(loc=0.0, scale=noise_level, size=image.shape).astype(np.int8)
    noisy_image = cv2.add(image, noise, dtype=cv2.CV_8U)
    return noisy_image

def denoise_image(image):
    return cv2.denoise_TVL1([image], weight=0.1, iterations=100)[0]

def encrypt_image(image):
    height, width = image.shape
    public_key, secret_key = pqcrypto.kem.kyber512.generate_keypair()
    ciphertext, _ = pqcrypto.kem.kyber512.enc(public_key, image.tobytes())
    return ciphertext

def cli_interface():
    parser = argparse.ArgumentParser(description="Image Denoising and Post-Quantum Encryption")
    parser.add_argument('--height', type=int, default=256, help='Height of the generated image')
    parser.add_argument('--width', type=int, default=256, help='Width of the generated image')
    parser.add_argument('--noise', type=int, default=25, help='Noise level for non-Gaussian noise')
    args = parser.parse_args()

    image = generate_image(args.height, args.width)
    noisy_image = add_non_gaussian_noise(image, noise_level=args.noise)
    denoised_image = denoise_image(noisy_image)
    encrypted_image = encrypt_image(denoised_image)

    print("Image generated, denoised, and encrypted successfully.")
    # You could save the image or ciphertext to a file here as needed.

def gui_interface():
    root = tk.Tk()
    root.title("Image Denoising & Encryption")

    def load_image():
        file_path = filedialog.askopenfilename()
        if file_path:
            img = Image.open(file_path).convert('L')  # Convert to grayscale
            img = img.resize((256, 256))  # Resize for simplicity
            img_arr = np.array(img, dtype=np.uint8)
            process_image(img_arr)

    def process_image(image):
        noisy = add_non_gaussian_noise(image)
        denoised = denoise_image(noisy)
        encrypted = encrypt_image(denoised)
        
        # Display the denoised image for visualization
        img = Image.fromarray(denoised)
        img_tk = ImageTk.PhotoImage(img)
        panel.config(image=img_tk)
        panel.image = img_tk

        messagebox.showinfo("Success", "Image processed and encrypted!")

    panel = tk.Label(root)
    panel.pack()

    btn_load = tk.Button(root, text="Load Image", command=load_image)
    btn_load.pack()

    root.mainloop()

if __name__ == "__main__":
    print("Choose mode: 1 for

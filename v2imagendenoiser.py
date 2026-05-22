#!/usr/bin/env python3
import argparse
import os
import threading
import time
import signal
import sys

import numpy as np
import cv2
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk
from pqclean.bindings import pqcrypto
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

# -----------------------------
# IMAGE GENERATION & PROCESSING
# -----------------------------

def generate_image(height, width):
    """Generate a gradient test image"""
    return np.linspace(0, 255, num=height * width, dtype=np.uint8).reshape((height, width))

def add_non_gaussian_noise(image, noise_level=25):
    """Add Laplacian (non-Gaussian) noise to the image"""
    noise = np.random.laplace(loc=0.0, scale=noise_level, size=image.shape).astype(np.int16)
    noisy_image = np.clip(image.astype(np.int16) + noise, 0, 255).astype(np.uint8)
    return noisy_image

def denoise_image(image):
    """Denoise image using Total Variation L1 denoising"""
    return cv2.denoise_TVL1([image], weight=0.1, iterations=100)[0]

def calculate_metrics(original, noisy, denoised):
    """Calculate PSNR and MSE metrics for image quality assessment"""
    mse_noisy = np.mean((original.astype(float) - noisy.astype(float)) ** 2)
    psnr_noisy = 10 * np.log10(255**2 / mse_noisy) if mse_noisy > 0 else float('inf')
    mse_denoised = np.mean((original.astype(float) - denoised.astype(float)) ** 2)
    psnr_denoised = 10 * np.log10(255**2 / mse_denoised) if mse_denoised > 0 else float('inf')
    return {
        'mse_noisy': mse_noisy,
        'psnr_noisy': psnr_noisy,
        'mse_denoised': mse_denoised,
        'psnr_denoised': psnr_denoised
    }

def encrypt_image(image):
    """Encrypt image using post-quantum Kyber512 KEM (placeholder)"""
    # Kyber KEM typically encapsulates a shared secret; here we call encapsulate for demonstration
    public_key, secret_key = pqcrypto.kem.kyber512.generate_keypair()
    ciphertext, _ = pqcrypto.kem.kyber512.encapsulate(public_key)
    return ciphertext, len(ciphertext)

def save_image(image, out_dir, prefix, iteration):
    """Save image to disk as PNG"""
    if not out_dir:
        return None
    os.makedirs(out_dir, exist_ok=True)
    filename = os.path.join(out_dir, f"{prefix}_iter{iteration:05d}.png")
    cv2.imwrite(filename, image)
    return filename

def create_comparison_plot(original, noisy, denoised, metrics):
    """Create a comprehensive comparison visualization"""
    fig = Figure(figsize=(14, 10))
    ax1 = fig.add_subplot(3, 3, 1)
    ax1.imshow(original, cmap='gray', vmin=0, vmax=255)
    ax1.set_title('Original Image', fontsize=10, fontweight='bold')
    ax1.axis('off')

    ax2 = fig.add_subplot(3, 3, 2)
    ax2.imshow(noisy, cmap='gray', vmin=0, vmax=255)
    ax2.set_title(f'Noisy Image\nPSNR: {metrics["psnr_noisy"]:.2f} dB', fontsize=10, fontweight='bold')
    ax2.axis('off')

    ax3 = fig.add_subplot(3, 3, 3)
    ax3.imshow(denoised, cmap='gray', vmin=0, vmax=255)
    ax3.set_title(f'Denoised Image\nPSNR: {metrics["psnr_denoised"]:.2f} dB', fontsize=10, fontweight='bold')
    ax3.axis('off')

    ax4 = fig.add_subplot(3, 3, 4)
    noise_diff = np.abs(original.astype(float) - noisy.astype(float))
    im4 = ax4.imshow(noise_diff, cmap='hot', vmin=0, vmax=100)
    ax4.set_title('Noise Pattern\n(Original - Noisy)', fontsize=9)
    ax4.axis('off')
    plt.colorbar(im4, ax=ax4, fraction=0.046)

    ax5 = fig.add_subplot(3, 3, 5)
    denoised_diff = np.abs(original.astype(float) - denoised.astype(float))
    im5 = ax5.imshow(denoised_diff, cmap='hot', vmin=0, vmax=100)
    ax5.set_title('Residual Error\n(Original - Denoised)', fontsize=9)
    ax5.axis('off')
    plt.colorbar(im5, ax=ax5, fraction=0.046)

    ax6 = fig.add_subplot(3, 3, 6)
    improvement = noise_diff - denoised_diff
    im6 = ax6.imshow(improvement, cmap='RdYlGn', vmin=-50, vmax=50)
    ax6.set_title('Denoising Improvement\n(Green = Better)', fontsize=9)
    ax6.axis('off')
    plt.colorbar(im6, ax=ax6, fraction=0.046)

    ax7 = fig.add_subplot(3, 3, 7)
    ax7.hist(original.ravel(), bins=50, alpha=0.7, label='Original', color='blue', density=True)
    ax7.hist(noisy.ravel(), bins=50, alpha=0.5, label='Noisy', color='red', density=True)
    ax7.set_title('Pixel Distribution\n(Original vs Noisy)', fontsize=9)
    ax7.set_xlabel('Pixel Intensity')
    ax7.set_ylabel('Density')
    ax7.legend(fontsize=8)
    ax7.grid(alpha=0.3)

    ax8 = fig.add_subplot(3, 3, 8)
    ax8.hist(original.ravel(), bins=50, alpha=0.7, label='Original', color='blue', density=True)
    ax8.hist(denoised.ravel(), bins=50, alpha=0.5, label='Denoised', color='green', density=True)
    ax8.set_title('Pixel Distribution\n(Original vs Denoised)', fontsize=9)
    ax8.set_xlabel('Pixel Intensity')
    ax8.set_ylabel('Density')
    ax8.legend(fontsize=8)
    ax8.grid(alpha=0.3)

    ax9 = fig.add_subplot(3, 3, 9)
    ax9.axis('off')
    metrics_text = f"""
Quality Metrics:

Noisy Image:
• MSE: {metrics['mse_noisy']:.2f}
• PSNR: {metrics['psnr_noisy']:.2f} dB

Denoised Image:
• MSE: {metrics['mse_denoised']:.2f}
• PSNR: {metrics['psnr_denoised']:.2f} dB

Improvement:
• ΔPSNR: {metrics['psnr_denoised'] - metrics['psnr_noisy']:.2f} dB
• Noise Reduction: {(1 - metrics['mse_denoised']/metrics['mse_noisy'])*100:.1f}%
"""
    ax9.text(0.05, 0.5, metrics_text, fontsize=9, verticalalignment='center',
             family='monospace', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.3))

    fig.tight_layout()
    return fig

# -----------------------------
# CLI MODE (with continuous)
# -----------------------------

_stop_cli = False

def _signal_handler(sig, frame):
    global _stop_cli
    _stop_cli = True
    print("\nStopping continuous CLI loop...")

signal.signal(signal.SIGINT, _signal_handler)

def cli_interface():
    """Command-line interface for image processing with optional continuous mode"""
    parser = argparse.ArgumentParser(description="Image Denoising and Post-Quantum Encryption")
    parser.add_argument('--height', type=int, default=256, help='Height of the generated image')
    parser.add_argument('--width', type=int, default=256, help='Width of the generated image')
    parser.add_argument('--noise', type=int, default=25, help='Noise level for non-Gaussian noise')
    parser.add_argument('--visualize', action='store_true', help='Show visualization plots')
    parser.add_argument('--continuous', action='store_true', help='Run continuous generation until Ctrl+C')
    parser.add_argument('--save-dir', type=str, default=None, help='Directory to save per-iteration images')
    args = parser.parse_args()

    iteration = 0
    try:
        while True:
            iteration += 1
            print(f"\nIteration {iteration} - Generating image...")
            image = generate_image(args.height, args.width)

            noisy_image = add_non_gaussian_noise(image, noise_level=args.noise)
            denoised_image = denoise_image(noisy_image)
            metrics = calculate_metrics(image, noisy_image, denoised_image)

            print("="*40)
            print(f"Iteration {iteration} Results")
            print("="*40)
            print(f"Noise Level: {args.noise}")
            print(f"Noisy MSE: {metrics['mse_noisy']:.2f}  PSNR: {metrics['psnr_noisy']:.2f} dB")
            print(f"Denoised MSE: {metrics['mse_denoised']:.2f}  PSNR: {metrics['psnr_denoised']:.2f} dB")
            print(f"ΔPSNR: {metrics['psnr_denoised'] - metrics['psnr_noisy']:.2f} dB")

            encrypted_image, cipher_size = encrypt_image(denoised_image)
            print(f"Encrypted ciphertext size: {cipher_size} bytes")

            saved_path = None
            if args.save_dir:
                saved_path = save_image(denoised_image, args.save_dir, "denoised", iteration)
                print(f"Saved denoised image to: {saved_path}")

            if args.visualize:
                fig = create_comparison_plot(image, noisy_image, denoised_image, metrics)
                plt.show(block=False)
                plt.pause(0.001)
                plt.show()

            if not args.continuous:
                break

            if _stop_cli:
                break

            # small sleep to avoid hogging CPU; adjust as needed
            time.sleep(0.2)

    except KeyboardInterrupt:
        print("\nInterrupted by user. Exiting CLI loop.")
    except Exception as e:
        print(f"\nError in CLI loop: {e}")
    finally:
        print("CLI mode finished.")

# -----------------------------
# GUI MODE (with continuous)
# -----------------------------

class GUIApp:
    def __init__(self, root):
        self.root = root
        root.title("Image Denoising & Post-Quantum Encryption (Continuous Mode)")
        root.geometry("1200x800")

        self.current_images = {}
        self.canvas = None
        self.fig_canvas = None
        self.continuous_running = False
        self.iteration = 0
        self.save_dir = None

        main_frame = ttk.Frame(root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        control_frame = ttk.LabelFrame(main_frame, text="Controls", padding=10)
        control_frame.pack(side=tk.TOP, fill=tk.X, pady=(0, 10))

        noise_frame = ttk.Frame(control_frame)
        noise_frame.pack(side=tk.LEFT, padx=10)
        ttk.Label(noise_frame, text="Noise Level:").pack(side=tk.LEFT)
        self.noise_var = tk.IntVar(value=25)
        noise_slider = ttk.Scale(noise_frame, from_=5, to=100, variable=self.noise_var, orient=tk.HORIZONTAL, length=200)
        noise_slider.pack(side=tk.LEFT, padx=5)
        self.noise_label = ttk.Label(noise_frame, text="25")
        self.noise_label.pack(side=tk.LEFT)
        noise_slider.config(command=self.update_noise_label)

        button_frame = ttk.Frame(control_frame)
        button_frame.pack(side=tk.LEFT, padx=20)

        self.status_var = tk.StringVar(value="Ready")
        status_label = ttk.Label(control_frame, textvariable=self.status_var, foreground="blue")
        status_label.pack(side=tk.RIGHT, padx=10)

        # Buttons
        btn_load = ttk.Button(button_frame, text="Load Image", command=self.load_image)
        btn_load.pack(side=tk.LEFT, padx=5)

        btn_generate = ttk.Button(button_frame, text="Generate Test Image", command=self.generate_test_image)
        btn_generate.pack(side=tk.LEFT, padx=5)

        btn_reprocess = ttk.Button(button_frame, text="Reprocess", command=self.reprocess)
        btn_reprocess.pack(side=tk.LEFT, padx=5)

        # Continuous controls
        cont_frame = ttk.Frame(control_frame)
        cont_frame.pack(side=tk.LEFT, padx=10)
        self.btn_start = ttk.Button(cont_frame, text="Start Continuous", command=self.start_continuous)
        self.btn_start.pack(side=tk.LEFT, padx=5)
        self.btn_stop = ttk.Button(cont_frame, text="Stop", command=self.stop_continuous, state=tk.DISABLED)
        self.btn_stop.pack(side=tk.LEFT, padx=5)

        # Save options
        save_frame = ttk.Frame(control_frame)
        save_frame.pack(side=tk.LEFT, padx=10)
        self.save_var = tk.BooleanVar(value=False)
        chk_save = ttk.Checkbutton(save_frame, text="Auto Save", variable=self.save_var, command=self.toggle_save)
        chk_save.pack(side=tk.LEFT)
        btn_choose_dir = ttk.Button(save_frame, text="Choose Save Dir", command=self.choose_save_dir)
        btn_choose_dir.pack(side=tk.LEFT, padx=5)

        # Canvas for matplotlib figure
        self.canvas_frame = ttk.Frame(main_frame)
        self.canvas_frame.pack(fill=tk.BOTH, expand=True)

        welcome_label = ttk.Label(self.canvas_frame, text="Load an image or generate a test image to begin",
                                  font=('Arial', 14), foreground='gray')
        welcome_label.pack(expand=True)

    def update_noise_label(self, val):
        self.noise_label.config(text=f"{int(float(val))}")

    def choose_save_dir(self):
        d = filedialog.askdirectory()
        if d:
            self.save_dir = d
            self.status_var.set(f"Save dir: {d}")

    def toggle_save(self):
        if self.save_var.get() and not self.save_dir:
            self.choose_save_dir()

    def load_image(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.bmp *.tiff"), ("All files", "*.*")]
        )
        if file_path:
            self.status_var.set("Loading image...")
            self.root.update()
            img = Image.open(file_path).convert('L')
            img = img.resize((256, 256))
            img_arr = np.array(img, dtype=np.uint8)
            self.current_images['original'] = img_arr
            self.process_image(img_arr)

    def generate_test_image(self):
        self.status_var.set("Generating test image...")
        self.root.update()
        img_arr = generate_image(256, 256)
        self.current_images['original'] = img_arr
        self.process_image(img_arr)

    def reprocess(self):
        if 'original' in self.current_images:
            self.process_image(self.current_images['original'])

    def process_image(self, image):
        self.status_var.set("Adding noise...")
        self.root.update()
        noisy = add_non_gaussian_noise(image, noise_level=self.noise_var.get())
        self.current_images['noisy'] = noisy

        self.status_var.set("Denoising image...")
        self.root.update()
        denoised = denoise_image(noisy)
        self.current_images['denoised'] = denoised

        self.status_var.set("Calculating metrics...")
        self.root.update()
        metrics = calculate_metrics(image, noisy, denoised)

        self.status_var.set("Encrypting image...")
        self.root.update()
        encrypted, cipher_size = encrypt_image(denoised)

        # Save if requested
        saved_path = None
        if self.save_var.get() and self.save_dir:
            self.iteration += 1
            saved_path = save_image(denoised, self.save_dir, "denoised", self.iteration)

        # Update visualization
        for widget in self.canvas_frame.winfo_children():
            widget.destroy()

        fig = create_comparison_plot(image, noisy, denoised, metrics)
        self.fig_canvas = FigureCanvasTkAgg(fig, master=self.canvas_frame)
        self.fig_canvas.draw()
        self.fig_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        status_text = f"Iter: {self.iteration} | Cipher: {cipher_size} bytes | ΔPSNR: {metrics['psnr_denoised'] - metrics['psnr_noisy']:.2f} dB"
        if saved_path:
            status_text += f" | Saved: {os.path.basename(saved_path)}"
        self.status_var.set(status_text)

    # Continuous loop using tkinter .after() to remain responsive
    def _continuous_step(self):
        if not self.continuous_running:
            return
        try:
            # If no original image loaded, generate one each iteration
            img = self.current_images.get('original', generate_image(256, 256))
            self.iteration += 1
            noisy = add_non_gaussian_noise(img, noise_level=self.noise_var.get())
            denoised = denoise_image(noisy)
            metrics = calculate_metrics(img, noisy, denoised)
            encrypted, cipher_size = encrypt_image(denoised)
            if self.save_var.get() and self.save_dir:
                save_image(denoised, self.save_dir, "denoised", self.iteration)
            # Update visualization
            for widget in self.canvas_frame.winfo_children():
                widget.destroy()
            fig = create_comparison_plot(img, noisy, denoised, metrics)
            self.fig_canvas = FigureCanvasTkAgg(fig, master=self.canvas_frame)
            self.fig_canvas.draw()
            self.fig_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
            self.status_var.set(f"Iter: {self.iteration} | Cipher: {cipher_size} bytes | ΔPSNR: {metrics['psnr_denoised'] - metrics['psnr_noisy']:.2f} dB")
        except Exception as e:
            self.status_var.set(f"Error during continuous step: {e}")
            self.stop_continuous()
            return
        # Schedule next iteration; adjust delay_ms for speed
        delay_ms = 200
        self.root.after(delay_ms, self._continuous_step)

    def start_continuous(self):
        if self.continuous_running:
            return
        self.continuous_running = True
        self.btn_start.config(state=tk.DISABLED)
        self.btn_stop.config(state=tk.NORMAL)
        self.status_var.set("Continuous generation started")
        # Kick off the loop
        self.root.after(10, self._continuous_step)

    def stop_continuous(self):
        if not self.continuous_running:
            return
        self.continuous_running = False
        self.btn_start.config(state=tk.NORMAL)
        self.btn_stop.config(state=tk.DISABLED)
        self.status_var.set("Continuous generation stopped")

def gui_interface():
    root = tk.Tk()
    app = GUIApp(root)
    root.mainloop()

# -----------------------------
# MAIN ENTRY POINT
# -----------------------------

if __name__ == "__main__":
    print("="*60)
    print("Image Denoising & Post-Quantum Encryption Tool (with Continuous Modes)")
    print("="*60)
    print("\nChoose mode:")
    print("1 - GUI Mode (Interactive with visualizations and Start/Stop continuous)")
    print("2 - CLI Mode (Command line with optional continuous loop)")
    print("="*60)

    try:
        choice = input("\nEnter choice (1 or 2): ").strip()
        if choice == "1":
            gui_interface()
        elif choice == "2":
            cli_interface()
        else:
            print("Invalid choice. Defaulting to GUI mode...")
            gui_interface()
    except KeyboardInterrupt:
        print("\nExiting...")
    except Exception as e:
        print(f"\nError: {e}")
        print("Falling back to GUI mode...")
        try:
            gui_interface()
        except Exception:
            print("Unable to launch GUI. Exiting.")
            sys.exit(1)

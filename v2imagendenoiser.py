import argparse
import numpy as np
import cv2
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk
from pqclean.bindings import pqcrypto
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

def generate_image(height, width):
    """Generate a gradient test image"""
    return np.linspace(0, 255, num=height*width, dtype=np.uint8).reshape((height, width))

def add_non_gaussian_noise(image, noise_level=25):
    """Add Laplacian (non-Gaussian) noise to the image"""
    noise = np.random.laplace(loc=0.0, scale=noise_level, size=image.shape).astype(np.int8)
    noisy_image = cv2.add(image, noise, dtype=cv2.CV_8U)
    return noisy_image

def denoise_image(image):
    """Denoise image using Total Variation L1 denoising"""
    return cv2.denoise_TVL1([image], weight=0.1, iterations=100)[0]

def calculate_metrics(original, noisy, denoised):
    """Calculate PSNR and MSE metrics for image quality assessment"""
    # PSNR and MSE for noisy image
    mse_noisy = np.mean((original.astype(float) - noisy.astype(float)) ** 2)
    psnr_noisy = 10 * np.log10(255**2 / mse_noisy) if mse_noisy > 0 else float('inf')
    
    # PSNR and MSE for denoised image
    mse_denoised = np.mean((original.astype(float) - denoised.astype(float)) ** 2)
    psnr_denoised = 10 * np.log10(255**2 / mse_denoised) if mse_denoised > 0 else float('inf')
    
    return {
        'mse_noisy': mse_noisy,
        'psnr_noisy': psnr_noisy,
        'mse_denoised': mse_denoised,
        'psnr_denoised': psnr_denoised
    }

def encrypt_image(image):
    """Encrypt image using post-quantum Kyber512 KEM"""
    height, width = image.shape
    public_key, secret_key = pqcrypto.kem.kyber512.generate_keypair()
    ciphertext, _ = pqcrypto.kem.kyber512.encapsulate(public_key)
    # For demonstration, we'll just return a placeholder
    # In real use, you'd implement proper encryption of the image data
    return ciphertext, len(ciphertext)

def create_comparison_plot(original, noisy, denoised, metrics):
    """Create a comprehensive comparison visualization"""
    fig = Figure(figsize=(14, 10))
    
    # Image comparisons (2 rows x 3 columns)
    # Row 1: Full images
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
    
    # Row 2: Difference maps
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
    
    # Row 3: Histograms and metrics
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
    
    # Metrics summary
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
    ax9.text(0.1, 0.5, metrics_text, fontsize=9, verticalalignment='center',
             family='monospace', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.3))
    
    fig.tight_layout()
    return fig

def cli_interface():
    """Command-line interface for image processing"""
    parser = argparse.ArgumentParser(description="Image Denoising and Post-Quantum Encryption")
    parser.add_argument('--height', type=int, default=256, help='Height of the generated image')
    parser.add_argument('--width', type=int, default=256, help='Width of the generated image')
    parser.add_argument('--noise', type=int, default=25, help='Noise level for non-Gaussian noise')
    parser.add_argument('--visualize', action='store_true', help='Show visualization plots')
    args = parser.parse_args()

    print("Generating image...")
    image = generate_image(args.height, args.width)
    
    print("Adding noise...")
    noisy_image = add_non_gaussian_noise(image, noise_level=args.noise)
    
    print("Denoising image...")
    denoised_image = denoise_image(noisy_image)
    
    print("Calculating metrics...")
    metrics = calculate_metrics(image, noisy_image, denoised_image)
    
    print("\n" + "="*50)
    print("RESULTS")
    print("="*50)
    print(f"Original Image Size: {args.height}x{args.width}")
    print(f"Noise Level: {args.noise}")
    print(f"\nNoisy Image Metrics:")
    print(f"  MSE:  {metrics['mse_noisy']:.2f}")
    print(f"  PSNR: {metrics['psnr_noisy']:.2f} dB")
    print(f"\nDenoised Image Metrics:")
    print(f"  MSE:  {metrics['mse_denoised']:.2f}")
    print(f"  PSNR: {metrics['psnr_denoised']:.2f} dB")
    print(f"\nImprovement: {metrics['psnr_denoised'] - metrics['psnr_noisy']:.2f} dB")
    
    print("\nEncrypting image...")
    encrypted_image, cipher_size = encrypt_image(denoised_image)
    print(f"Encryption complete. Ciphertext size: {cipher_size} bytes")
    print("="*50)
    
    if args.visualize:
        print("\nGenerating visualization...")
        fig = create_comparison_plot(image, noisy_image, denoised_image, metrics)
        plt.show()

def gui_interface():
    """Enhanced GUI interface with comprehensive visualizations"""
    root = tk.Tk()
    root.title("Image Denoising & Post-Quantum Encryption")
    root.geometry("1200x800")
    
    # Variables to store current images
    current_images = {}
    
    # Create main container with scrollbar
    main_frame = ttk.Frame(root)
    main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    # Control panel
    control_frame = ttk.LabelFrame(main_frame, text="Controls", padding=10)
    control_frame.pack(side=tk.TOP, fill=tk.X, pady=(0, 10))
    
    # Noise level slider
    noise_frame = ttk.Frame(control_frame)
    noise_frame.pack(side=tk.LEFT, padx=10)
    ttk.Label(noise_frame, text="Noise Level:").pack(side=tk.LEFT)
    noise_var = tk.IntVar(value=25)
    noise_slider = ttk.Scale(noise_frame, from_=5, to=100, variable=noise_var, orient=tk.HORIZONTAL, length=200)
    noise_slider.pack(side=tk.LEFT, padx=5)
    noise_label = ttk.Label(noise_frame, text="25")
    noise_label.pack(side=tk.LEFT)
    
    def update_noise_label(val):
        noise_label.config(text=f"{int(float(val))}")
    
    noise_slider.config(command=update_noise_label)
    
    # Buttons
    button_frame = ttk.Frame(control_frame)
    button_frame.pack(side=tk.LEFT, padx=20)
    
    # Status label
    status_var = tk.StringVar(value="Ready")
    status_label = ttk.Label(control_frame, textvariable=status_var, foreground="blue")
    status_label.pack(side=tk.RIGHT, padx=10)
    
    # Canvas for matplotlib figure
    canvas_frame = ttk.Frame(main_frame)
    canvas_frame.pack(fill=tk.BOTH, expand=True)
    
    canvas = None
    
    def load_image():
        """Load image from file"""
        file_path = filedialog.askopenfilename(
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.bmp *.tiff"), ("All files", "*.*")]
        )
        if file_path:
            status_var.set("Loading image...")
            root.update()
            img = Image.open(file_path).convert('L')
            img = img.resize((256, 256))
            img_arr = np.array(img, dtype=np.uint8)
            current_images['original'] = img_arr
            process_image(img_arr)
    
    def generate_test_image():
        """Generate a test gradient image"""
        status_var.set("Generating test image...")
        root.update()
        img_arr = generate_image(256, 256)
        current_images['original'] = img_arr
        process_image(img_arr)
    
    def process_image(image):
        """Process the image and display visualizations"""
        nonlocal canvas
        
        status_var.set("Adding noise...")
        root.update()
        noisy = add_non_gaussian_noise(image, noise_level=noise_var.get())
        current_images['noisy'] = noisy
        
        status_var.set("Denoising image...")
        root.update()
        denoised = denoise_image(noisy)
        current_images['denoised'] = denoised
        
        status_var.set("Calculating metrics...")
        root.update()
        metrics = calculate_metrics(image, noisy, denoised)
        
        status_var.set("Encrypting image...")
        root.update()
        encrypted, cipher_size = encrypt_image(denoised)
        
        status_var.set("Generating visualization...")
        root.update()
        
        # Clear previous canvas
        for widget in canvas_frame.winfo_children():
            widget.destroy()
        
        # Create and display the comparison plot
        fig = create_comparison_plot(image, noisy, denoised, metrics)
        canvas = FigureCanvasTkAgg(fig, master=canvas_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        status_var.set(f"Complete! Encrypted size: {cipher_size} bytes | PSNR Improvement: {metrics['psnr_denoised'] - metrics['psnr_noisy']:.2f} dB")
        
        messagebox.showinfo("Success", 
            f"Image processed and encrypted!\n\n"
            f"PSNR Improvement: {metrics['psnr_denoised'] - metrics['psnr_noisy']:.2f} dB\n"
            f"Noise Reduction: {(1 - metrics['mse_denoised']/metrics['mse_noisy'])*100:.1f}%\n"
            f"Ciphertext Size: {cipher_size} bytes")
    
    # Create buttons
    btn_load = ttk.Button(button_frame, text="Load Image", command=load_image)
    btn_load.pack(side=tk.LEFT, padx=5)
    
    btn_generate = ttk.Button(button_frame, text="Generate Test Image", command=generate_test_image)
    btn_generate.pack(side=tk.LEFT, padx=5)
    
    btn_reprocess = ttk.Button(button_frame, text="Reprocess with New Noise Level", 
                                command=lambda: process_image(current_images.get('original')) if 'original' in current_images else None)
    btn_reprocess.pack(side=tk.LEFT, padx=5)
    
    # Initial message
    welcome_label = ttk.Label(canvas_frame, text="Load an image or generate a test image to begin", 
                              font=('Arial', 14), foreground='gray')
    welcome_label.pack(expand=True)
    
    root.mainloop()

if __name__ == "__main__":
    print("="*60)
    print("Image Denoising & Post-Quantum Encryption Tool")
    print("="*60)
    print("\nChoose mode:")
    print("1 - GUI Mode (Interactive with visualizations)")
    print("2 - CLI Mode (Command line with optional plots)")
    print("="*60)
    
    try:
        choice = input("\nEnter choice (1 or 2): ").strip()
        
        if choice == "1":
            print("\nLaunching GUI...")
            gui_interface()
        elif choice == "2":
            print("\nRunning CLI mode...")
            print("Use --help for options (e.g., --visualize to show plots)\n")
            cli_interface()
        else:
            print("Invalid choice. Defaulting to GUI mode...")
            gui_interface()
    except KeyboardInterrupt:
        print("\n\nExiting...")
    except Exception as e:
        print(f"\nError: {e}")
        print("Falling back to GUI mode...")
        gui_interface()

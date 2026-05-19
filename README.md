# nongossgendenoiser

this is an auto generated read me file paths and names may need to be updated at a future date
Image Denoising and Post-Quantum Encryption Tool

Overview

This Python script provides a combined command-line and GUI-based solution to generate synthetic images, add non-Gaussian noise, perform denoising, and then encrypt the image using post-quantum cryptography.

Features

• Image Generation: Creates a grayscale image with linear pixel values.
• Noise Addition: Adds non-Gaussian (Laplace) noise to the image.
• Denoising: Uses a TV-L1 denoising algorithm to clean up the image.
• Post-Quantum Encryption: Encrypts the denoised image using the Kyber512 algorithm from the PQClean library.


Requirements

You’ll need the following packages:

numpy
opencv-python
Pillow
tk
pqclean


Install them using:

pip install -r requirements.txt


Usage

Command-Line Interface

Run the script from the command line with optional arguments:

python script.py --height 256 --width 256 --noise 25


This will generate an image, add noise, denoise it, and encrypt it.

Graphical User Interface

Just run the script without arguments:

python script.py


A simple GUI will open, allowing you to load an image and process it through the same steps.

Notes

• The generated or processed images can be saved or modified within the script.
• For encryption, the script uses Kyber512, a post-quantum cryptographic algorithm.

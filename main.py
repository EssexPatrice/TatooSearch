import os
import json
import concurrent.futures
from tkinter import Tk, Label, Entry, Button, messagebox
import ollama
from PIL import Image, ImageTk

# Define the folder to automatically search in
DATA_FOLDER = './data'
CACHE_FILE = './descriptions_cache.json'
ALLOWED_EXTENSIONS = ('.png', '.jpg', '.jpeg')

# Load or create a cache file for image descriptions
if os.path.exists(CACHE_FILE):
    with open(CACHE_FILE, 'r') as f:
        descriptions_cache = json.load(f)
else:
    descriptions_cache = {}

# Function to describe images using the smaller llava:7b model
def describe_image(image_path, retries=3):
    if image_path in descriptions_cache:
        return descriptions_cache[image_path]  # Return cached description
    
    attempt = 0
    while attempt < retries:
        try:
            # Send the image to the model (switching to llava:7b or quantized version)
            res = ollama.chat(
                model='llava:7b',  # Switch to a smaller model
                messages=[
                    {'role': 'user', 'content': 'Describe this image', 'images': [image_path]}
                ]
            )
            description = res['message']['content']
            descriptions_cache[image_path] = description  # Cache the description
            with open(CACHE_FILE, 'w') as f:
                json.dump(descriptions_cache, f)  # Save cache to file
            return description  # Return the description
        except Exception as e:
            attempt += 1
            print(f"Attempt {attempt}: Error processing image {image_path}: {e}")
    return None

# Function to format the file name
def format_file_name(file_name):
    # Remove the file extension (.jpg, .png, etc.)
    base_name = os.path.splitext(file_name)[0]
    # Split by underscore to get the first name, last name, and inmate ID
    parts = base_name.split('_')
    if len(parts) == 3:
        first_name, last_name, inmate_id = parts
        return f"{first_name}\n{last_name}\n{inmate_id}"
    return base_name

# Function to perform the search with parallel processing
def search_images(event=None):
    search_query = search_box.get()

    # Ensure the data folder exists
    if not os.path.exists(DATA_FOLDER):
        messagebox.showwarning("Folder Not Found", f"The folder {DATA_FOLDER} does not exist.")
        return

    result_images = []  # Initialize list to store file names of matching images
    image_files = [os.path.join(DATA_FOLDER, f) for f in os.listdir(DATA_FOLDER) if f.lower().endswith(ALLOWED_EXTENSIONS)]

    # Process images in parallel
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_to_image = {executor.submit(describe_image, img_path): img_path for img_path in image_files}
        for future in concurrent.futures.as_completed(future_to_image):
            img_path = future_to_image[future]
            try:
                description = future.result()
                if description and search_query.lower() in description.lower():
                    result_images.append(img_path)  # Collect file paths of matching images
            except Exception as e:
                print(f"Error processing image {img_path}: {e}")
    
    if result_images:
        display_images(result_images)
    else:
        messagebox.showinfo("No Matches", "No images found matching the description.")

# Function to display the result images and file names
def display_images(image_files):
    # Clear previous search results
    for widget in result_frame.winfo_children():
        widget.destroy()

    # Display each image that matched the search query
    for img_path in image_files:
        # Open and resize the image, keeping aspect ratio, but height = 300px
        img = Image.open(img_path)
        img.thumbnail((img.width, 300))  # Set height to 300px and adjust width accordingly
        img = ImageTk.PhotoImage(img)

        # Create a label to hold the image
        img_label = Label(result_frame, image=img)
        img_label.image = img  # Keep a reference to avoid garbage collection
        img_label.pack(side="left", padx=5, pady=5)  # Display side by side with padding

        # Get the formatted file name
        file_name_formatted = format_file_name(os.path.basename(img_path))

        # Create a label to display the formatted file name under the image
        file_name_label = Label(result_frame, text=file_name_formatted, justify="center")
        file_name_label.pack(side="left", padx=5, pady=5)  # Display under the image

# Function to clear the images and labels from the result frame
def clear_images():
    for widget in result_frame.winfo_children():
        widget.destroy()

# Initialize GUI window
root = Tk()
root.title("Tattoo Image Search")

# Set the GUI window size to 500x500 pixels
root.geometry('500x500')

# Input field for the tattoo design description with padding
Label(root, text="Enter design description:").pack(pady=10)
search_box = Entry(root, width=50)
search_box.pack(padx=20, pady=10)  # Add padding around the search bar

# Bind "Enter" key to trigger search
search_box.bind("<Return>", search_images)

# Search button
search_button = Button(root, text="Search", command=search_images)
search_button.pack(pady=5)

# Clear button to remove images and labels
clear_button = Button(root, text="Clear", command=clear_images)
clear_button.pack(pady=5)

# Frame for displaying the search results
result_frame = Label(root)
result_frame.pack()

root.mainloop()
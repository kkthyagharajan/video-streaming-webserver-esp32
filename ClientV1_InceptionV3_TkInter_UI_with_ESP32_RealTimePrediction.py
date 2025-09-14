#Use TF2_1Py_3_11_11CV_h5 environment
#Training the model and saving is done by the file    Py-file-insect-inceptionv3-Working-V1- V3  comments have been modofied in this version
#and stored in D:\Python_Spyder_Working Dir\InsectDetection working\KKT_Model   Use forward slashes
#line 39 check the path for loading the newly trained model. Choose the model that provides highest accuracy manually from 
# that path and KKT_model folder
#line62 labels shoulde be set correctly  for correct prediction  labels = {0: 'Bees', 1: 'Beetles', 2: 'Butterfly', 3: 'Dragonfly', 4: 'Grasshopper'}
# any chnage in the folder names in the path D:\Python_Spyder_Working Dir\InsectDetection working\InsectClasses
# should reflect in line 62 labels
#line 40 check the path for loading the newly trained model. Choose the model that provides highest accuracy manually from 
# that path and KKT_model folder
#line 40: change the .h5 file D:\Python_Spyder_Working Dir\InsectDetection working\KKT_Model\model_19-0.90.h5 
#choose the file 
#In version 1 training and predction both are combined
#Removed unused packages on 12-09-2025

# In[]

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, Scale
from PIL import Image, ImageTk, ImageOps
import numpy as np
from tensorflow import keras
from tensorflow.keras.preprocessing import image
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import threading
import os
import requests
import io
import time
import cv2

# Suppress TensorFlow messages
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

# Load the model
MODEL_PATH = r"D:\32 Python_Spyder_Working Dir\2_InsectDetection working\KKT_Model\model_06-0.95.keras"

class InsectDetectionTkinter:
    def __init__(self, root):
        self.root = root
        self.root.title("Insect Detection System V1")
        self.root.geometry("1200x800")
        
        self.model = None
        self.image_path = None
        self.esp32_url = "http://10.20.29.150/stream"  # Your ESP32 stream URL
        self.update_interval = 0.5  # Default update interval in seconds
        self.is_streaming = False
        self.stream_thread = None
        self.cap = None  # Video capture object
        
        self.setup_ui()
        self.load_model()
    
    def setup_ui(self):
        # Main frames
        left_frame = ttk.Frame(self.root, padding="10")
        left_frame.grid(row=0, column=0, sticky="nsew")
        
        right_frame = ttk.Frame(self.root, padding="10")
        right_frame.grid(row=0, column=1, sticky="nsew")
        
        # Image display
        self.image_label = tk.Label(left_frame, text="No image selected", 
                                   background="lightgray", anchor="center",
                                   width=40, height=15)
        self.image_label.grid(row=0, column=0, pady=10, padx=10, sticky="nsew")
        
        # ESP32 URL configuration
        url_frame = ttk.Frame(left_frame)
        url_frame.grid(row=1, column=0, pady=5, sticky="ew")
        
        ttk.Label(url_frame, text="ESP32 Stream URL:").pack(side=tk.LEFT, padx=5)
        self.url_var = tk.StringVar(value=self.esp32_url)
        self.url_entry = ttk.Entry(url_frame, textvariable=self.url_var, width=30)
        self.url_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # Update interval slider
        interval_frame = ttk.Frame(left_frame)
        interval_frame.grid(row=2, column=0, pady=5, sticky="ew")
        
        ttk.Label(interval_frame, text="Capture Interval (s):").pack(side=tk.LEFT, padx=5)
        self.interval_var = tk.DoubleVar(value=self.update_interval)
        self.interval_scale = Scale(interval_frame, from_=0.1, to=2.0, resolution=0.1, 
                                   orient=tk.HORIZONTAL, variable=self.interval_var,
                                   length=200, showvalue=True)
        self.interval_scale.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # Buttons
        button_frame = ttk.Frame(left_frame)
        button_frame.grid(row=3, column=0, pady=10)
        
        self.load_btn = ttk.Button(button_frame, text="Load Image", 
                                 command=self.load_image)
        self.load_btn.pack(side=tk.LEFT, padx=5)
        
        self.predict_btn = ttk.Button(button_frame, text="Predict", 
                                    command=self.predict, state="disabled")
        self.predict_btn.pack(side=tk.LEFT, padx=5)
        
        self.stream_btn = ttk.Button(button_frame, text="Start Real Time Prediction", 
                                   command=self.toggle_stream)
        self.stream_btn.pack(side=tk.LEFT, padx=5)
        
        # Progress bar
        self.progress_bar = ttk.Progressbar(left_frame, mode='indeterminate')
        self.progress_bar.grid(row=4, column=0, pady=10, sticky="ew")
        
        # Result label
        self.result_label = ttk.Label(left_frame, text="Result: None", 
                                    font=("Arial", 12, "bold"))
        self.result_label.grid(row=5, column=0, pady=10)
        
        # Status label for streaming
        self.status_label = ttk.Label(left_frame, text="Status: Ready", 
                                     font=("Arial", 10))
        self.status_label.grid(row=6, column=0, pady=5)
        
        # Matplotlib figure
        self.fig, self.ax = plt.subplots(figsize=(5, 4))
        self.canvas = FigureCanvasTkAgg(self.fig, master=right_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.columnconfigure(1, weight=1)
        self.root.rowconfigure(0, weight=1)
        left_frame.columnconfigure(0, weight=1)
        left_frame.rowconfigure(0, weight=1)
    
    def load_model(self):
        try:
            self.model = keras.models.load_model(MODEL_PATH)
            messagebox.showinfo("Success", "Model loaded successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load model: {str(e)}")
    
    def load_image(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("Image Files", "*.png *.jpg *.jpeg *.bmp")]
        )
        
        if file_path:
            self.image_path = file_path
            img = Image.open(file_path)
            img.thumbnail((400, 400))
            photo = ImageTk.PhotoImage(img)
            self.image_label.config(image=photo, text="")
            self.image_label.image = photo
            self.predict_btn.config(state="normal")
            self.result_label.config(text="Result: None")
    
    def predict(self):
        if not self.image_path:
            messagebox.showwarning("Warning", "Please load an image first!")
            return
        
        self.progress_bar.start()
        self.predict_btn.config(state="disabled")
        self.load_btn.config(state="disabled")
        self.stream_btn.config(state="disabled")
        
        # Run prediction in separate thread
        thread = threading.Thread(target=self.run_prediction)
        thread.daemon = True
        thread.start()
    
    def run_prediction(self):
        try:
            img = image.load_img(self.image_path, target_size=(300, 300))
            img = image.img_to_array(img, dtype=np.uint8)
            img = np.array(img)/255.0
            
            p = self.model.predict(img[np.newaxis, ...], verbose=0)
            
            labels = {0: 'Bees', 1: 'Beetles', 2: 'Butterfly', 3: 'Dragonfly', 4: 'Grasshopper'}
            predicted_class = labels[np.argmax(p[0], axis=-1)]
            
            classes = []
            prob = []
            for i, j in enumerate(p[0], 0):
                classes.append(labels[i])
                prob.append(round(j*100, 2))
            
            # Update UI in main thread
            self.root.after(0, self.update_results, predicted_class, classes, prob)
            
        except Exception as e:
            # Capture the exception properly
            error_message = str(e)
            self.root.after(0, lambda: self.show_error(error_message))
    
    def toggle_stream(self):
        if self.is_streaming:
            self.stop_stream()
        else:
            self.start_stream()
    
    def start_stream(self):
        self.esp32_url = self.url_var.get()
        self.update_interval = self.interval_var.get()
        
        if not self.esp32_url:
            messagebox.showwarning("Warning", "Please enter ESP32 Stream URL!")
            return
        
        self.is_streaming = True
        self.stream_btn.config(text="Stop Real Time Prediction")
        self.load_btn.config(state="disabled")
        self.predict_btn.config(state="disabled")
        self.status_label.config(text="Status: Connecting to ESP32 stream...")
        
        # Start streaming thread
        self.stream_thread = threading.Thread(target=self.stream_prediction)
        self.stream_thread.daemon = True
        self.stream_thread.start()
    
    def stop_stream(self):
        self.is_streaming = False
        self.stream_btn.config(text="Start Real Time Prediction")
        self.load_btn.config(state="normal")
        self.predict_btn.config(state="normal")
        self.status_label.config(text="Status: Ready")
        
        # Release video capture
        if self.cap:
            self.cap.release()
            self.cap = None
    
    def stream_prediction(self):
        """Continuously capture frames from ESP32 stream and run prediction"""
        try:
            # Open video stream
            self.cap = cv2.VideoCapture(self.esp32_url)
            
            if not self.cap.isOpened():
                self.root.after(0, lambda: self.status_label.config(
                    text="Status: Failed to open stream"))
                self.stop_stream()
                return
            
            self.root.after(0, lambda: self.status_label.config(
                text=f"Status: Streaming - Capturing every {self.update_interval}s"))
            
            last_capture_time = 0
            
            while self.is_streaming and self.cap.isOpened():
                current_time = time.time()
                
                # Read frame from stream
                ret, frame = self.cap.read()
                
                if not ret:
                    self.root.after(0, lambda: self.status_label.config(
                        text="Status: Failed to read frame from stream"))
                    time.sleep(1)
                    continue
                
                # Capture frame at specified interval
                if current_time - last_capture_time >= self.update_interval:
                    last_capture_time = current_time
                    
                    # Convert BGR to RGB
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    
                    # Convert to PIL Image
                    img = Image.fromarray(frame_rgb)
                    
                    # Prepare image for prediction
                    img_array = img.resize((300, 300))
                    img_array = image.img_to_array(img_array)
                    img_array = np.array(img_array)/255.0
                    
                    # Run prediction
                    p = self.model.predict(img_array[np.newaxis, ...], verbose=0)
                    
                    labels = {0: 'Bees', 1: 'Beetles', 2: 'Butterfly', 3: 'Dragonfly', 4: 'Grasshopper'}
                    predicted_class = labels[np.argmax(p[0], axis=-1)]
                    
                    classes = []
                    prob = []
                    for i, j in enumerate(p[0], 0):
                        classes.append(labels[i])
                        prob.append(round(j*100, 2))
                    
                    # Display image and update results in main thread
                    display_img = img.copy()
                    display_img.thumbnail((400, 400))
                    self.root.after(0, self.update_stream_display, display_img, predicted_class, classes, prob)
                
                # Small delay to prevent high CPU usage
                time.sleep(0.01)
                
        except Exception as e:
            error_msg = str(e)
            self.root.after(0, lambda: self.status_label.config(
                text=f"Status: Error - {error_msg}"))
            time.sleep(2)
        finally:
            if self.cap:
                self.cap.release()
                self.cap = None
    
    def update_stream_display(self, img, predicted_class, classes, prob):
        """Update the display with streamed image and prediction results"""
        if not self.is_streaming:
            return
            
        photo = ImageTk.PhotoImage(img)
        self.image_label.config(image=photo, text="")
        self.image_label.image = photo
        self.result_label.config(text=f"Result: {predicted_class}")
        
        # Update probability chart
        self.ax.clear()
        index = np.arange(len(classes))
        self.ax.bar(index, prob)
        self.ax.set_xlabel('Labels', fontsize=8)
        self.ax.set_ylabel('Probability (%)', fontsize=8)
        self.ax.set_xticks(index)
        self.ax.set_xticklabels(classes, fontsize=8, rotation=20)
        self.ax.set_title('Probability Distribution')
        self.canvas.draw()
    
    def show_error(self, error_message):
        """Show error message and reset UI"""
        messagebox.showerror("Error", f"Prediction failed: {error_message}")
        self.reset_ui()
    
    def update_results(self, predicted_class, classes, prob):
        self.progress_bar.stop()
        self.predict_btn.config(state="normal")
        self.load_btn.config(state="normal")
        self.stream_btn.config(state="normal")
        
        self.result_label.config(text=f"Result: {predicted_class}")
        
        # Update chart
        self.ax.clear()
        index = np.arange(len(classes))
        self.ax.bar(index, prob)
        self.ax.set_xlabel('Labels', fontsize=8)
        self.ax.set_ylabel('Probability (%)', fontsize=8)
        self.ax.set_xticks(index)
        self.ax.set_xticklabels(classes, fontsize=8, rotation=20)
        self.ax.set_title('Probability Distribution')
        self.canvas.draw()
    
    def reset_ui(self):
        self.progress_bar.stop()
        self.predict_btn.config(state="normal")
        self.load_btn.config(state="normal")
        self.stream_btn.config(state="normal")

# To run the Tkinter version
if __name__ == "__main__":
    root = tk.Tk()
    app = InsectDetectionTkinter(root)
    root.mainloop()
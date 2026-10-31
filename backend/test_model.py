import os
import sys

# Suppress TF logging
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

print("Importing Keras...")
import keras
print(f"Keras version: {keras.__version__}")

model_path = "backend/models/best_model_resnet50.keras"
print(f"Loading model from {model_path}...")
try:
    model = keras.models.load_model(model_path)
    print("SUCCESS: Model loaded with keras.models.load_model!")
    print(f"Input shape: {model.input_shape}")
    print(f"Output shape: {model.output_shape}")
except Exception as e:
    print(f"Keras 3 load failed: {e}")
    print("Trying tensorflow.keras...")
    import tensorflow as tf
    model = tf.keras.models.load_model(model_path)
    print("SUCCESS: Model loaded with tf.keras.models.load_model!")
    print(f"Input shape: {model.input_shape}")
    print(f"Output shape: {model.output_shape}")

print("Testing inference on sample image...")
import numpy as np
from PIL import Image

sample_img = "backend/samples/sample_caries_front.jpg"
img = Image.open(sample_img).convert('RGB').resize((224, 224))
x = np.array(img, dtype=np.float32)
# ResNet50 caffe preprocessing: BGR and mean subtraction
x = x[:, :, ::-1]  # RGB to BGR
x[:, :, 0] -= 103.939
x[:, :, 1] -= 116.779
x[:, :, 2] -= 123.68
x = np.expand_dims(x, axis=0)

preds = model.predict(x)
print(f"Raw predictions shape: {preds.shape}")
print(f"Predictions: {preds[0]}")

import json
with open("backend/models/class_indices.json") as f:
    class_indices = json.load(f)

for idx, score in enumerate(preds[0]):
    cname = class_indices.get(str(idx), f"Class {idx}")
    print(f"  {cname}: {score * 100:.2f}%")

best_idx = int(np.argmax(preds[0]))
print(f"Top predicted class: {class_indices.get(str(best_idx))} ({preds[0][best_idx]*100:.2f}%)")


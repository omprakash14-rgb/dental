import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
import tensorflow as tf
import numpy as np
from PIL import Image
import cv2
import keras

model_path = "backend/models/best_model_resnet50.keras"
model = keras.models.load_model(model_path)

resnet_layer = model.get_layer('resnet50')
conv_layer_name = 'conv5_block3_out'
target_conv_layer = resnet_layer.get_layer(conv_layer_name)

print("Target conv layer found:", target_conv_layer.name)

# Create a submodel that outputs the feature map and final predictions
grad_model = keras.models.Model(
    inputs=[model.inputs],
    outputs=[target_conv_layer.output, model.output]
)

sample_img = "backend/samples/sample_caries_front.jpg"
orig_img = Image.open(sample_img).convert('RGB')
orig_w, orig_h = orig_img.size
img_resized = orig_img.resize((224, 224))
x = np.array(img_resized, dtype=np.float32)
x = x[:, :, ::-1]  # RGB to BGR
x[:, :, 0] -= 103.939
x[:, :, 1] -= 116.779
x[:, :, 2] -= 123.68
x = np.expand_dims(x, axis=0)

with tf.GradientTape() as tape:
    conv_outputs, predictions = grad_model(x)
    pred_index = tf.argmax(predictions[0])
    loss = predictions[:, pred_index]

grads = tape.gradient(loss, conv_outputs)
pooled_grads = tf.reduce_mean(grads, axis=(0, 1, 2))

conv_outputs = conv_outputs[0]
heatmap = conv_outputs @ pooled_grads[..., tf.newaxis]
heatmap = tf.squeeze(heatmap)

# Apply ReLU to heatmap
heatmap = tf.maximum(heatmap, 0) / (tf.math.reduce_max(heatmap) + 1e-10)
heatmap_np = heatmap.numpy()

# Resize heatmap to original image size
heatmap_resized = cv2.resize(heatmap_np, (orig_w, orig_h))

# Find bounding box around region with high activation
thresh = (heatmap_resized > 0.45).astype(np.uint8) * 255
contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

boxes = []
for cnt in contours:
    if cv2.contourArea(cnt) > (orig_w * orig_h * 0.01):  # at least 1% of image
        bx, by, bw, bh = cv2.boundingRect(cnt)
        boxes.append({
            "x": int(bx),
            "y": int(by),
            "width": int(bw),
            "height": int(bh),
            "normalized": [
                round(by / orig_h, 4),
                round(bx / orig_w, 4),
                round((by + bh) / orig_h, 4),
                round((bx + bw) / orig_w, 4)
            ]
        })

print(f"Computed Grad-CAM successfully! Detected {len(boxes)} bounding regions.")
for b in boxes:
    print("  Box:", b)


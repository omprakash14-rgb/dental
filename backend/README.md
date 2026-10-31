---
title: DentalAI ResNet50 Inference Backend
emoji: 🦷
colorFrom: blue
colorTo: cyan
sdk: docker
app_port: 7860
pinned: false
---

# DentalAI — Intraoral Photographic Screening & ResNet-50 Backend

This repository powers the AI inference and clinical reporting microservice for **DentalAI**.

- **AI Model:** Pretrained ResNet-50 trained on 6 intraoral photographic classes (Calculus, Caries, Gingivitis, Hypodontia, Mouth Ulcer, Tooth Discoloration).
- **Grad-CAM Visual Salience:** Target layer `conv5_block3_out`.
- **Framework:** FastAPI, Uvicorn, TensorFlow 2.16, Keras 3.0, OpenCV, ReportLab.


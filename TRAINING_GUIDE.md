# Custom Recognition Training Guide

## Overview

Train HomePi to recognize your specific car and family members using custom image recognition models.

## Quick Start

### Step 1: Collect Training Images

**Via Web Interface (Easiest):**

1. Open HomePi web interface: `http://raspberry-pi-ip:5000`
2. Scroll to "AI Security System" section
3. Go to "Custom Recognition Training"
4. Upload photos:
   - **For Car**: Click "Train Car Recognition" → Upload photos
   - **For Person**: Click "Train Person Recognition" → Upload photos

**Requirements:**
- Minimum 50 images per car/person
- Various angles (front, side, back, 3/4 view)
- Different lighting (day, night, cloudy, sunny)
- Multiple distances (close-up and far away)
- High quality, not blurry

### Step 2: Label Your Images

When uploading:
- **Car Label Examples**: `my_car`, `dads_car`, `neighbors_bmw`
- **Person Label Examples**: `dad`, `mom`, `john`, `sarah`

Labels should be:
- Lowercase
- No spaces (use underscore)
- Descriptive and unique

### Step 3: Monitor Progress

The web interface shows:
- ✅ **Ready** - 50+ images collected
- ⚠️ **Need more** - Less than 50 images

Progress bar shows collection status (100% = 50 images).

---

## Method 1: On-Device Training (Coming Soon)

**Note**: Currently not implemented. Upload your training data and use Method 2 below.

Future features:
- One-click training button
- Progress notifications
- Automatic model deployment

---

## Method 2: Remote Training (Recommended)

Train on your laptop/desktop with GPU for faster results.

### Prerequisites

**On your laptop:**
- Python 3.8-3.11
- CUDA-capable GPU (recommended, not required)
- 4GB+ RAM

### Step 1: Download Training Data from Pi

```bash
# On Raspberry Pi
cd ~/homepi
zip -r training_data.zip training_data/

# Transfer to laptop
scp mujadded@raspberry-pi:~/homepi/training_data.zip ~/Downloads/
```

### Step 2: Setup Training Environment on Laptop

```bash
# Create directory
mkdir ~/homepi-training
cd ~/homepi-training

# Extract training data
unzip ~/Downloads/training_data.zip

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install tensorflow==2.13.0
pip install pillow numpy matplotlib scikit-learn
```

### Step 3: Create Training Script

Save as `train_classifier.py`:

```python
"""
Simple transfer learning classifier for car/person recognition
"""

import os
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
import numpy as np
from pathlib import Path

# Configuration
CATEGORY = 'car'  # or 'person'
IMAGE_SIZE = (224, 224)
BATCH_SIZE = 32
EPOCHS = 50
MODEL_NAME = f'{CATEGORY}_classifier'

# Load data
def load_dataset(data_dir):
    """Load images from directory structure"""
    train_ds = keras.utils.image_dataset_from_directory(
        data_dir,
        validation_split=0.2,
        subset="training",
        seed=123,
        image_size=IMAGE_SIZE,
        batch_size=BATCH_SIZE
    )
    
    val_ds = keras.utils.image_dataset_from_directory(
        data_dir,
        validation_split=0.2,
        subset="validation",
        seed=123,
        image_size=IMAGE_SIZE,
        batch_size=BATCH_SIZE
    )
    
    return train_ds, val_ds

# Create model with transfer learning
def create_model(num_classes):
    """Create model using MobileNetV2 base"""
    base_model = keras.applications.MobileNetV2(
        input_shape=IMAGE_SIZE + (3,),
        include_top=False,
        weights='imagenet'
    )
    
    # Freeze base model
    base_model.trainable = False
    
    # Add custom head
    inputs = keras.Input(shape=IMAGE_SIZE + (3,))
    x = base_model(inputs, training=False)
    x = layers.GlobalAveragePooling2D()(x)
    x = layers.Dropout(0.2)(x)
    outputs = layers.Dense(num_classes, activation='softmax')(x)
    
    model = keras.Model(inputs, outputs)
    
    model.compile(
        optimizer='adam',
        loss='sparse_categorical_crossentropy',
        metrics=['accuracy']
    )
    
    return model

# Train
def train():
    data_dir = f'training_data/{CATEGORY}'
    
    if not os.path.exists(data_dir):
        print(f"Error: Directory not found: {data_dir}")
        return
    
    # Check number of classes
    num_classes = len([d for d in os.listdir(data_dir) if os.path.isdir(os.path.join(data_dir, d))])
    print(f"Found {num_classes} classes")
    
    if num_classes < 2:
        print("Error: Need at least 2 classes (your car + unknown)")
        print("Tip: Add an 'unknown' folder with random car images")
        return
    
    # Load data
    print("Loading dataset...")
    train_ds, val_ds = load_dataset(data_dir)
    
    # Create model
    print("Creating model...")
    model = create_model(num_classes)
    model.summary()
    
    # Train
    print("Training...")
    history = model.fit(
        train_ds,
        validation_data=val_ds,
        epochs=EPOCHS,
        callbacks=[
            keras.callbacks.EarlyStopping(patience=10, restore_best_weights=True),
            keras.callbacks.ModelCheckpoint(f'{MODEL_NAME}_best.h5', save_best_only=True)
        ]
    )
    
    # Save final model
    model.save(f'{MODEL_NAME}_final.h5')
    print(f"Model saved as {MODEL_NAME}_final.h5")
    
    # Convert to TFLite
    print("Converting to TFLite...")
    converter = tf.lite.TFLiteConverter.from_keras_model(model)
    converter.optimizations = [tf.lite.Optimize.DEFAULT]
    tflite_model = converter.convert()
    
    with open(f'{MODEL_NAME}.tflite', 'wb') as f:
        f.write(tflite_model)
    
    print(f"TFLite model saved as {MODEL_NAME}.tflite")
    print("\nNext steps:")
    print(f"1. Copy {MODEL_NAME}.tflite to Raspberry Pi")
    print("2. Update config.json with model path")
    print("3. Restart HomePi service")

if __name__ == '__main__':
    train()
```

### Step 4: Prepare Training Data

Your data should be organized like:

```
training_data/
├── car/
│   ├── my_car/
│   │   ├── img_001.jpg
│   │   ├── img_002.jpg
│   │   └── ... (50+ images)
│   └── unknown_car/
│       ├── img_001.jpg
│       └── ... (50+ random car images)
└── person/
    ├── dad/
    │   └── ... (50+ images)
    ├── mom/
    │   └── ... (50+ images)
    └── unknown_person/
        └── ... (50+ random people images)
```

**Important**: Add an `unknown` class with random images for better accuracy!

You can download random car/person images from:
- Google Images (use bulk downloader extension)
- https://unsplash.com/s/photos/car
- https://www.pexels.com/search/people/

### Step 5: Train the Model

```bash
# Train car classifier
python train_classifier.py

# Edit CATEGORY to 'person' and run again
python train_classifier.py
```

Training will take 5-30 minutes depending on your GPU.

### Step 6: Deploy to Raspberry Pi

```bash
# Copy trained model to Pi
scp car_classifier.tflite mujadded@raspberry-pi:~/homepi/models/
scp person_classifier.tflite mujadded@raspberry-pi:~/homepi/models/

# SSH to Pi and update config
ssh mujadded@raspberry-pi
cd ~/homepi
nano config.json
```

Update config.json:

```json
{
  "security": {
    "detection": {
      "car_model_path": "models/car_classifier.tflite",
      "person_model_path": "models/person_classifier.tflite"
    }
  }
}
```

Restart HomePi:

```bash
sudo systemctl restart homepi.service
```

---

## Method 3: Edge TPU Compilation (Advanced)

For maximum speed on Coral TPU:

### Step 1: Install Edge TPU Compiler

```bash
# On laptop (not Pi)
curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo apt-key add -
echo "deb https://packages.cloud.google.com/apt coral-edgetpu-stable main" | sudo tee /etc/apt/sources.list.d/coral-edgetpu.list
sudo apt-get update
sudo apt-get install edgetpu-compiler
```

### Step 2: Compile Model

```bash
edgetpu_compiler car_classifier.tflite
# Generates: car_classifier_edgetpu.tflite
```

### Step 3: Deploy

```bash
scp car_classifier_edgetpu.tflite mujadded@raspberry-pi:~/homepi/models/
```

Update config to use `_edgetpu.tflite` model.

---

## Tips for Better Accuracy

### Image Collection Tips

1. **Variety is key**: 
   - Day/night/cloudy/rainy
   - Clean/dirty car
   - Different seasons

2. **Multiple angles**:
   - Front, back, sides
   - 3/4 views
   - Close-up and distant

3. **Consistent framing**:
   - Car should fill ~50% of frame
   - Include some background

4. **Quality matters**:
   - Not blurry or dark
   - 1080p resolution minimum
   - No extreme filters

### Training Tips

1. **Use data augmentation**:
   - Add to training script:
   ```python
   data_augmentation = keras.Sequential([
       layers.RandomFlip("horizontal"),
       layers.RandomRotation(0.1),
       layers.RandomZoom(0.1),
   ])
   ```

2. **More is better**:
   - 100+ images > 50 images
   - Aim for balanced classes

3. **Test thoroughly**:
   - Walk past camera at different times
   - Test with similar cars nearby
   - Verify at night

---

## Troubleshooting

### Low Accuracy

**Problem**: Model confuses your car with others

**Solutions**:
- Collect more images (aim for 100+)
- Add more "unknown_car" images of similar vehicles
- Include distinctive features (bumper stickers, damage, etc.)

### Model Won't Load

**Problem**: TFLite model fails to load

**Solutions**:
- Check file exists: `ls -lh models/car_classifier.tflite`
- Verify file isn't corrupted (re-transfer)
- Check config.json path is correct

### Slow Inference

**Problem**: Detection is laggy

**Solutions**:
- Use Edge TPU compilation
- Reduce image size in training (try 160x160)
- Use MobileNetV2 Lite instead of standard

---

## Current Status

✅ **Implemented**:
- Image upload API
- Training data collection
- Progress tracking
- Web interface for uploads

⏳ **Coming Soon**:
- On-device training
- One-click model deployment
- Automatic testing and validation
- Pre-trained model library

---

## Support

Need help? Check:
- Web interface training guide
- `IMPLEMENTATION_STATUS.md` for current features
- Jetson logs: `docker-compose logs -f`
- Pi logs: `sudo journalctl -u homepi.service -f`

---

**Pro Tip**: Train on laptop first, then transfer models to Pi. Much faster!


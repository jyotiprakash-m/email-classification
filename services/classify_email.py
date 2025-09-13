import pickle
import os
import re

MODEL_PATH = 'pkl_files/email_dataset_long.pkl'

classifier = None
label_encoder = None

def load_model():
    global classifier, label_encoder
    try:
        with open(MODEL_PATH, 'rb') as f:
            model_data = pickle.load(f)
        classifier = model_data['pipeline']
        label_encoder = model_data['label_encoder']
        print("Email classification model loaded successfully!")
    except FileNotFoundError:
        print(f"Error: Model file '{MODEL_PATH}' not found.")
        print("Please ensure the model is saved in the correct directory.")
        classifier = None
        label_encoder = None
    except Exception as e:
        print(f"Error loading model: {e}")
        classifier = None
        label_encoder = None

def preprocess_text_simple(text):
    if text is None:
        return ""
    text = text.lower()
    text = re.sub(r'\S+@\S+', ' email_address ', text)
    text = re.sub(r'http\S+|www\S+', ' url_link ', text)
    text = re.sub(r'\b\d+\b', ' number ', text)
    text = re.sub(r'[^\w\s\?\!]', ' ', text)
    text = ' '.join(text.split())
    return text

def classify_email(email_content: str):
    global classifier, label_encoder
    if classifier is None or label_encoder is None:
        load_model()
    print(f"Classifier: {classifier}, Label Encoder: {label_encoder}")
    if classifier is None or label_encoder is None:
        raise RuntimeError("Email classification model or label encoder not loaded.")
    processed_text = preprocess_text_simple(email_content)
    prediction_encoded = classifier.predict([processed_text])[0]
    probabilities = classifier.predict_proba([processed_text])[0]
    predicted_department = label_encoder.inverse_transform([prediction_encoded])[0]
    dept_probs = {dept: probabilities[i] for i, dept in enumerate(label_encoder.classes_)}
    return {
        "predicted_department": predicted_department,
        "confidence": float(max(probabilities)),
        "all_probabilities": {k: float(v) for k, v in dept_probs.items()}
    }

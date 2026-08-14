# Machine Learning Based Diabetes Complication Prediction Framework

A machine-learning-based diabetes prediction and early-warning application developed as a Final Year Project.

## Overview

The system provides a multi-step workflow for:

- Diabetes stage prediction
- Etiological type prediction
- Diabetes complication prediction
- Patient management
- Reports and analytics
- AI-assisted chat functionality

## Technologies

- Python
- Streamlit
- Scikit-learn
- Pandas
- NumPy
- Plotly
- SQLite
- Joblib
- Gemini API

## Machine Learning

The application uses trained machine-learning models stored in the `ml_models/` directory.

The public repository intentionally excludes private hospital/patient datasets and local database files.

## Project Structure

```text
├── ml.py
├── database.py
├── auth_db.py
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
└── ml_models/
```

## Setup

1. Clone the repository.
2. Create and activate a Python virtual environment.
3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Create a `.env` file from `.env.example` and add your own API credentials.
5. Run the Streamlit application:

```bash
python -m streamlit run ml.py
```

## Data Privacy

Private patient records, local databases, and project datasets are not included in this public repository.

## Note

This repository contains the software implementation of the academic project. It is intended for educational/research purposes and should not be treated as a substitute for professional medical diagnosis.

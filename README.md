# Machine Learning Based Diabetes Complication Prediction Framework

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.12-blue?style=for-the-badge&logo=python" alt="Python">
  <img src="https://img.shields.io/badge/Streamlit-Application-red?style=for-the-badge&logo=streamlit" alt="Streamlit">
  <img src="https://img.shields.io/badge/Scikit--Learn-Machine%20Learning-orange?style=for-the-badge&logo=scikit-learn" alt="Scikit-learn">
  <img src="https://img.shields.io/badge/SQLite-Database-003B57?style=for-the-badge&logo=sqlite" alt="SQLite">
  <img src="https://img.shields.io/badge/Gemini%20API-AI%20Integration-4285F4?style=for-the-badge&logo=google" alt="Gemini API">
</p>

<p align="center">
  <strong>Final Year Project | Machine Learning | Artificial Intelligence | Healthcare</strong>
</p>

---

## 📌 Project Overview

**Machine Learning Based Diabetes Complication Prediction Framework** is a Final Year Project developed to support the prediction and early identification of diabetes-related risks using Machine Learning and Artificial Intelligence.

The framework provides an interactive healthcare application that combines trained Machine Learning models, clinical data processing, patient management, analytics, reporting, and AI-assisted interaction within a unified system.

The application follows a structured multi-stage prediction workflow:

> **Diabetes Stage → Etiological Type → Complication Prediction → Risk Assessment → Report & Recommendations**

The project is designed as an academic healthcare decision-support framework and is **not intended to replace professional medical diagnosis or clinical decision-making**.

---

## 🎯 Project Objectives

The main objectives of this project are to:

- Develop a Machine Learning-based diabetes prediction framework.
- Identify the patient's diabetes stage through clinical and demographic information.
- Predict the etiological type of diabetes.
- Predict diabetes-related complications.
- Provide an interactive interface for healthcare-oriented prediction workflows.
- Maintain patient prediction records and history.
- Present analytical results through charts and visualizations.
- Generate patient-oriented reports.
- Integrate Artificial Intelligence for AI-assisted interaction.
- Provide a structured platform for demonstrating Machine Learning in healthcare.

---

## ✨ Key Features

### 🩺 Diabetes Stage Prediction

The system analyzes relevant patient information and predicts the corresponding diabetes stage through the trained Machine Learning workflow.

### 🧬 Etiological Type Prediction

The framework provides prediction of the supported etiological categories of diabetes, including:

- Type 1 Diabetes
- Type 2 Diabetes
- Gestational Diabetes
- Secondary Diabetes

### ⚠️ Diabetes Complication Prediction

The system uses trained Machine Learning models to assess diabetes-related complication risks as part of the multi-stage prediction workflow.

### 📊 Risk Assessment

Prediction results are presented through an interactive interface to help users understand the generated risk information.

### 👤 Patient Management

The application provides functionality for managing patient information and prediction records.

### 📈 Analytics & Visualization

Interactive analytics and visualizations are provided to support the interpretation of stored prediction information.

### 📄 Report Generation

The framework provides reporting functionality for presenting patient-related prediction results and relevant information.

### 🤖 AI-Assisted Chat

The application integrates the **Gemini API** to provide an AI-assisted interaction component within the healthcare application.

---

## 🔬 Machine Learning Workflow

The Machine Learning component is organized into a multi-stage prediction pipeline.

```text
                Patient Information
                       │
                       ▼
             ┌─────────────────────┐
             │ Diabetes Prediction │
             └──────────┬──────────┘
                        │
                        ▼
             ┌─────────────────────┐
             │ Etiological Type    │
             │ Prediction          │
             └──────────┬──────────┘
                        │
                        ▼
             ┌─────────────────────┐
             │ Complication        │
             │ Prediction          │
             └──────────┬──────────┘
                        │
                        ▼
             ┌─────────────────────┐
             │ Risk Assessment     │
             └──────────┬──────────┘
                        │
                        ▼
             ┌─────────────────────┐
             │ Reports & Analytics │
             └─────────────────────┘

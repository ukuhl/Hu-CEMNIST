# Hu-CEMNIST: Human-Generated Counterfactual Explanations for MNIST

This repository contains the **Hu-CEMNIST dataset**, a large-scale collection of **human-generated counterfactual explanations (CFEs)** for MNIST digits, together with the data collection interface and analysis code.

## Repository Structure

├── Analysis/      # Scripts for generating and evaluating CFEs

├── Data/          # Final dataset and annotations

├── Server/        # Web-based data collection interface

├── README.md

└── mnist-data.tar.gz

## 🔬 Analysis

'Analysis/' contains code for generating and evaluating counterfactual explanations:

- 'cf_dice.py': DiCE-based CFEs  
- 'cf_nf.py': Neural feature-based CFEs  
- 'cf_proto.py': Prototype-based CFEs  
- 'dnn.py': MNIST classifier  
- 'utils.py': Utility functions  
- 'REQUIREMENTS.txt': Python dependencies  

---

## 📊 Dataset

'Data/' contains the full dataset:

- 'Hu-CEMNIST_valid_images.zip'  
  → Final set of 4659 validated human-generated CFEs (.npz + .png) 

- 'annotator_ratings_complete.csv'  
  → Annotations from three independent raters  

- 'demographics_complete.csv'  
  → Participant demographics  

- 'surveyData_complete.csv'  
  → Questionnaire responses  

- 'user_info_complete.csv'  
  → Study metadata and trial-level information  

---

## 🧾 Data Format

### 'annotator_ratings_complete.csv'

Per-image annotation data:

- 'userID': participant ID  
- 'trialNo': trial index (1–3)  
- 'filename': generated image  
- 'GroundTruth_Target': intended target digit  
- 'rater1/2/3': assigned digit  
- 'rater*_unsure': optional uncertainty flag  
- 'correct_target_judgement_by_all': 1 if all raters agreed on target  

---

### 'demographics_complete.csv'

Participant-level demographics:

- 'userID'  
- 'gender' (categorical coding)  
- 'age' (categorical coding)  

---

### 'surveyData_complete.csv'

Questionnaire responses:

- 'userID'  
- 'itemNo': question ID  
- 'responseNo': option index  
- 'checked': selected option (1/0)  
- 'responseText': free-text (if applicable)  
- 'responseTime': response time (ms)  

---

### 'user_info_complete.csv'

Study execution and trial metadata:

- 'Wave': data collection batch  
- 'userID'  
- 'comprehensionCheck*': responses and pass indicators  
- 'trial*_baseDigit': source digit  
- 'trial*_targetDigit': target digit  
- 'trial*_percChange': pixel-level modification ratio  

---

## 🌐 Data Collection Interface

'Server/' contains the web-based annotation tool:

- 'server.py': backend server  
- 'dbmgr.py': data handling  
- 'create_all_trials.py': trial generation  
- 'export_results.py': data export  

### Frontend ('Server/site/'):
- 'index.htm': main interface  
- 'js/': logic and drawing tool  
- 'static/': assets (images, tutorial, styles)

Participants edited MNIST digits using a pixel-based interface supporting drawing, erasing, and undo actions.

---

## 📦 MNIST Data

- 'mnist-data.tar.gz': original MNIST dataset used for training

---

## 🧠 Summary

- **~4.6k validated human CFEs**
- Pixel-level transformations from source → target digits
- Independent human verification via 3 annotators
- Rich metadata: demographics, behavior, and study context

---

## 📄 License

Creative Commons Attribution 4.0 International

---

## 📚 Citation

If you use this dataset, please cite: TBD

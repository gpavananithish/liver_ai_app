# 🩺 Liver AI: Smart Hepatic Diagnostics & AI Assistant

Welcome to **Liver AI**, a powerful yet simple healthcare platform designed to help people understand liver health better. This project uses smart Machine Learning to predict liver cirrhosis stages and an empathetic AI Chatbot to guide users through their health journey.

- **🌍Check Out Here**: [Hosted on PythonAnywhere](https://gpavananitish.pythonanywhere.com/) 
---

## 🚀 Key Features

### 1. 📊 Cirrhosis Staging Predictor
Enter simple clinical data (like Bilirubin, Albumin, etc.), and our **LightGBM model** will instantly tell you the liver status:
- **Normal**
- **Initial Stage**
- **Intermediate Stage**
- **End Stage**

### 2. 👩‍⚕️ Dr. Qwen: AI Health Consultant
Our AI assistant, **Dr. Qwen**, is always ready to talk:
- **Medical Education**: Explains complex liver terms in simple, human-friendly language.
- **Report Analysis**: Upload your medical PDF reports, and the AI will summarize the findings for you.
- **Lifestyle Guidance**: Get tips on diet, hydration, and healthy habits.

### 3. 📈 Interactive Health Dashboard
Visualize your health over time! Our dashboard shows you charts of your health trends, helping you see if your levels are improving or need attention.

### 4. 📄 Professional PDF Reports
Need to show your results to a doctor? Generate and download a professional, neatly formatted PDF report of your assessment with one click.

### 5. 🌗 Premium Design
A beautiful, modern interface with a "Glassmorphism" look. It fully supports **Dark Mode** and **Light Mode** for a comfortable experience on any device.

---

## 🛠️ Tech Stack (The Tools We Used)

### **Frontend (The Face)**
- **HTML5 & CSS3**: Custom styles with a premium "Glass" effect.
- **JavaScript**: For smooth animations and interactive chat.
- **Chart.js**: To create beautiful, easy-to-read health charts.
- **Font Awesome**: Premium icons for a professional look.

### **Backend (The Brain)**
- **Python & Django 5.1**: The powerful engine that runs the website.
- **SQLite**: A reliable database to store user profiles and health records.
- **xhtml2pdf**: To turn your health data into professional PDF documents.

### **AI & Machine Learning (The Smart Parts)**
- **LightGBM**: A high-speed model used for predicting health stages.
- **Qwen 2.5 (LLM)**: A smart AI model (hosted via Hugging Face) that powers our chatbot.
- **PyMuPDF (fitz)**: Used to read and extract text from uploaded medical PDF reports.

---

## 📂 Project Structure
```text
myproject/
├── app1/               # Core logic, AI chat, and ML model loading
├── myproject/          # Main website settings
├── static/             # CSS, JS, Images, and SVGs
├── templates/          # HTML pages (Home, Login, Prediction, etc.)
├── media/              # Storage for generated reports
├── manage.py           # Django command-line tool
└── requirements.txt    # List of all Python tools needed
```

---

## 🚀 How to Run Locally

1. **Clone the project**:
   ```cmd
   git clone https://github.com/gpavananithish/liver_ai_app.git
   cd liver_ai_app
   ```

2. **Set up a Virtual Environment**:
   ```cmd
   python -m venv venv
   venv\Scripts\activate
   ```

3. **Install Tools**:
   ```cmd
   pip install -r requirements.txt
   ```

4. **Run the Server**:
   ```cmd
   python manage.py runserver
   ```
   Now open `http://127.0.0.1:8000` in your browser!

---

## 🌐 Deployment & Links

- **📂 GitHub Code**: [gpavananithish/liver_ai_app](https://github.com/gpavananithish/liver_ai_app)
- **🌍 Live Demo**: [Hosted on PythonAnywhere](https://gpavananitish.pythonanywhere.com/) 

---

## ⚠️ Medical Disclaimer
*This application is for informational and educational purposes only. It is not a substitute for professional medical advice, diagnosis, or treatment. Always seek the advice of your physician or other qualified health provider with any questions you may have regarding a medical condition.*

---


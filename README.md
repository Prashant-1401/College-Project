# ✉️ Email Enhancer

An AI-powered web application that transforms your draft emails into polished, professional communications using Google's Gemini AI.

![Email Enhancer Demo](UI%20images/Screenshot%20(30).png)

## ✨ Features

- **AI-Powered Polish** - Uses Gemini AI to enhance grammar, clarity, and professionalism
- **Multiple Tone Options** - Professional, Formal, Friendly, Concise, Marketing, Apology, Appreciation
- **Real-time Analysis** - Get tone and readability metrics for your polished email
- **One-Click Send** - Send emails directly from the app via SMTP
- **Dark/Light Mode** - Toggle between themes for comfortable viewing
- **Responsive Design** - Works seamlessly on desktop and mobile

## 🛠️ Tech Stack

- **Frontend**: HTML5, CSS3, JavaScript
- **Backend**: Python, Flask
- **AI**: Google Gemini API
- **Email**: SMTP with SSL

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- Google Gemini API Key ([Get one here](https://makersuite.google.com/app/apikey))

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/YOUR_USERNAME/EmailPolisher.git
   cd EmailPolisher
   ```

2. **Create a virtual environment**
   ```bash
   cd backend
   python -m venv venv
   venv\Scripts\activate  # Windows
   # source venv/bin/activate  # macOS/Linux
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Create a `.env` file in the `backend` folder**
   ```env
   GEMINI_API_KEY=your_gemini_api_key_here
   
   # Optional: For email sending functionality
   SMTP_SERVER=smtp.gmail.com
   SMTP_PORT=465
   SENDER_EMAIL=your_email@gmail.com
   SENDER_PASSWORD=your_app_password
   ```

5. **Run the application**
   ```bash
   python app.py
   ```

6. **Open your browser** and go to `http://localhost:5000`

## 📁 Project Structure

```
EmailPolisher/
├── backend/
│   ├── app.py           # Flask server & API endpoints
│   └── requirements.txt # Python dependencies
├── frontend/
│   ├── index.html       # Main HTML page
│   ├── style.css        # Styling
│   └── script.js        # Frontend logic
├── UI images/           # Screenshots
├── .gitignore
└── README.md
```

## 📸 Screenshots

| Draft Mode | Polished Result |
|------------|-----------------|
| ![Draft](UI%20images/Screenshot%20(31).png) | ![Polished](UI%20images/Screenshot%20(32).png) |

## 🔒 Security Notes

- Never commit your `.env` file
- Use [Gmail App Passwords](https://support.google.com/accounts/answer/185833) instead of your actual password
- The app includes XSS protection and input validation

## 📄 License

This project is open source and available under the [MIT License](LICENSE).

## 🤝 Contributing

Contributions, issues, and feature requests are welcome!

---

Made with ❤️ using AI

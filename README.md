# Gemini Flash YouTube Video Summary App

An advanced YouTube video analysis tool powered by Google's Gemini Flash 1.5 AI. This application automatically generates comprehensive summaries, detailed notes, and enables interactive Q&A about video content.

![App Screenshot](assets/app-screenshot.png) *(You can add a screenshot of your app here)*

## 🚀 Features

- **AI-Powered Video Analysis**: Leverages Google's Gemini Flash 1.5 for deep content understanding
- **Comprehensive Summaries**: Generates detailed notes and key points from video content
- **Interactive Q&A**: Ask questions about the video content and get AI-powered responses
- **Multiple Export Options**: Download summaries in Markdown or Word format
- **Timestamp Integration**: Preserves video timestamps in summaries for easy reference
- **User-Friendly Interface**: Clean, intuitive design built with Streamlit

## 🛠️ Installation

1. Clone the repository:
```bash
git clone https://github.com/lhiebert01/gemini-flash-tube.git
cd gemini-flash-tube
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install required packages:
```bash
pip install -r requirements.txt
```

4. Set up your environment variables:
   - Create a `.env` file in the project root
   - Add your Google API key:
     ```
     GOOGLE_API_KEY=your_api_key_here
     ```

## 💻 Usage

1. Start the application:
```bash
streamlit run app.py
```

2. Open your web browser to the displayed URL (typically `http://localhost:8501`)

3. Paste a YouTube URL into the input field

4. Click "Generate Detailed Notes" to analyze the video

5. Explore the generated summary and ask questions about the content

6. Download the summary in your preferred format (Markdown/Word)

## 🔧 Requirements

- Python 3.8+
- Streamlit
- Google Generative AI
- python-dotenv
- youtube_transcript_api
- python-docx
- beautifulsoup4
- requests

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👤 Author

**Lindsay Hiebert**
- LinkedIn: [Lindsay Hiebert](https://www.linkedin.com/in/lindsayhiebert/)
- GitHub: [@lhiebert01](https://github.com/lhiebert01)

## 🙏 Acknowledgments

- Google Gemini AI for providing the advanced language model capabilities
- Streamlit for the excellent web app framework
- All contributors and users of this application

---

*Made with ❤️ using Google Gemini Flash and Streamlit*
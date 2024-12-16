import streamlit as st
import os
from dotenv import load_dotenv
import google.generativeai as genai
from youtube_transcript_api import YouTubeTranscriptApi
from datetime import datetime
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
import io
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs


# Must be the first Streamlit command
 

st.set_page_config(
    page_title="Gemini Flash YouTube Video Summary App",
    page_icon="🎯",
    layout="wide"
)

# 1. Add this with your other session state variables (near the top of the file):
if "current_summary" not in st.session_state:
    st.session_state.current_summary = None
if "word_doc_binary" not in st.session_state:
    st.session_state.word_doc_binary = None
if "video_processed" not in st.session_state:
    st.session_state.video_processed = False
if "current_transcript" not in st.session_state:
    st.session_state.current_transcript = None
if "current_video_id" not in st.session_state:
    st.session_state.current_video_id = None
if "current_video_title" not in st.session_state:
    st.session_state.current_video_title = None
# Add this new line:
if "qa_history" not in st.session_state:
    st.session_state.qa_history = []


# Load environment variables and configure Gemini
load_dotenv(override=True)
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Constants for prompts
CHUNK_PROMPT = """Analyze this portion of the video transcript and provide:
1. Key points discussed in this section
2. Notable quotes with timestamps (preserve exact wording)
3. Technical data, statistics, or numerical information
4. Important concepts and definitions
5. Brief summary of the content

For quotes and technical data, maintain exact wording and include timestamps.
Transcript section: """

FINAL_PROMPT = """Based on the analysis of all sections, provide a comprehensive summary with:
1. Main Topic/Title: Identify the title of the video and the core subject
2. Executive Summary (200 words): Brief overview
3. Key Points (10-20): Most important concepts discussed
4. Detailed Analysis (2000 words): In-depth discussion
5. Technical Data & Statistics: List all statistical information
6. Notable Quotes (10-20): Include significant quotes with timestamps
7. Key Terms & Definitions (10-20): Technical terminology explained
8. Concepts & Frameworks (10-20): Theoretical frameworks discussed
9. Timeline & Structure: Content progression
10. Practical Applications (5-10 examples): Real-world applications

Format quotes as: "[HH:MM:SS] Speaker (if known): Quote"
Format technical data as: "[HH:MM:SS] Technical point: Data/Statistics"

Please synthesize this complete summary: """

def get_youtube_video_id(url):
    """Extract video ID from YouTube URL."""
    try:
        parsed_url = urlparse(url)
        if parsed_url.hostname in ['www.youtube.com', 'youtube.com']:
            return parse_qs(parsed_url.query)['v'][0]
        elif parsed_url.hostname == 'youtu.be':
            return parsed_url.path[1:]
    except Exception:
        return None
    return None

def get_youtube_title(video_id):
    """Get YouTube video title."""
    try:
        url = f"https://www.youtube.com/watch?v={video_id}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        title = soup.find('meta', property='og:title')
        return title['content'] if title else None
    except Exception as e:
        st.warning(f"Could not extract video title: {str(e)}")
        return None

def extract_transcript(video_id):
    """Extract transcript from YouTube video."""
    try:
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
        formatted_transcript = ""
        for item in transcript_list:
            timestamp = int(item["start"])
            time_str = f"[{timestamp//3600:02d}:{(timestamp%3600)//60:02d}:{timestamp%60:02d}]"
            formatted_transcript += f"{time_str} {item['text']} "
        return formatted_transcript.strip()
    except Exception as e:
        st.error(f"Error extracting transcript: {str(e)}")
        return None

def chunk_text(text, chunk_size=10000):
    """Split text into manageable chunks."""
    words = text.split()
    chunks = []
    current_chunk = []
    current_length = 0
    
    for word in words:
        if current_length + len(word) + 1 <= chunk_size:
            current_chunk.append(word)
            current_length += len(word) + 1
        else:
            chunks.append(' '.join(current_chunk))
            current_chunk = [word]
            current_length = len(word)
    
    if current_chunk:
        chunks.append(' '.join(current_chunk))
    return chunks

def generate_content(text, prompt, retry_count=3):
    """Generate content using Gemini."""
    for attempt in range(retry_count):
        try:
            model = genai.GenerativeModel("gemini-1.5-flash-latest",
                                        generation_config={
                                            'temperature': 0.7,
                                            'top_p': 0.8,
                                            'top_k': 40
                                        })
            response = model.generate_content(prompt + text)
            return response.text
        except Exception as e:
            if attempt == retry_count - 1:
                st.error(f"Error generating content: {str(e)}")
                return None
            continue

def analyze_transcript(transcript):
    """Analyze transcript in chunks."""
    chunks = chunk_text(transcript)
    progress_bar = st.progress(0)
    chunk_analyses = []
    
    for i, chunk in enumerate(chunks):
        st.write(f"Analyzing part {i+1} of {len(chunks)}...")
        progress_bar.progress((i + 1) / len(chunks))
        
        chunk_summary = generate_content(chunk, CHUNK_PROMPT)
        if chunk_summary:
            chunk_analyses.append(chunk_summary)
    
    combined_analysis = "\n\n".join(chunk_analyses)
    return generate_content(combined_analysis, FINAL_PROMPT)

# 2. Replace your entire create_markdown_download function with this:
def create_markdown_download(summary, video_title, video_id, qa_history=None):
    """Create markdown format document with Q&A history."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    markdown_content = f"""# Video Summary: {video_title}

Generated on: {timestamp}
Video Link: https://youtube.com/watch?v={video_id}

![Thumbnail](http://img.youtube.com/vi/{video_id}/0.jpg)

{summary}

"""
    
    # Add Q&A section if there are questions
    if qa_history and len(qa_history) > 0:
        markdown_content += "\n## Questions & Answers\n\n"
        for qa in qa_history:
            markdown_content += f"**Q: {qa['question']}**\n\n"
            markdown_content += f"A: {qa['answer']}\n\n"
    
    markdown_content += "\n---\nGenerated using YouTube Video Summarizer"
    return markdown_content


# 3. Replace your entire create_word_document function with this:
def create_word_document(summary, video_title, video_id, qa_history=None):
    """Create Word document with proper formatting for markdown content."""
    doc = Document()
    
    # Add title
    title = doc.add_heading(f"Video Summary: {video_title or 'Untitled'}", 0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    # Add metadata
    doc.add_paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    doc.add_paragraph(f"Video Link: https://youtube.com/watch?v={video_id}")
    doc.add_paragraph()
    
    def format_markdown_text(paragraph, text):
        """Format bold and italic text within a paragraph."""
        parts = re.split(r'(\*\*.*?\*\*|\*.*?\*|`.*?`)', text)
        for part in parts:
            if part.startswith('**') and part.endswith('**'):
                # Bold text
                run = paragraph.add_run(part[2:-2])
                run.bold = True
            elif part.startswith('*') and part.endswith('*'):
                # Italic text
                run = paragraph.add_run(part[1:-1])
                run.italic = True
            elif part.startswith('`') and part.endswith('`'):
                # Code text
                run = paragraph.add_run(part[1:-1])
                run.font.name = 'Courier New'
            elif part:
                # Regular text
                paragraph.add_run(part)

    def parse_and_create_table(table_text):
        """Create a properly formatted Word table from markdown table text."""
        lines = [line.strip() for line in table_text.split('\n') if line.strip()]
        if not lines:
            return None

        # Filter out separator lines and empty lines
        rows = []
        for line in lines:
            if line.startswith('|') and line.endswith('|'):
                # Skip separator lines
                if not re.match(r'^[\|\s\-:]+$', line):
                    cells = [cell.strip() for cell in line.strip('|').split('|')]
                    rows.append(cells)

        if not rows:
            return None

        # Create table
        num_cols = len(rows[0])
        table = doc.add_table(rows=len(rows), cols=num_cols)
        table.style = 'Table Grid'
        table.autofit = True

        # Fill table with content
        for i, row in enumerate(rows):
            for j, cell_content in enumerate(row):
                cell = table.cell(i, j)
                # Clear existing paragraph if any
                if cell.paragraphs:
                    p = cell.paragraphs[0]
                    p.clear()
                else:
                    p = cell.add_paragraph()

                # Format cell content
                if i == 0:  # Header row
                    run = p.add_run(cell_content)
                    run.bold = True
                else:
                    format_markdown_text(p, cell_content)

                # Set cell padding
                p.paragraph_format.space_before = Pt(2)
                p.paragraph_format.space_after = Pt(2)

        return table

    def process_content(content):
        """Process content blocks and apply appropriate formatting."""
        # Split content into blocks (tables and non-tables)
        blocks = re.split(r'(\n\|.*?\n\n)', content, flags=re.DOTALL)
        
        for block in blocks:
            if not block.strip():
                continue
            
            # Check if block is a table
            if block.strip().startswith('|') and '|' in block:
                table = parse_and_create_table(block)
                if table:
                    doc.add_paragraph()  # Add spacing after table
            else:
                # Process non-table content
                lines = block.strip().split('\n')
                current_list_level = 0
                
                for line in lines:
                    if not line.strip():
                        continue
                        
                    # Check for headers
                    header_match = re.match(r'^(#{1,6})\s+(.+)$', line)
                    if header_match:
                        level = len(header_match.group(1))
                        doc.add_heading(header_match.group(2), level)
                        continue
                    
                    # Check for bullet points
                    list_match = re.match(r'^(\s*)[*\-+]\s+(.+)$', line)
                    if list_match:
                        indent = len(list_match.group(1))
                        level = indent // 2
                        p = doc.add_paragraph(style='List Bullet')
                        p.paragraph_format.left_indent = Pt(level * 12)
                        format_markdown_text(p, list_match.group(2))
                        continue
                    
                    # Check for numbered lists
                    num_list_match = re.match(r'^(\s*)\d+\.\s+(.+)$', line)
                    if num_list_match:
                        indent = len(num_list_match.group(1))
                        level = indent // 2
                        p = doc.add_paragraph(style='List Number')
                        p.paragraph_format.left_indent = Pt(level * 12)
                        format_markdown_text(p, num_list_match.group(2))
                        continue
                    
                    # Regular paragraph
                    p = doc.add_paragraph()
                    format_markdown_text(p, line)

    # Process main summary
    process_content(summary)
    
    # Add Q&A section if there are questions
    if qa_history and len(qa_history) > 0:
        doc.add_heading("Questions & Answers", 1)
        for qa in qa_history:
            question_para = doc.add_paragraph()
            question_run = question_para.add_run("Q: ")
            question_run.bold = True
            format_markdown_text(question_para, qa['question'])
            
            answer_para = doc.add_paragraph()
            answer_run = answer_para.add_run("A: ")
            answer_run.bold = True
            format_markdown_text(answer_para, qa['answer'])
            
            doc.add_paragraph()  # Add spacing between Q&A pairs
    
    # Add footer
    doc.add_paragraph()
    footer = doc.add_paragraph("Generated using YouTube Video Summarizer")
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    return doc

def generate_qa_response(question, transcript, summary):
    """Generate Q&A response."""
    prompt = f"""Based on the video transcript and summary, answer this question:

Question: {question}

Summary:
{summary}

Transcript:
{transcript}

Please provide a specific answer based on the video content."""

    return generate_content(prompt, "")

def main():
    # Enhanced CSS styling
    st.markdown("""
    <style>
    .main-title {
        background: linear-gradient(120deg, #4285F4, #0F9D58);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3rem;
        font-weight: 800;
        text-align: center;
        padding: 1rem 0;
        margin-bottom: 0.5rem;
        font-family: 'Google Sans', Arial, sans-serif;
    }

    .subtitle {
        color: #5f6368;
        font-size: 1.3rem;
        text-align: center;
        margin-bottom: 1rem;
        font-family: 'Google Sans', Arial, sans-serif;
    }

    .stButton > button {
        background: linear-gradient(120deg, #4285F4, #0F9D58);
        color: white;
        border-radius: 30px;
        padding: 0.6rem 2rem;
        font-weight: bold;
        border: none;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        transition: all 0.3s ease;
    }

    .video-container {
        background: white;
        border-radius: 15px;
        padding: 1.5rem;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        margin: 2rem auto;
        max-width: 800px;
    }

    .section-header {
        color: #4285F4;
        font-size: 1.8rem;
        font-weight: bold;
        margin: 1.5rem 0;
        padding-left: 0.5rem;
        border-left: 4px solid #4285F4;
    }

    .footer {
        text-align: center;
        padding: 1rem 0;
        color: #666;
        font-size: 0.9rem;
        margin-top: 2rem;
        border-top: 1px solid #eee;
    }

    .linkedin-link {
        color: #0077b5;
        text-decoration: none;
    }
    </style>
    """, unsafe_allow_html=True)

    # Single compact header
    st.markdown("""
    <div style="text-align: center; padding: 1rem;">
        <h1 class="main-title">🎯 Gemini Flash YouTube Video Summary App</h1>
        <p class="subtitle">AI-Powered Video Analysis & Summarization</p>
        <div style="margin-top: 1rem;">
            <a href="https://www.linkedin.com/in/lindsayhiebert/" class="linkedin-link">By Lindsay Hiebert</a>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Quick Guide in expander
    with st.expander("ℹ️ How to Use"):
        st.markdown("""
        1. 🔗 Paste a YouTube URL below
        2. 🚀 Click 'Generate Detailed Notes'
        3. 📝 Get AI-powered summary and insights
        4. ❓ Ask questions about the content
        5. 📥 Download in Markdown or Word format
        """)

    # Rest of your code continues here...
    youtube_link = st.text_input("🎥 Enter YouTube Video Link:", placeholder="https://www.youtube.com/watch?v=...")
    
        
    # Then, modify the main logic section (replace the existing if youtube_link: block):
    if youtube_link:
        video_id = get_youtube_video_id(youtube_link)
        if not video_id:
            st.error("Invalid YouTube URL")
            return

        # Only process if it's a new video or no video has been processed
        if video_id != st.session_state.current_video_id:
            transcript = extract_transcript(video_id)
            if not transcript:
                st.error("Could not extract video transcript")
                return

            video_title = get_youtube_title(video_id)
            
            # Store current video information
            st.session_state.current_video_id = video_id
            st.session_state.current_video_title = video_title
            st.session_state.current_transcript = transcript
            # Reset previous results
            st.session_state.current_summary = None
            st.session_state.word_doc_binary = None
            st.session_state.video_processed = False
        
        # Display video thumbnail
        st.markdown('<div class="video-container">', unsafe_allow_html=True)
        st.image(f"http://img.youtube.com/vi/{st.session_state.current_video_id}/0.jpg",
                use_container_width=True,
                caption=st.session_state.current_video_title or "Video Thumbnail")
        if st.session_state.current_video_title:
            st.markdown(f'<div style="text-align: center;">{st.session_state.current_video_title}</div>', 
                       unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # Generate button or show existing summary
        if not st.session_state.video_processed:
            if st.button("🚀 Generate Detailed Notes", type="primary", key="generate_button"):
                with st.spinner("🔄 Analyzing video content..."):
                    summary = analyze_transcript(st.session_state.current_transcript)
                    
                    if summary:
                        st.session_state.current_summary = summary
                        st.session_state.video_processed = True
                        st.session_state.word_doc_binary = None  # Reset word doc binary
                        st.rerun()  # Rerun to update UI with new state  # Rerun to update UI with new state
        
        # Show results if video has been processed
        if st.session_state.video_processed and st.session_state.current_summary:
            st.success("✨ Summary generated successfully!")
            
            st.markdown('<h2 class="section-header">📋 Detailed Notes</h2>', unsafe_allow_html=True)
            st.markdown(st.session_state.current_summary)
            
            # Download options
            col1, col2 = st.columns(2)
            
            with col1:
                markdown_content = create_markdown_download(
                    st.session_state.current_summary,
                    st.session_state.current_video_title,
                    st.session_state.current_video_id,
                    st.session_state.qa_history
                )
                st.download_button(
                    label="📥 Download Markdown",
                    data=markdown_content,
                    file_name=f"video_summary_{st.session_state.current_video_id}.md",
                    mime="text/markdown",
                    key="markdown_download"
                )
            with col2:
                if st.session_state.word_doc_binary is None:
                    doc = create_word_document(
                        st.session_state.current_summary,
                        st.session_state.current_video_title,
                        st.session_state.current_video_id,
                        st.session_state.qa_history  # Add this parameter
                    )
                    bio = io.BytesIO()
                    doc.save(bio)
                    st.session_state.word_doc_binary = bio.getvalue()
                
                st.download_button(
                    label="📄 Download Word",
                    data=st.session_state.word_doc_binary,
                    file_name=f"video_summary_{st.session_state.current_video_id}.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    key="word_download"
                )
            
            # Q&A Section
            

            st.markdown('<h2 class="section-header">❓ Ask Questions About the Video</h2>', 
                      unsafe_allow_html=True)
            
            # Display existing Q&A history
            if st.session_state.qa_history:
                st.markdown("### Previous Questions & Answers")
                for qa in st.session_state.qa_history:
                    st.markdown(f"**Q: {qa['question']}**")
                    st.markdown(f"A: {qa['answer']}\n")
            
            # Add a key to track if we should clear the input
            if "clear_input" not in st.session_state:
                st.session_state.clear_input = False
            
            # Create the text input with a default value based on clear_input state
            user_question = st.text_input(
                "Enter your question:", 
                key="qa_input",
                value="" if st.session_state.clear_input else st.session_state.get("qa_input", "")
            )
            
            # Reset the clear_input flag
            st.session_state.clear_input = False
            
            if user_question:
                with st.spinner("🤔 Analyzing your question..."):
                    answer = generate_qa_response(
                        user_question,
                        st.session_state.current_transcript,
                        st.session_state.current_summary
                    )
                    if answer:
                        # Add to Q&A history
                        st.session_state.qa_history.append({
                            "question": user_question,
                            "answer": answer
                        })
                        
                        # Update the word document binary to include new Q&A
                        doc = create_word_document(
                            st.session_state.current_summary,
                            st.session_state.current_video_title,
                            st.session_state.current_video_id,
                            st.session_state.qa_history
                        )
                        bio = io.BytesIO()
                        doc.save(bio)
                        st.session_state.word_doc_binary = bio.getvalue()
                        
                        # Show the new answer
                        st.markdown("### 💡 Latest Answer")
                        st.markdown(answer)
                        
                        # Set the clear_input flag to True
                        st.session_state.clear_input = True
                        # Clear the input by triggering a rerun
                        st.rerun()

# Single compact header


    
    # New footer code goes here
    st.markdown("---")  # This creates a clean horizontal line
    st.markdown("""
    <div style="text-align: center; font-size: 0.8rem; color: #666; margin: 10px 0;">
        End of Analysis
    </div>
    <div style="text-align: center; font-size: 0.7rem; color: #888; margin: 5px 0;">
        Made by Lindsay Hiebert powered by GenAI tools: ❤️ Google Gemini Flash and Streamlit<br>
        <a href="https://www.linkedin.com/in/lindsayhiebert/" style="color: #0077b5; text-decoration: none;">Connect with me on LinkedIn</a>
    </div>
    <div style="text-align: center; font-size: 0.6rem; color: #999; margin-top: 5px;">
        Gemini Flash YouTube Video Summary App
    </div>
    """, unsafe_allow_html=True)
    st.markdown("---")  # Another clean horizontal line at the very bottom


#if __name__ == "__main__":
#    main()
main()

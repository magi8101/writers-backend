import os
import requests
from fastapi import FastAPI, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from bs4 import BeautifulSoup
import google.generativeai as genai

app = FastAPI()

# Enable CORS for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Fetch API Key securely from environment variables
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("❌ GEMINI_API_KEY is missing. Set it in Render Environment Variables.")

# Configure Gemini API
genai.configure(api_key=GEMINI_API_KEY)

# Function to scrape website content
def scrape_website(url: str):
    """Fetches and extracts textual content from the given URL."""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        title = soup.title.text.strip() if soup.title else "No title available"
        paragraphs = [p.text.strip() for p in soup.find_all("p") if p.text.strip()]
        content = " ".join(paragraphs)[:2000]  # Limit content to first 2000 characters

        if not content:
            raise HTTPException(status_code=400, detail="No readable content found on the webpage.")

        return {"title": title, "content": content}
    
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"🔴 Error fetching website: {str(e)}")

# Function to generate content using Gemini API
def generate_content(prompt: str):
    """Generates content based on a structured prompt."""
    try:
        model = genai.GenerativeModel("gemini-1.5-pro-latest")
        response = model.generate_content(prompt)
        if response and hasattr(response, "text"):
            return response.text.strip()
        return "⚠️ Error: No response from AI."
    except Exception as e:
        return f"❌ AI Generation Error: {str(e)}"

# API route to generate content based on user selection
@app.post("/generate")
def generate(
    url: str = Form(None),
    company_name: str = Form(None),
    product_name: str = Form(None),
    ideal_user: str = Form(None),
    email: str = Form(None),
    content_type: str = Form("instagram"),  # Default to Instagram
):
    """Handles content generation for Instagram, Blog, and Twitter based on user selection."""
    
    scraped_data_prompt = ""
    user_details_prompt = ""
    
    # Process website scraping if URL is provided
    if url:
        scraped_data = scrape_website(url)
        scraped_data_prompt = f"""
        Website Title: {scraped_data['title']}
        Website Content: {scraped_data['content']}
        """

    # Process user-provided details separately
    if company_name or product_name or ideal_user or email:
        user_details_prompt = f"""
        Company Name: {company_name}
        Product Name: {product_name}
        Target Audience: {ideal_user}
        Contact Email: {email}
        """

    # Generate content based on selection
    generated_content = ""

    if content_type == "instagram":
        prompt = f"""
        You are an expert social media content creator. Generate an **Instagram post** 
        based on the details below:

        {scraped_data_prompt}
        {user_details_prompt}

        **Instagram Post Requirements**:
        - Keep it under **200 words**
        - Use an **engaging caption**
        - Include **5-7 relevant hashtags**
        - Make it visually appealing

        Format:  
        **Caption:**  
        **Hashtags:**  
        """
        generated_content = generate_content(prompt)

    elif content_type == "blog":
        prompt = f"""
        You are a professional content writer. Generate a well-structured **blog article** 
        based on the details below:

        {scraped_data_prompt}
        {user_details_prompt}

        **Blog Requirements**:
        - **SEO-optimized** (use keywords naturally)
        - **800-1000 words long**
        - Include **an introduction, main content, and a conclusion**
        - Use an **engaging and professional tone**
        - Format the response with headings and bullet points

        Format:  
        **Title:**  
        **Introduction:**  
        **Main Content:**  
        **Conclusion:**  
        """
        generated_content = generate_content(prompt)

    elif content_type == "twitter":
        prompt = f"""
        You are an expert in crafting **engaging Twitter posts**. Generate a compelling tweet 
        based on the details below:

        {scraped_data_prompt}
        {user_details_prompt}

        **Twitter Post Requirements**:
        - Keep it under **280 characters**
        - Make it catchy and engaging
        - Include **2-5 trending hashtags**
        - Encourage user engagement

        Format:  
        **Tweet:**  
        **Hashtags:**  
        """
        generated_content = generate_content(prompt)

    else:
        generated_content = "⚠️ Invalid content type selected."

    # Return generated content
    return {"content_type": content_type, "generated_content": generated_content or "⚠️ No content generated."}

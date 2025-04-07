import google.generativeai as genai
from flask import current_app
from bs4 import BeautifulSoup
import re
import traceback

def init_gemini():
    try:
        genai.configure(api_key=current_app.config['GOOGLE_GEMINI_API_KEY'])
        model = genai.GenerativeModel('gemini-pro')
        return model
    except Exception as e:
        print(f"Error initializing Gemini: {str(e)}")
        print(traceback.format_exc())
        raise

def extract_page_content(html_content):
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        for script in soup(["script", "style"]):
            script.decompose()
        text = soup.get_text(separator=' ', strip=True)
        text = re.sub(r'\s+', ' ', text)
        return text
    except Exception as e:
        print(f"Error extracting page content: {str(e)}")
        return ""

def get_buyer_response(query, preferences=None, page_content=None):
    try:
        model = init_gemini()
        
        prompt = """You are RealEstimate's AI assistant. Be concise and direct.

        About RealEstimate:
        - Real estate platform in India
        - Connects buyers and sellers
        - Features: property search, AI help, messaging
        
        Guidelines:
        1. Keep responses under 3 sentences when possible
        2. Be direct and specific
        3. For property queries, focus on key details
        4. Suggest next steps when relevant"""
        
        if preferences:
            prompt += f"\nUser Preferences: {preferences}"
        
        if page_content:
            prompt += f"\nPage Context: {page_content}"
            
        prompt += f"\nQuestion: {query}"
        
        response = model.generate_content(prompt)
        return response.text
        
    except Exception as e:
        print(f"Error in get_buyer_response: {str(e)}")
        return "Sorry, I couldn't process your request. Please try again."

def get_seller_response(query, property_details=None, page_content=None):
    try:
        model = init_gemini()
        
        prompt = """You are a real estate assistant helping sellers manage properties. 
        Be concise and professional in your responses."""
        
        if property_details:
            prompt += f"\nProperty Details: {property_details}"
        
        if page_content:
            # Limit page content length
            page_content = page_content[:500] + "..." if len(page_content) > 500 else page_content
            prompt += f"\nPage Context: {page_content}"
            
        prompt += f"\nQuestion: {query}"
        
        print(f"Sending prompt to Gemini: {prompt[:200]}...")  # Debug print
        
        response = model.generate_content(prompt)
        return response.text
        
    except Exception as e:
        print(f"Error in get_seller_response: {str(e)}")
        print(traceback.format_exc())
        return "I apologize, but I'm having trouble processing your request. Please try again." 
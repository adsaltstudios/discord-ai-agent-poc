import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')

print(f"Testing Google AI with API key: {GOOGLE_API_KEY[:10]}...")

try:
    import google.generativeai as genai
    
    # Configure with your API key
    genai.configure(api_key=GOOGLE_API_KEY)
    
    # Create a model
    model = genai.GenerativeModel('gemini-2.0-flash')
    
    # Test with a simple question
    response = model.generate_content("What is the capital of France?")
    
    print("✅ Success! Google AI responded:")
    print(response.text)
    
except Exception as e:
    print(f"❌ Error: {e}")

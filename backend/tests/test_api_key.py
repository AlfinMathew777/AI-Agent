
import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

def test_api():
    api_key = os.getenv("GOOGLE_API_KEY")
    print(f"API Key found: {api_key[:5]}...{api_key[-5:] if api_key else 'None'}")
    
    if not api_key:
        print("Error: No API key found.")
        return

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-flash-latest')
        
        print("Sending request to Gemini...")
        response = model.generate_content("Hello, can you hear me?")
        
        print("\nResponse received:")
        print(response.text)
        print("\nSUCCESS: API is working.")
        
    except Exception as e:
        print("\nFAILURE: API call failed.")
        print(f"Error: {e}")

if __name__ == "__main__":
    test_api()

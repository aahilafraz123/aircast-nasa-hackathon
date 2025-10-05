import os
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

def test_openai():
    """Test if OpenAI API is working"""
    try:
        print("🧪 Testing OpenAI connection...")
        
        # Simple test call
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Say 'Hello from AirCast!' in a friendly way."}
            ],
            max_tokens=50
        )
        
        result = response.choices[0].message.content
        
        print("✅ OpenAI API is working!")
        print(f"📝 Response: {result}")
        print(f"💰 Tokens used: {response.usage.total_tokens}")
        
        return True
        
    except Exception as e:
        print(f"❌ OpenAI API Error: {str(e)}")
        return False

if __name__ == "__main__":
    test_openai()
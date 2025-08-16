from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import openai
import os
import json
from datetime import datetime

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

class ZimChemBot:
    def __init__(self):
        # Fixed OpenAI client initialization
        openai.api_key = os.getenv('OPENAI_API_KEY')
        self.conversations = {}
        
        self.system_message = """You are ZimChem AI, an expert chemistry assistant. You help with:

- Chemical equations and balancing
- Molecular structures and properties  
- Reaction mechanisms
- Laboratory procedures and safety
- Chemical calculations and stoichiometry
- Organic, inorganic, and physical chemistry
- Chemical nomenclature
- Image analysis of chemical structures, equations, lab setups

Keep responses clear, educational, and accurate. Prioritize safety in lab procedures.
If analyzing images, describe what you see clearly before providing chemical insights."""

    def get_conversation_history(self, user_id):
        if user_id not in self.conversations:
            self.conversations[user_id] = [
                {"role": "system", "content": self.system_message}
            ]
        return self.conversations[user_id]

    def add_to_conversation(self, user_id, role, content):
        history = self.get_conversation_history(user_id)
        history.append({"role": role, "content": content})
        
        # Keep only last 20 messages to control costs
        if len(history) > 21:
            history = [history[0]] + history[-20:]
            self.conversations[user_id] = history

    def analyze_image(self, image_data, user_message, user_id):
        try:
            self.add_to_conversation(user_id, "user", f"[Image uploaded] {user_message}")
            
            response = openai.ChatCompletion.create(
                model="gpt-4-vision-preview",
                messages=[
                    {"role": "system", "content": self.system_message},
                    {
                        "role": "user", 
                        "content": [
                            {"type": "text", "text": user_message},
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}
                            }
                        ]
                    }
                ],
                max_tokens=1000
            )
            
            ai_response = response.choices[0].message.content
            self.add_to_conversation(user_id, "assistant", ai_response)
            return ai_response
            
        except Exception as e:
            return f"Sorry, I couldn't analyze the image. Error: {str(e)}"

    def get_text_response(self, user_message, user_id):
        try:
            self.add_to_conversation(user_id, "user", user_message)
            messages = self.get_conversation_history(user_id)
            
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=messages,
                max_tokens=800,
                temperature=0.7
            )
            
            ai_response = response.choices[0].message.content
            self.add_to_conversation(user_id, "assistant", ai_response)
            return ai_response
            
        except Exception as e:
            return f"Sorry, I'm having trouble right now. Error: {str(e)}"

bot = ZimChemBot()

@app.route('/', methods=['GET'])
def home():
    api_key_status = "✅ Connected" if os.getenv('OPENAI_API_KEY') else "❌ Missing API Key"
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>ZimChem WhatsApp Bot</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; background: #f5f5f5; }
            .container { background: white; padding: 30px; border-radius: 15px; box-shadow: 0 5px 15px rgba(0,0,0,0.1); }
            .header { color: #2c3e50; text-align: center; margin-bottom: 30px; }
            .status { color: #27ae60; font-weight: bold; }
            .error { color: #e74c3c; font-weight: bold; }
            .endpoint { background: #ecf0f1; padding: 20px; border-radius: 10px; margin: 15px 0; }
            .test-form { background: #e8f5e8; padding: 25px; border-radius: 10px; margin: 20px 0; }
            input[type="text"] { width: 70%; padding: 12px; margin: 5px; border: 2px solid #ddd; border-radius: 5px; }
            button { padding: 12px 25px; background: #3498db; color: white; border: none; border-radius: 5px; cursor: pointer; }
            button:hover { background: #2980b9; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🧪 ZimChem WhatsApp Bot</h1>
                <p>Status: <span class="status">Running</span></p>
                <p>OpenAI API: <span class="''' + ('status' if os.getenv('OPENAI_API_KEY') else 'error') + '''">''' + api_key_status + '''</span></p>
            </div>
            
            <div class="test-form">
                <h2>🧪 Quick Test</h2>
                <form action="/chat" method="post">
                    <input type="text" name="message" placeholder="Ask a chemistry question..." required>
                    <input type="hidden" name="user_id" value="web_test">
                    <button type="submit">Test Bot</button>
                </form>
            </div>
            
            <div class="endpoint">
                <h2>📱 API Endpoints</h2>
                <p><strong>Health Check:</strong> <code>GET /health</code></p>
                <p><strong>WhatsApp Integration:</strong> <code>POST /whatsapp</code></p>
                <p><strong>Active conversations:</strong> ''' + str(len(bot.conversations)) + '''</p>
            </div>
            
            <div class="endpoint">
                <h2>🔗 Test Links</h2>
                <p><a href="/health" target="_blank">Health Check</a></p>
                <p><a href="/test-api" target="_blank">API Test Page</a></p>
            </div>
        </div>
    </body>
    </html>
    ''')

@app.route('/test-api', methods=['GET'])
def test_api_page():
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>ZimChem API Test</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
            .test-form { background: #f8f9fa; padding: 20px; border-radius: 10px; margin: 20px 0; }
            input, button { padding: 10px; margin: 10px; border-radius: 5px; border: 1px solid #ddd; }
            button { background: #007bff; color: white; cursor: pointer; }
            .response { background: #e8f5e8; padding: 15px; border-radius: 5px; margin: 10px 0; }
        </style>
    </head>
    <body>
        <h1>🧪 ZimChem API Test</h1>
        
        <div class="test-form">
            <h3>Test the Bot API</h3>
            <input type="text" id="testMessage" placeholder="Ask a chemistry question..." value="What is H2O?">
            <button onclick="testAPI()">Send Question</button>
            <div id="response"></div>
        </div>
        
        <script>
            async function testAPI() {
                const message = document.getElementById('testMessage').value;
                const responseDiv = document.getElementById('response');
                
                responseDiv.innerHTML = '⏳ Asking ZimChem...';
                
                try {
                    const response = await fetch('/whatsapp', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            user_id: 'api_test',
                            message: message
                        })
                    });
                    
                    const data = await response.json();
                    
                    if (data.success) {
                        responseDiv.className = 'response';
                        responseDiv.innerHTML = '<strong>ZimChem:</strong> ' + data.response;
                    } else {
                        responseDiv.innerHTML = '❌ Error: ' + (data.error || 'Unknown error');
                    }
                } catch (error) {
                    responseDiv.innerHTML = '❌ Connection error: ' + error.message;
                }
            }
        </script>
    </body>
    </html>
    ''')

@app.route('/chat', methods=['POST'])
def chat():
    message = request.form.get('message') or request.json.get('message')
    user_id = request.form.get('user_id') or request.json.get('user_id', 'web_user')
    
    if not message:
        return jsonify({"error": "No message provided"}), 400
    
    response = bot.get_text_response(message, user_id)
    
    # Return HTML response for web form
    if request.form.get('message'):
        return render_template_string('''
        <!DOCTYPE html>
        <html>
        <head>
            <title>ZimChem Response</title>
            <style>
                body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
                .question { background: #e3f2fd; padding: 15px; border-radius: 5px; margin: 10px 0; }
                .response { background: #e8f5e8; padding: 15px; border-radius: 5px; margin: 10px 0; }
                .back { background: #3498db; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; }
            </style>
        </head>
        <body>
            <h1>🧪 ZimChem AI</h1>
            <div class="question"><strong>Question:</strong><br>''' + message + '''</div>
            <div class="response"><strong>Answer:</strong><br>''' + response + '''</div>
            <a href="/" class="back">Ask Another</a>
        </body>
        </html>
        ''')
    
    return jsonify({"response": response, "user_id": user_id})

@app.route('/whatsapp', methods=['POST', 'OPTIONS'])
def whatsapp_endpoint():
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        user_id = data.get('user_id', 'unknown')
        message = data.get('message', '')
        image_data = data.get('image')
        
        if not message and not image_data:
            return jsonify({"error": "No message or image provided"}), 400
        
        if image_data:
            response = bot.analyze_image(image_data, message or "Analyze this image", user_id)
        else:
            response = bot.get_text_response(message, user_id)
        
        return jsonify({
            "success": True,
            "response": response,
            "user_id": user_id,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({"error": str(e), "success": False}), 500

@app.route('/health')
def health():
    return jsonify({
        "status": "healthy",
        "openai_key": "present" if os.getenv('OPENAI_API_KEY') else "missing",
        "users": len(bot.conversations),
        "endpoints": ["/", "/chat", "/whatsapp", "/health"]
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"🧪 ZimChem Bot starting on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)

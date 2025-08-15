
from flask import Flask, request, jsonify, render_template_string
import openai
import os
import json
from datetime import datetime

app = Flask(__name__)

class ZimChemBot:
    def __init__(self):
        self.client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
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
            
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
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
            
            response = self.client.chat.completions.create(
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
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>ZimChem WhatsApp Bot</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
            .header { color: #2c3e50; text-align: center; }
            .status { color: #27ae60; font-weight: bold; }
            .endpoint { background: #ecf0f1; padding: 15px; border-radius: 5px; margin: 10px 0; }
            .test-form { background: #f8f9fa; padding: 20px; border-radius: 5px; }
            input[type="text"] { width: 70%; padding: 10px; margin: 5px; }
            button { padding: 10px 20px; background: #3498db; color: white; border: none; border-radius: 5px; }
            .response { background: #e8f5e8; padding: 15px; margin: 10px 0; border-radius: 5px; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🧪 ZimChem WhatsApp Bot</h1>
            <p>Status: <span class="status">Running</span></p>
            <p>Cost-optimized: GPT-3.5 for text, GPT-4o-mini for images</p>
        </div>
        
        <div class="test-form">
            <h2>Quick Test</h2>
            <form action="/chat" method="post">
                <input type="text" name="message" placeholder="Ask a chemistry question..." required>
                <input type="hidden" name="user_id" value="web_test">
                <button type="submit">Test Bot</button>
            </form>
        </div>
        
        <div class="endpoint">
            <h2>📱 WhatsApp Integration</h2>
            <p><strong>Main Endpoint:</strong> <code>POST /whatsapp</code></p>
            <p><strong>Active conversations:</strong> ''' + str(len(bot.conversations)) + '''</p>
        </div>
        
        <div class="endpoint">
            <h2>🔗 Quick Links</h2>
            <p><a href="/health">Health Check</a></p>
            <p><a href="/users">View Users</a></p>
        </div>
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
        <head><title>ZimChem Bot Response</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
            .question { background: #e3f2fd; padding: 15px; border-radius: 5px; margin: 10px 0; }
            .response { background: #e8f5e8; padding: 15px; border-radius: 5px; margin: 10px 0; }
            .back-btn { display: inline-block; padding: 10px 20px; background: #3498db; color: white; text-decoration: none; border-radius: 5px; }
        </style></head>
        <body>
            <h1>🧪 ZimChem AI Response</h1>
            <div class="question"><strong>Your Question:</strong><br>{{ question }}</div>
            <div class="response"><strong>ZimChem AI:</strong><br>{{ response }}</div>
            <a href="/" class="back-btn">Ask Another Question</a>
        </body>
        </html>
        ''', question=message, response=response)
    
    return jsonify({"response": response, "user_id": user_id})

@app.route('/whatsapp', methods=['POST'])
def whatsapp_endpoint():
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
            "timestamp": datetime.now().isoformat(),
            "model_used": "gpt-4o-mini" if image_data else "gpt-3.5-turbo"
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/users', methods=['GET'])
def get_users():
    user_stats = {}
    for user_id, messages in bot.conversations.items():
        user_stats[user_id] = {
            "message_count": len(messages) - 1,
            "last_message": messages[-1]["content"][:100] + "..." if len(messages) > 1 else "No messages"
        }
    
    return jsonify({
        "active_users": len(bot.conversations),
        "users": user_stats
    })

@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        "status": "healthy",
        "active_users": len(bot.conversations),
        "models": ["gpt-3.5-turbo", "gpt-4o-mini"]
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"🧪 ZimChem Bot starting on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)

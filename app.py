from flask import Flask, render_template, request, jsonify, send_file
from flask_socketio import SocketIO, emit
import ssl
import os
import base64
from datetime import datetime
import threading
import time
from openai import OpenAI
import config
from weather_art import generate_weather_prompt

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
socketio = SocketIO(app, cors_allowed_origins="*")

# Initialize OpenAI client
client = OpenAI(api_key=config.OPENAI_API_KEY)

# Current image state
current_image_path = config.CURRENT_IMAGE
generation_in_progress = False

def ensure_directories():
    """Ensure all required directories exist"""
    os.makedirs(config.IMAGES_DIR, exist_ok=True)
    os.makedirs('certs', exist_ok=True)

@app.route('/')
def display():
    """Main display page - shows current artwork"""
    return render_template('index.html')

@app.route('/control')
def control():
    """Control interface for phones"""
    return render_template('control.html')

@app.route('/current-image')
def get_current_image():
    """Serve the current display image"""
    if os.path.exists(current_image_path):
        return send_file(current_image_path, mimetype='image/png')
    return '', 404

@socketio.on('generate_image')
def handle_generate_image(data):
    """Handle image generation request from phone"""
    global generation_in_progress
    
    if generation_in_progress:
        emit('generation_status', {'status': 'busy', 'message': 'Generation already in progress'})
        return
    
    prompt = data.get('prompt', '')
    if not prompt:
        emit('generation_status', {'status': 'error', 'message': 'No prompt provided'})
        return
    
    # Add artistic style to prompt
    full_prompt = f"{prompt}, {config.DEFAULT_STYLE}"
    
    # Start generation in background
    thread = threading.Thread(target=generate_and_broadcast_image, args=(full_prompt,))
    thread.start()

def generate_and_broadcast_image(prompt):
    """Generate image with streaming and broadcast updates"""
    global generation_in_progress
    generation_in_progress = True
    
    try:
        socketio.emit('generation_status', {'status': 'starting', 'message': 'Starting image generation...'})
        
        # Create streaming request using the new API format
        stream = client.responses.create(
            model="gpt-4.1",
            input=prompt,
            stream=True,
            tools=[{"type": "image_generation", "partial_images": config.PARTIAL_IMAGES}],
        )
        
        # Process stream
        partial_count = 0
        final_image_data = None
        
        for event in stream:
            if event.type == "response.image_generation_call.partial_image":
                idx = event.partial_image_index
                image_base64 = event.partial_image_b64
                image_bytes = base64.b64decode(image_base64)
                
                # Save as current image
                with open(current_image_path, 'wb') as f:
                    f.write(image_bytes)
                
                # Save partial image
                partial_path = os.path.join(config.IMAGES_DIR, f'partial_{idx}.png')
                with open(partial_path, 'wb') as f:
                    f.write(image_bytes)
                
                # Broadcast update
                socketio.emit('image_update', {
                    'status': 'partial',
                    'partial_index': idx,
                    'image_data': f"data:image/png;base64,{image_base64}"
                })
                
                final_image_data = image_base64
                partial_count += 1
        
        # Save final image with timestamp
        if final_image_data:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            archive_path = os.path.join(config.IMAGES_DIR, f'art_{timestamp}.png')
            final_bytes = base64.b64decode(final_image_data)
            with open(archive_path, 'wb') as f:
                f.write(final_bytes)
        
        socketio.emit('generation_status', {
            'status': 'complete',
            'message': 'Image generation complete!',
            'image_url': '/current-image'
        })
        
    except Exception as e:
        socketio.emit('generation_status', {
            'status': 'error',
            'message': f'Error generating image: {str(e)}'
        })
    finally:
        generation_in_progress = False

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    emit('connected', {'message': 'Connected to art display'})

if __name__ == '__main__':
    ensure_directories()
    
    # SSL context for HTTPS
    context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
    context.load_cert_chain('certs/cert.pem', 'certs/key.pem')
    
    socketio.run(app, host=config.HOST, port=config.PORT, ssl_context=context)
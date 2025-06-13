from flask import Flask, render_template, request, jsonify, send_file
from flask_socketio import SocketIO, emit
import ssl
import os
import base64
from datetime import datetime
import threading
import time
import json
import shutil
from openai import OpenAI
import config
from weather_art import generate_weather_prompt
try:
    from PIL import Image, ImageDraw, ImageFont
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("PIL not available - will create simple placeholder")

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
socketio = SocketIO(app, cors_allowed_origins="*")

# Initialize OpenAI client
client = OpenAI(api_key=config.OPENAI_API_KEY)

# Current image state
current_image_path = config.CURRENT_IMAGE
generation_in_progress = False

# Image history tracking
IMAGE_HISTORY_FILE = os.path.join(config.BASE_DIR, 'image_history.json')
MAX_HISTORY = 50  # Keep track of last 50 images
CURRENT_POSITION_FILE = os.path.join(config.BASE_DIR, 'current_position.json')

def load_current_position():
    """Load current position in history"""
    if os.path.exists(CURRENT_POSITION_FILE):
        try:
            with open(CURRENT_POSITION_FILE, 'r') as f:
                data = json.load(f)
                return data.get('position', 0)
        except:
            return 0
    return 0

def save_current_position(position):
    """Save current position in history"""
    with open(CURRENT_POSITION_FILE, 'w') as f:
        json.dump({'position': position}, f)

def load_image_history():
    """Load image history from file"""
    if os.path.exists(IMAGE_HISTORY_FILE):
        try:
            with open(IMAGE_HISTORY_FILE, 'r') as f:
                return json.load(f)
        except:
            return []
    return []

def save_image_history(history):
    """Save image history to file"""
    with open(IMAGE_HISTORY_FILE, 'w') as f:
        json.dump(history, f)

def add_to_history(image_path):
    """Add image to history"""
    history = load_image_history()
    
    # Add new image to the front
    history.insert(0, {
        'path': image_path,
        'timestamp': datetime.now().isoformat()
    })
    
    # Keep only MAX_HISTORY items
    history = history[:MAX_HISTORY]
    
    save_image_history(history)
    
    # Reset position to 0 when new image is added
    save_current_position(0)
    
    return history

def get_previous_image():
    """Get the previous image from history"""
    history = load_image_history()
    current_pos = load_current_position()
    
    # Move to previous position
    new_pos = current_pos + 1
    
    # Check if we have a valid previous image
    if new_pos < len(history) and os.path.exists(history[new_pos]['path']):
        save_current_position(new_pos)
        return history[new_pos]['path']
    
    return None

def get_next_image():
    """Get the next image from history"""
    history = load_image_history()
    current_pos = load_current_position()
    
    # Move to next position
    new_pos = current_pos - 1
    
    # Check if we have a valid next image
    if new_pos >= 0 and new_pos < len(history) and os.path.exists(history[new_pos]['path']):
        save_current_position(new_pos)
        return history[new_pos]['path']
    
    return None

def create_placeholder_image():
    """Create a simple placeholder image"""
    if PIL_AVAILABLE:
        # Create a gradient background
        width, height = 1536, 1024
        img = Image.new('RGB', (width, height))
        draw = ImageDraw.Draw(img)
        
        # Create a gradient from dark blue to purple
        for y in range(height):
            r = int(30 + (y / height) * 50)
            g = int(40 + (y / height) * 30)
            b = int(80 + (y / height) * 100)
            draw.rectangle([(0, y), (width, y+1)], fill=(r, g, b))
        
        # Add some text
        try:
            # Try to use a nice font if available
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 60)
        except:
            # Fall back to default font
            font = ImageFont.load_default()
        
        text = "Art Display"
        text_bbox = draw.textbbox((0, 0), text, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        
        # Center the text
        x = (width - text_width) // 2
        y = (height - text_height) // 2
        
        # Draw text with shadow
        draw.text((x+3, y+3), text, fill=(0, 0, 0, 128), font=font)
        draw.text((x, y), text, fill=(255, 255, 255), font=font)
        
        # Add subtitle
        subtitle = "Initializing..."
        try:
            subtitle_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 30)
        except:
            subtitle_font = ImageFont.load_default()
        
        subtitle_bbox = draw.textbbox((0, 0), subtitle, font=subtitle_font)
        subtitle_width = subtitle_bbox[2] - subtitle_bbox[0]
        sx = (width - subtitle_width) // 2
        sy = y + text_height + 40
        
        draw.text((sx, sy), subtitle, fill=(200, 200, 200), font=subtitle_font)
        
        # Save the image
        img.save(current_image_path)
        print(f"Created placeholder image at {current_image_path}")
    else:
        # Create a simple 1x1 black pixel as fallback
        print("Creating minimal placeholder (PIL not available)")
        with open(current_image_path, 'wb') as f:
            # PNG header for a 1x1 black image
            f.write(b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x00\x00\x00\x00:~\x9bU\x00\x00\x00\x0bIDATx\x9cc\xf8\x00\x00\x00\x01\x00\x01UU\x86\x18\x00\x00\x00\x00IEND\xaeB`\x82')

def ensure_directories():
    """Ensure all required directories exist"""
    os.makedirs(config.IMAGES_DIR, exist_ok=True)
    os.makedirs('certs', exist_ok=True)
    
    # Create placeholder image if none exists
    if not os.path.exists(current_image_path):
        print("No current image found, creating placeholder...")
        create_placeholder_image()
        add_to_history(current_image_path)
        save_current_position(0)

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
    else:
        # If somehow the image doesn't exist, create it
        create_placeholder_image()
        return send_file(current_image_path, mimetype='image/png')

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

@socketio.on('previous_image')
def handle_previous_image():
    """Handle request to show previous image"""
    try:
        previous_path = get_previous_image()
        
        if previous_path and os.path.exists(previous_path):
            # Copy previous image to current
            shutil.copy2(previous_path, current_image_path)
            
            # Notify all clients
            socketio.emit('image_update', {
                'status': 'changed',
                'message': 'Previous image loaded'
            })
            
            emit('previous_status', {
                'status': 'success',
                'message': 'Previous image loaded'
            })
        else:
            emit('previous_status', {
                'status': 'error',
                'message': 'No previous image available'
            })
    except Exception as e:
        emit('previous_status', {
            'status': 'error',
            'message': f'Error loading previous image: {str(e)}'
        })

@socketio.on('next_image')
def handle_next_image():
    """Handle request to show next image"""
    try:
        next_path = get_next_image()
        
        if next_path and os.path.exists(next_path):
            # Copy next image to current
            shutil.copy2(next_path, current_image_path)
            
            # Notify all clients
            socketio.emit('image_update', {
                'status': 'changed',
                'message': 'Next image loaded'
            })
            
            emit('next_status', {
                'status': 'success',
                'message': 'Next image loaded'
            })
        else:
            emit('next_status', {
                'status': 'error',
                'message': 'No next image available'
            })
    except Exception as e:
        emit('next_status', {
            'status': 'error',
            'message': f'Error loading next image: {str(e)}'
        })

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
            tools=[{"type": "image_generation", 
                    "partial_images": config.PARTIAL_IMAGES,
                    "quality":"high",
                    "moderation":"low",
                    "size":"1536x1024"
                    }
                    ],
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
            
            # Add to history
            add_to_history(archive_path)
        
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

def generate_initial_art():
    """Generate initial weather-based art on startup"""
    print("Generating initial weather-based art...")
    try:
        from weather_art import generate_weather_art
        success, message = generate_weather_art()
        if success:
            # Add the weather art to history
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            archive_path = os.path.join(config.IMAGES_DIR, f'weather_art_{timestamp}.png')
            if os.path.exists(current_image_path):
                shutil.copy2(current_image_path, archive_path)
                add_to_history(archive_path)
                save_current_position(0)
        print(message)
    except Exception as e:
        print(f"Could not generate weather art: {e}")
        print("Placeholder image will be used instead")

if __name__ == '__main__':
    ensure_directories()
    
    # Try to generate initial art after a short delay
    # This runs in the background so the server can start immediately
    threading.Timer(5.0, generate_initial_art).start()
    
    # Create SSL context with modern TLS version
    context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    context.load_cert_chain('certs/cert.pem', 'certs/key.pem')
    
    # Run with production-ready settings
    socketio.run(app, 
                 host=config.HOST, 
                 port=config.PORT, 
                 ssl_context=context,
                 allow_unsafe_werkzeug=True)  # Required for newer Flask versions
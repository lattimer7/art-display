import requests
import json
from datetime import datetime
from openai import OpenAI
import config
import base64

client = OpenAI(api_key=config.OPENAI_API_KEY)

def get_nyc_weather():
    """Fetch current weather for NYC"""
    url = f"https://api.openweathermap.org/data/3.0/onecall?lat={config.NYC_LAT}&lon={config.NYC_LON}&units=imperial&appid={config.OPENWEATHER_API_KEY}"
    
    response = requests.get(url)
    return response.json()

def generate_weather_prompt(weather_data):
    """Use GPT-4.1 to create an artistic prompt from weather data"""
    today_weather = weather_data['daily'][0]
    weather_desc = today_weather['summary']
    temp = today_weather['temp']['day']
    feels_like = today_weather['feels_like']['day']
    humidity = today_weather['humidity']
    wind_speed = today_weather['wind_speed']
        
    system_prompt = """You are an artistic AI that creates beautiful, evocative image generation prompts based on weather conditions. 
    Create prompts that capture the mood and atmosphere of the weather in an abstract, artistic way.
    Focus on colors, textures, movements, and emotions that the weather evokes.
    Make the prompts suitable for creating stunning digital art."""
    
    user_prompt = f"""Create an artistic image generation prompt based on this NYC weather:
    - Weather: {weather_desc}
    - Temperature: {temp}°F (feels like {feels_like}°F)
    - Humidity: {humidity}%
    - Wind: {wind_speed} mph
    
    Create a single, cohesive prompt that would result in a beautiful, abstract artwork that captures the essence of this weather."""
    
    response = client.chat.completions.create(
        model="gpt-4.1",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.9
    )
    
    return response.choices[0].message.content

def generate_weather_art():
    """Main function to generate weather-based art"""
    try:
        # Get weather
        weather = get_nyc_weather()
        
        # Generate prompt
        art_prompt = generate_weather_prompt(weather)
        print(f"Generated prompt: {art_prompt}")
        
        # Add style suffix
        full_prompt = f"{art_prompt}, {config.DEFAULT_STYLE}"
        
        # Generate image using the new streaming API
        stream = client.responses.create(
            model="gpt-4.1",
            input=full_prompt,
            stream=True,
            tools=[{"type": "image_generation", "partial_images": config.PARTIAL_IMAGES}],
        )
        
        # Process stream and save the final image
        final_image_data = None
        for event in stream:
            if event.type == "response.image_generation_call.partial_image":
                idx = event.partial_image_index
                image_base64 = event.partial_image_b64
                image_bytes = base64.b64decode(image_base64)
                
                # Keep updating current image with each partial
                with open(config.CURRENT_IMAGE, 'wb') as f:
                    f.write(image_bytes)
                
                final_image_data = image_bytes
                print(f"Received partial image {idx}")
        
        # Archive final image with timestamp
        if final_image_data:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            archive_path = f"{config.IMAGES_DIR}/weather_art_{timestamp}.png"
            with open(archive_path, 'wb') as f:
                f.write(final_image_data)
        
        return True, "Weather art generated successfully"
        
    except Exception as e:
        return False, f"Error generating weather art: {str(e)}"

if __name__ == "__main__":
    success, message = generate_weather_art()
    print(message)
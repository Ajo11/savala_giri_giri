# backend/ring_counter/views.py

from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework import status
import google.generativeai as genai
from pydub import AudioSegment
import io
import base64
from PIL import Image, ImageEnhance

# --- SECURELY CONFIGURE GEMINI API ---
try:
    genai.configure(api_key=settings.GEMINI_API_KEY)
except AttributeError:
    print("CRITICAL ERROR: GEMINI_API_KEY not found in settings.py.")

# --- Audio Processing Function ---
def create_final_audio(ring_count):
    try:
        savala_sound = AudioSegment.from_mp3("savala.mp3")
        
        if ring_count == 0:
             # This case should no longer be hit, but is kept for safety
            final_audio = savala_sound
        else:
            giri_sound = AudioSegment.from_mp3("giri.mp3")
            repeated_giri = giri_sound * ring_count
            fast_giri = repeated_giri.speedup(playback_speed=1.2)
            final_audio = savala_sound + fast_giri
        
        buffer = io.BytesIO()
        final_audio.export(buffer, format="mp3")
        buffer.seek(0)
        return base64.b64encode(buffer.read()).decode('utf-8')
    except FileNotFoundError:
        print("Audio files 'savala.mp3' or 'giri.mp3' not found.")
        return None

# --- Main API View Using Gemini ---
class OnionProcessView(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):
        if 'file' not in request.data:
            return Response({"error": "No file provided"}, status=status.HTTP_400_BAD_REQUEST)
        
        file_obj = request.data['file']
        
        try:
            image = Image.open(file_obj)
            contrast_enhancer = ImageEnhance.Contrast(image)
            enhanced_image = contrast_enhancer.enhance(1.2)
            
            buffer = io.BytesIO()
            enhanced_image.save(buffer, format="PNG")
            enhanced_image_bytes = buffer.getvalue()
            
            image_parts = [{"mime_type": "image/png", "data": enhanced_image_bytes}]
            
            prompt = """
            You are a machine that only performs one function: counting onion rings from an image.
            Analyze the image. Count the number of distinct, concentric rings.
            Your entire response must be a single integer number and nothing else.
            DO NOT include words, explanations, or sentences. Example of a valid response: 12
            """
            
            model = genai.GenerativeModel('gemini-1.5-flash-latest')
            response = model.generate_content([prompt, *image_parts])
            
            ring_count = int(response.text.strip())

            # --- NEW: If the AI returns 0, default to 1 as per the new rule ---
            if ring_count == 0:
                ring_count = 1

            if ring_count >= 15:
                ring_count = ring_count // 2

        except Exception as e:
            print(f"Error during Gemini API call: {e}")
            # --- NEW: If there's an error, default the count to 1 ---
            ring_count = 1

        final_audio_data = create_final_audio(ring_count)
        
        response_data = {
            "ring_count": ring_count,
            "final_audio_data": final_audio_data,
            "rings": []
        }
        
        return Response(response_data, status=status.HTTP_200_OK)
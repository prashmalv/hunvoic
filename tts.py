from google.cloud import texttospeech
import os

def get_tts_client():
    return texttospeech.TextToSpeechClient.from_service_account_file(
        os.getenv('GOOGLE_TTS_KEY_JSON_PATH')
    )

def synthesize_text(text: str, out_path='/tmp/out.wav'):
    client = get_tts_client()
    input_text = texttospeech.SynthesisInput(text=text)
    voice = texttospeech.VoiceSelectionParams(language_code='en-IN', name='en-IN-Wavenet-D')
    audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.LINEAR16)
    response = client.synthesize_speech(input=input_text, voice=voice, audio_config=audio_config)
    with open(out_path, 'wb') as f:
        f.write(response.audio_content)
    return out_path

def synthesize_text_stream(text):
    path = synthesize_text(text)
    def iterfile():
        with open(path, 'rb') as f:
            data = f.read(4096)
            while data:
                yield data
                data = f.read(4096)
    return iterfile()

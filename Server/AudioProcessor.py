import os
import numpy as np
import librosa
import pickle
import soundfile as sf
from scipy.spatial.distance import cosine
import torch
import whisper
from silero_vad import load_silero_vad, read_audio, get_speech_timestamps
import warnings
import sys
from speechbrain.inference import EncoderClassifier
import asyncio
import websockets
import base64
import json

warnings.filterwarnings("ignore", category=UserWarning, module="whisper.transcribe")
warnings.filterwarnings("ignore", category=FutureWarning)

print("Loading models...")
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
whisper_model = whisper.load_model("small")

try:
    vad_model = load_silero_vad()
    print("Silero VAD model loaded successfully.")
except Exception as e:
    print(f"Failed to load Silero VAD model: {e}")
    sys.exit(1)

model = EncoderClassifier.from_hparams(source="speechbrain/spkrec-ecapa-voxceleb", run_opts={"device": device})

def convert_to_wav(input_path):
    try:
        if input_path.lower().endswith('.wav'):
            return input_path
        output_path = os.path.splitext(input_path)[0] + '.wav'
        audio, sr = librosa.load(input_path, sr=16000, mono=True)
        sf.write(output_path, audio, sr)
        return output_path
    except Exception as e:
        raise RuntimeError(f"Error converting to WAV: {e}")

def extract_embedding(file_path, speaker_name, embedding_file='embeddings.pkl'):
    try:
        wav_path = convert_to_wav(file_path)
        audio, sr = librosa.load(wav_path, sr=16000)
        audio_tensor = torch.from_numpy(audio).unsqueeze(0)
        embedding = model.encode_batch(audio_tensor).squeeze(0).detach().cpu().numpy().flatten()

        # Load existing embeddings if the file exists
        embeddings = {}
        if os.path.exists(embedding_file):
            with open(embedding_file, 'rb') as f:
                embeddings = pickle.load(f)

        # Save with formatted name
        embedding_key = f"{speaker_name}_embeddings"
        embeddings[embedding_key] = embedding

        with open(embedding_file, 'wb') as f:
            pickle.dump(embeddings, f)

        print(f"Successfully extracted and stored embedding as '{embedding_key}'")
        return {"message": f"Embedding extracted and stored as '{embedding_key}'"}
    except Exception as e:
        raise RuntimeError(f"Error extracting embedding: {e}")


def load_embeddings(embedding_file='embeddings.pkl'):
    if not os.path.exists(embedding_file):
        raise FileNotFoundError("No embeddings found. Please run 'extract' first.")
    with open(embedding_file, 'rb') as f:
        return pickle.load(f)
    
def get_embeddings(embedding_file='embeddings.pkl'):
    try:
        if not os.path.exists(embedding_file):
            return {"error": "No embeddings found."}
        with open(embedding_file, 'rb') as f:
            embeddings = pickle.load(f)
        return {"embeddings": list(embeddings.keys())}
    except Exception as e:
        return {"error": str(e)}


def extract_embedding_without_saving(file_path):
    try:
        wav_path = convert_to_wav(file_path)
        audio, sr = librosa.load(wav_path, sr=16000)
        audio_tensor = torch.from_numpy(audio).unsqueeze(0)
        embedding = model.encode_batch(audio_tensor).squeeze(0).detach().cpu().numpy().flatten()
        return embedding
    except Exception as e:
        raise RuntimeError(f"Error extracting embedding without saving: {e}")

def identify_speaker(input_path):
    try:
        # Load existing embeddings
        embeddings = load_embeddings()

        # Extract input embedding without saving
        input_embedding = extract_embedding_without_saving(input_path)

        # Perform speaker identification using cosine similarity
        similarities = {name: 1 - cosine(input_embedding, emb) for name, emb in embeddings.items()}
        best_match = max(similarities, key=similarities.get)

        result = {
            "speaker": best_match,
            "confidence": float(similarities[best_match])
        }
        print(f"Identified Speaker: {best_match} (Confidence: {similarities[best_match]:.2f})")
        return result
    except Exception as e:
        print(f"Error identifying speaker: {e}")
        return {"error": str(e)}


def transcribe_audio(segment_audio):
    try:
        segment_audio = np.array(segment_audio, dtype=np.float32)
        result = whisper_model.transcribe(segment_audio)
        return result.get('text', '')
    except Exception as e:
        raise RuntimeError(f"Error during transcription: {e}")

async def diarize_audio(input_path, websocket):
    try:
        wav_path = convert_to_wav(input_path)
        wav = read_audio(wav_path, sampling_rate=16000)
        speech_timestamps = get_speech_timestamps(wav, vad_model, return_seconds=True, min_speech_duration_ms=300, min_silence_duration_ms=500)
        embeddings = load_embeddings()

        for i, segment in enumerate(speech_timestamps):
            start_time, end_time = segment['start'], segment['end']
            segment_audio = wav[int(start_time * 16000): int(end_time * 16000)]
            segment_audio = np.array(segment_audio, dtype=np.float32)
            audio_tensor = torch.from_numpy(segment_audio).unsqueeze(0)
            segment_embedding = model.encode_batch(audio_tensor).squeeze(0).detach().cpu().numpy().flatten()

            # Identify speaker
            similarities = {name: 1 - cosine(segment_embedding, emb) for name, emb in embeddings.items()}
            best_match = max(similarities, key=similarities.get)
            transcription = transcribe_audio(segment_audio)

            # Send results immediately
            result = {
                "start_time": float(start_time),
                "end_time": float(end_time),
                "speaker": best_match,
                "confidence": float(similarities[best_match]),
                "transcription": transcription
            }
            print(f"Segment {start_time:.2f}s - {end_time:.2f}s | Speaker: {best_match} (Confidence: {similarities[best_match]:.2f}) | Transcription: {transcription}")

            try:
                await websocket.send(json.dumps(result))
            except websockets.exceptions.ConnectionClosedError as e:
                print(f"Connection closed while sending data: {e}")
                break
            await asyncio.sleep(0)  # Prevent blocking
    except Exception as e:
        print(f"Error during diarization: {e}")

async def handle_message(websocket, path=None):
    print("Client connected")
    async for message in websocket:
        try:
            data = json.loads(message)
            print(f"Received Action: {data['action']}")

            if data['action'] == 'view_embeddings':
                print("Fetching embeddings...")
                result = get_embeddings()
                await websocket.send(json.dumps(result))
                continue

            # Validate audioData only for actions that need it
            if data['action'] in ['identify', 'diarize', 'extract']:
                if 'audioData' not in data:
                    await websocket.send(json.dumps({"error": "'audioData' is required for this action."}))
                    continue

                audio_data = base64.b64decode(data['audioData'])
                file_path = 'received_audio.wav'
                with open(file_path, 'wb') as f:
                    f.write(audio_data)
                print(f"Audio saved to {file_path}")

            if data['action'] == 'identify':
                print("Identifying speaker...")
                result = identify_speaker(file_path)
                await websocket.send(json.dumps({"message": "Speaker identification complete.", "result": result}))

            elif data['action'] == 'diarize':
                print("Performing diarization...")
                await diarize_audio(file_path, websocket)

            elif data['action'] == 'extract':
                if 'speakerName' not in data or not data['speakerName'].strip():
                    await websocket.send(json.dumps({"error": "Speaker name is required for extraction."}))
                else:
                    print(f"Extracting speaker embedding for {data['speakerName']}...")
                    result = extract_embedding(file_path, data['speakerName'])
                    await websocket.send(json.dumps({"message": result["message"]}))
            else:
                print("Unknown action received.")
                await websocket.send(json.dumps({"error": "Unknown action."}))

        except Exception as e:
            print(f"Error: {e}")
            await websocket.send(json.dumps({"error": str(e)}))


async def start_server():
    print("Python WebSocket server started on ws://localhost:5001")
    server = await websockets.serve(
        handle_message, 
        "localhost", 
        5001,
        max_size=20 * 1024 * 1024,
        ping_interval=30,  
        ping_timeout=60    
    )
    await server.wait_closed()



asyncio.run(start_server())

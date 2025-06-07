# Real-Time Voice Transcription & Speaker Identification System with Blockchain Integration

## Overview

This project is a full-stack application that captures live audio, performs real-time speech-to-text transcription, identifies speakers, and stores the final transcript securely on the blockchain. It ensures tamper-proof, transparent, and auditable meeting records, ideal for industries requiring high data integrity such as healthcare, legal, finance, and logistics.

---

## Features

- **Speaker Management**  
  Upload reference audio samples to extract and store speaker embeddings for identification.

- **Real-Time Recording & Transcription**  
  Stream live audio, detect voice activity, and transcribe speech in real time using advanced AI models.

- **Speaker Identification**  
  Match speaker voice segments against stored embeddings to label transcripts accurately.

- **Blockchain Integration**  
  Create and manage meetings via smart contracts, storing transcripts and metadata on-chain for security and immutability.

- **Secure Storage**  
  Optionally store encrypted raw audio files off-chain using IPFS/Filecoin.

---

## Application Flow

1. **Speaker Management**  
   Upload audio → Extract embeddings (using `librosa` & `speechbrain`) → Store embeddings.

2. **Start Meeting**  
   Trigger smart contract → Create meeting on blockchain → Receive meeting ID → Select participants.

3. **Fetch Meeting Details**  
   Retrieve meeting info using meeting ID from the blockchain.

4. **Live Audio Recording**  
   Stream audio via WebSocket → Detect voice activity (`silero_vad`) → Transcribe (`whisper`).

5. **Speaker Identification**  
   Match segments using cosine similarity → Label transcripts.

6. **On-Chain Storage**  
   Store final transcripts, speaker info, timestamps, and meeting metadata on blockchain via smart contracts.

---

## Tech Stack & Libraries

- **Frontend:** React.js  
- **Backend:** Node.js, Python  
- **Blockchain:** Solidity (Ethereum smart contracts)  
- **Storage:** IPFS/Filecoin (for encrypted audio files)  
- **AI & Audio Processing Libraries:**  
  - `librosa` (audio analysis)  
  - `speechbrain` (speaker embeddings)  
  - `whisper` (speech transcription)  
  - `silero_vad` (voice activity detection)  
  - `torch` (PyTorch framework)  
  - `EncoderClassifier` (for speaker recognition)

---


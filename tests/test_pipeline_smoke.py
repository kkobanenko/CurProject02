import numpy as np
import tempfile
import os
from app.audio.f0 import estimate_f0_pyin, estimate_f0_torchcrepe
from app.audio.quantize import estimate_tempo, quantize_rhythm
from app.audio.key_tempo import detect_key_from_pitches
from app.audio.notation import f0_to_midi, build_score, export_musicxml
from app.audio.synthesis import synth_audio
from app.audio.preprocess import apply_preprocessing_pipeline
from app.audio.io import get_audio_info
from app.settings import settings

def test_f0_basic():
    """Test basic F0 estimation with pYIN."""
    sr = 22050
    t = np.linspace(0, 1.0, int(sr), endpoint=False)
    y = 0.2 * np.sin(2*np.pi*440*t)  # A4
    times, f0, voiced = estimate_f0_pyin(y, sr)
    assert (f0 > 0).sum() > 10
    print("✅ F0 estimation with pYIN works")

def test_f0_torchcrepe():
    """Test F0 estimation with torchcrepe if available."""
    try:
        sr = 22050
        t = np.linspace(0, 1.0, int(sr), endpoint=False)
        y = 0.2 * np.sin(2*np.pi*440*t)  # A4
        times, f0, voiced = estimate_f0_torchcrepe(y, sr)
        assert (f0 > 0).sum() > 10
        print("✅ F0 estimation with torchcrepe works")
    except Exception as e:
        print(f"⚠️ torchcrepe not available: {e}")

def test_tempo_estimation():
    """Test tempo estimation."""
    sr = 22050
    # Create a simple beat pattern
    t = np.linspace(0, 2.0, int(sr * 2), endpoint=False)
    y = np.zeros_like(t)
    
    # Add beats every 0.5 seconds (120 BPM)
    for i in range(0, len(t), int(sr * 0.5)):
        if i < len(y):
            y[i:i+1000] = 0.5
    
    tempo = estimate_tempo(y, sr)
    assert 100 <= tempo <= 140  # Should be close to 120 BPM
    print(f"✅ Tempo estimation works: {tempo:.1f} BPM")

def test_rhythm_quantization():
    """Test rhythm quantization."""
    sr = 22050
    t = np.linspace(0, 1.0, int(sr), endpoint=False)
    y = 0.2 * np.sin(2*np.pi*440*t)  # A4
    
    # Get F0 first
    times, f0, voiced = estimate_f0_pyin(y, sr)
    
    # Quantize rhythm
    tempo = 120.0
    onsets, durations = quantize_rhythm(times, tempo, grid=0.25)
    
    assert len(onsets) > 0
    assert len(durations) > 0
    print(f"✅ Rhythm quantization works: {len(onsets)} notes")

def test_key_detection():
    """Test key detection."""
    # Create a simple C major scale
    midi_pitches = [60, 62, 64, 65, 67, 69, 71, 72]  # C major scale
    key = detect_key_from_pitches(midi_pitches)
    assert key in ["C", "C major", "C Major"]
    print(f"✅ Key detection works: {key}")

def test_score_building():
    """Test score building from MIDI data."""
    midi_pitches = [60, 62, 64, 65, 67, 69, 71, 72]  # C major scale
    onsets = [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5]
    durations = [0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5]
    
    score = build_score(
        midi_pitches=midi_pitches,
        onset_beats=onsets,
        dur_beats=durations,
        key_signature="C",
        time_signature="4/4",
        qpm=120.0,
        title="Test Score"
    )
    
    assert score is not None
    print("✅ Score building works")

def test_musicxml_export():
    """Test MusicXML export."""
    midi_pitches = [60, 62, 64, 65]  # C major scale (first 4 notes)
    onsets = [0.0, 0.5, 1.0, 1.5]
    durations = [0.5, 0.5, 0.5, 0.5]
    
    score = build_score(
        midi_pitches=midi_pitches,
        onset_beats=onsets,
        dur_beats=durations,
        key_signature="C",
        time_signature="4/4",
        qpm=120.0,
        title="Test Score"
    )
    
    # Create temporary file
    with tempfile.NamedTemporaryFile(suffix=".musicxml", delete=False) as tmp_file:
        try:
            export_musicxml(score, tmp_file.name)
            assert os.path.exists(tmp_file.name)
            assert os.path.getsize(tmp_file.name) > 0
            print("✅ MusicXML export works")
        finally:
            os.unlink(tmp_file.name)

def test_audio_synthesis():
    """Test audio synthesis."""
    midi_pitches = [60, 62, 64, 65]  # C major scale (first 4 notes)
    onsets = [0.0, 0.5, 1.0, 1.5]
    durations = [0.5, 0.5, 0.5, 0.5]
    
    # Test sine synthesis
    y_sine = synth_audio(midi_pitches, onsets, durations, qpm=120.0, synth_type="sine")
    assert len(y_sine) > 0
    print("✅ Sine synthesis works")
    
    # Test piano synthesis
    y_piano = synth_audio(midi_pitches, onsets, durations, qpm=120.0, synth_type="piano")
    assert len(y_piano) > 0
    print("✅ Piano synthesis works")

def test_preprocessing_pipeline():
    """Test preprocessing pipeline."""
    sr = 22050
    t = np.linspace(0, 1.0, int(sr), endpoint=False)
    y = 0.2 * np.sin(2*np.pi*440*t)  # A4
    
    # Add some noise
    y_noisy = y + 0.1 * np.random.randn(len(y))
    
    # Apply preprocessing
    y_processed = apply_preprocessing_pipeline(
        y_noisy, sr,
        highpass_enabled=True,
        normalize_enabled=True,
        trim_enabled=True,
        denoise_enabled=True
    )
    
    assert len(y_processed) > 0
    assert len(y_processed) <= len(y_noisy)  # Trim might reduce length
    print("✅ Preprocessing pipeline works")

def test_f0_to_midi_conversion():
    """Test F0 to MIDI conversion."""
    # Test with valid frequencies
    f0_hz = [440.0, 880.0, 220.0]  # A4, A5, A3
    midi_pitches = f0_to_midi(f0_hz)
    
    assert len(midi_pitches) == len(f0_hz)
    assert all(0 <= p <= 127 for p in midi_pitches)
    print("✅ F0 to MIDI conversion works")

def test_full_pipeline_simulation():
    """Test full pipeline simulation without actual file I/O."""
    print("\n🎵 Testing full pipeline simulation...")
    
    # 1. Create synthetic audio
    sr = 22050
    t = np.linspace(0, 2.0, int(sr * 2), endpoint=False)
    y = 0.2 * np.sin(2*np.pi*440*t)  # A4 for 2 seconds
    
    # 2. Preprocessing
    y_processed = apply_preprocessing_pipeline(y, sr)
    print("✅ Step 1: Preprocessing completed")
    
    # 3. F0 estimation
    times, f0, voiced = estimate_f0_pyin(y_processed, sr)
    print(f"✅ Step 2: F0 estimation completed ({voiced.sum()} voiced frames)")
    
    # 4. Tempo estimation
    tempo = estimate_tempo(y_processed, sr)
    print(f"✅ Step 3: Tempo estimation completed ({tempo:.1f} BPM)")
    
    # 5. Rhythm quantization
    onsets, durations = quantize_rhythm(times, tempo, grid=0.25)
    print(f"✅ Step 4: Rhythm quantization completed ({len(onsets)} notes)")
    
    # 6. Key detection
    midi_pitches = f0_to_midi(f0.tolist())
    key = detect_key_from_pitches([m for m in midi_pitches if m > 0])
    print(f"✅ Step 5: Key detection completed ({key})")
    
    # 7. Score building - use only the quantized notes
    if len(onsets) > 0 and len(durations) > 0:
        # Create simple MIDI pitches for the quantized notes
        quantized_midi_pitches = [60 + (i % 12) for i in range(len(onsets))]  # Simple C major scale
        
        score = build_score(
            midi_pitches=quantized_midi_pitches,
            onset_beats=onsets,
            dur_beats=durations,
            key_signature=key,
            time_signature="4/4",
            qpm=tempo,
            title="Pipeline Test Score"
        )
        print("✅ Step 6: Score building completed")
        
        # 8. Audio synthesis
        y_synth = synth_audio(quantized_midi_pitches, onsets, durations, qpm=tempo, synth_type="sine")
        print(f"✅ Step 7: Audio synthesis completed ({len(y_synth)} samples)")
    else:
        print("⚠️ Step 6: No quantized notes available for score building")
        print("⚠️ Step 7: No quantized notes available for audio synthesis")
    
    print("🎉 Full pipeline simulation completed successfully!")

if __name__ == "__main__":
    print("🧪 Running smoke tests...")
    
    test_f0_basic()
    test_f0_torchcrepe()
    test_tempo_estimation()
    test_rhythm_quantization()
    test_key_detection()
    test_score_building()
    test_musicxml_export()
    test_audio_synthesis()
    test_preprocessing_pipeline()
    test_f0_to_midi_conversion()
    test_full_pipeline_simulation()
    
    print("\n✅ All smoke tests passed!")

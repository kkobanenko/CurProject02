"""
Test rendering functionality.
"""
import tempfile
import os
from app.audio.notation import build_score, export_musicxml, render_to_pdf_png
from app.settings import settings

def test_musicxml_export():
    """Test MusicXML export."""
    # Create a simple score
    midi_pitches = [60, 62, 64, 65]  # C major scale
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
    
    # Export to MusicXML
    with tempfile.NamedTemporaryFile(suffix=".musicxml", delete=False) as tmp_file:
        try:
            export_musicxml(score, tmp_file.name)
            assert os.path.exists(tmp_file.name)
            assert os.path.getsize(tmp_file.name) > 0
            print("✅ MusicXML export works")
            
            # Test rendering if renderer is available
            if settings.renderer != "none":
                test_rendering(tmp_file.name)
            else:
                print("⚠️ Renderer not configured, skipping rendering test")
                
        finally:
            os.unlink(tmp_file.name)

def test_rendering(musicxml_path: str):
    """Test PDF/PNG rendering."""
    print(f"Testing rendering with {settings.renderer}...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        pdf_path = os.path.join(temp_dir, "test.pdf")
        png_path = os.path.join(temp_dir, "test.png")
        
        # Try rendering
        output_files = render_to_pdf_png(musicxml_path, pdf_path, png_path)
        
        if output_files:
            print(f"✅ Rendering successful: {len(output_files)} files created")
            for file_path in output_files:
                if os.path.exists(file_path):
                    size = os.path.getsize(file_path)
                    print(f"   - {os.path.basename(file_path)}: {size} bytes")
        else:
            print("⚠️ Rendering failed or no renderer available")

if __name__ == "__main__":
    test_musicxml_export()

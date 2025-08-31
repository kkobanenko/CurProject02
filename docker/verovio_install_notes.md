# Verovio Installation Notes

## Option 1: Package Manager (Recommended)
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install verovio

# CentOS/RHEL
sudo yum install verovio
```

## Option 2: Build from Source
```bash
# Install dependencies
sudo apt-get install cmake build-essential libpugixml-dev libcurl4-openssl-dev

# Clone and build
git clone https://github.com/rism-digital/verovio.git
cd verovio
mkdir build && cd build
cmake ..
make -j$(nproc)
sudo make install
```

## Option 3: Docker
```dockerfile
# Add to Dockerfile
RUN apt-get update && apt-get install -y verovio
```

## Usage
```bash
# Convert MusicXML to PNG
verovio --format png --output score.png input.musicxml

# Convert MusicXML to PDF
verovio --format pdf --output score.pdf input.musicxml
```

## Notes
- Verovio is a lightweight alternative to MuseScore
- Supports MusicXML 3.1 and MEI formats
- Outputs high-quality vector graphics
- No GUI dependencies required

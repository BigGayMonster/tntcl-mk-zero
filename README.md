# Tri-Lobe Hydraulic Tentacle Generator

A parametric Blender Python script that generates bio-inspired, 3-lobe hydraulic tentacles for silicone casting and 3D printing.

## 🎯 Project Overview

This project creates a squid-inspired hydraulic tentacle with three internal lobes that converge smoothly at the tip. The tentacle is designed for soft robotics applications using silicone casting with 3D-printed cores.

## 🔧 Requirements

- **Blender 4.4.3** (tested version)
- Linux environment (tested on Arch Linux)
- Python 3.x (included with Blender)

## 📁 Project Files

- `render_tentacle_cli.py` - Main Blender Python script (CLI-based generation)
- `run_tentacle_cli.sh` - Execution wrapper script
- `tri_lobe_tentacle_generator.py` - Alternative implementation (GUI-based)
- `.gitignore` - Excludes output directory

## 🚀 Quick Start

```bash
# Generate tentacle (requires Blender in PATH)
./run_tentacle_cli.sh
```

## 📦 Output Files

The generator creates the following files in the `out/` directory:

- `tentacle_camera_view.png` - High-quality rendered preview
- `tentacle_complete.blend` - Full Blender scene file
- `tentacle_body.stl` - Main tentacle for 3D printing
- `tentacle_bladders.stl` - Internal bladder cores
- `tentacle_channels.stl` - Vertical hydraulic channels

## 🏗️ Technical Architecture

### Final Design Solution

After multiple iterations, the final design uses:

1. **Unified Mesh Approach** - Single seamless tentacle body created via mathematical deformation
2. **Subtle Tri-Lobe Effect** - Sine wave deformation creates 3-fold symmetry without visible seams
3. **Natural Convergence** - Effect diminishes smoothly toward the tip for organic squid-like appearance
4. **Hydraulic System** - Internal bladders and channels aligned with lobe positions

### Key Parameters

```python
tentacle_len_mm = 150.0      # Total length (mm)
base_radius_mm = 25.0        # Base radius (mm)
tip_radius_mm = 8.0          # Tip radius (mm)
bladder_spacing_mm = 15.0    # Bladder spacing (mm)
channel_radius_mm = 2.0      # Channel radius (mm)
```

## 🔄 Design Evolution

### Problem: Visible Lobe Seams
Initial attempts used separate cone objects merged together, creating visible ridges and seams that looked artificial rather than bio-inspired.

### Solution: Mathematical Deformation
The final approach creates a single tapered cylinder and uses bmesh operations to apply subtle tri-lobe characteristics through vertex manipulation:

```python
# Create subtle tri-lobe effect that diminishes toward tip
lobe_effect = math.sin(angle * 3) * 0.15 * (1 - z_ratio**2)
```

### Result: Seamless Convergence
The tentacle now has a smooth, organic shape with natural convergence at the tip, eliminating artificial-looking seams.

## 🛠️ CLI vs GUI Implementation

### CLI Implementation (`render_tentacle_cli.py`)
- **Background execution** - No GUI required
- **Automatic rendering** - Generates PNG preview
- **Multi-format export** - STL files for 3D printing
- **Robust error handling** - Fallback export methods

### GUI Implementation (`tri_lobe_tentacle_generator.py`)
- **Interactive development** - Real-time viewport feedback
- **Manual control** - Step-by-step generation
- **Debug modes** - Testing and validation options

## 🎨 Rendering Features

- **Glass-like materials** with Fresnel effects for edge definition
- **Enhanced transparency** (40% opacity) showing internal structures
- **Four-point soft lighting** eliminating harsh shadows
- **Professional camera positioning** with track-to constraints

## 💾 Installation

### Arch Linux
```bash
sudo pacman -S blender
```

### Other Linux Distributions
Download Blender 4.4.3+ from [blender.org](https://www.blender.org/download/)

## 🔧 Customization

Edit parameters in `render_tentacle_cli.py`:

```python
# Tentacle geometry
tentacle_len_mm = 150.0        # Adjust length
base_radius_mm = 25.0          # Adjust base size
tip_radius_mm = 8.0            # Adjust tip size

# Bladder system
bladder_spacing_mm = 15.0      # Adjust density
channel_radius_mm = 2.0        # Adjust channel size
```

## 📊 Performance

- **Generation time**: ~15 seconds
- **Render time**: ~60 seconds (1920x1080, 64 samples)
- **STL export**: <1 second per file
- **File sizes**:
  - Main tentacle: ~9KB
  - Bladders: ~1.1MB
  - Channels: ~19KB

## 🎯 Use Cases

- **Soft robotics research** - Hydraulic tentacle actuators
- **3D printing** - Silicone casting molds
- **Scientific visualization** - Bio-inspired designs
- **Educational tools** - Parametric modeling examples

## 🤝 Contributing

This project evolved through iterative refinement focusing on:
1. Eliminating visible seams in merged geometry
2. Creating natural bio-inspired convergence
3. Maintaining hydraulic functionality
4. Ensuring 3D printability

---

*Generated tentacles should be checked for manifold geometry before 3D printing. Use the included PNG preview to verify visual correctness.*

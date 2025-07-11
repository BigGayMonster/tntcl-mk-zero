#!/bin/bash

echo "=== Running Tentacle Generator in CLI Mode ==="
echo "This will generate a tentacle using Blender in background mode"
echo "Output files will be saved to the 'out' directory"
echo ""

# Check if Blender is installed
if ! command -v blender &> /dev/null; then
    echo "Error: Blender is not installed or not in PATH"
    echo "Install with: sudo pacman -S blender"
    exit 1
fi

# Create output directory if it doesn't exist
mkdir -p out

# Run Blender in background mode with our script
echo "Running Blender CLI tentacle generator..."

# Capture both output and exit code
BLENDER_OUTPUT=$(blender --background --python render_tentacle_cli.py 2>&1)
BLENDER_EXIT_CODE=$?

# Print the output
echo "$BLENDER_OUTPUT"

# Check if Blender succeeded
if [ $BLENDER_EXIT_CODE -ne 0 ]; then
    echo "Generation failed! Check output above for errors."
    exit 1
fi

echo ""
echo "=== Generation Complete ==="
echo "Check the 'out' directory for:"
echo "  - tentacle_camera_view.png (rendered image)"
echo "  - tentacle_complete.blend (Blender scene file)"
echo "  - tentacle_body.stl (3D printable tentacle)"
echo "  - tentacle_bladders.stl (internal bladders)"
echo "  - tentacle_channels.stl (connecting channels)"
echo ""
echo "You can view the PNG to see if the geometry looks correct!"
echo "Open the .blend file in Blender to inspect and edit the full scene!"

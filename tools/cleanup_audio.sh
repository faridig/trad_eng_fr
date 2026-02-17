#!/bin/bash
# tools/cleanup_audio.sh
# Purge PulseAudio/PipeWire modules related to VoxTransync

echo "🧹 Cleaning up VoxTransync audio modules..."

# List all modules and find those containing the pattern 'vox'
# We use a pattern matching to catch vox-transync-mic, vox-transync-mic-output and loopbacks
MODULES=$(pactl list short modules 2>/dev/null | grep "vox" | cut -f1)

if [ -z "$MODULES" ]; then
    echo "✅ No 'vox' modules found."
else
    for ID in $MODULES; do
        echo "🚿 Unloading module $ID..."
        pactl unload-module "$ID" 2>/dev/null
    done
    echo "✨ Cleanup complete."
fi

# Optional: also clean up any orphaned loopbacks that might be stuck
# based on common patterns if 'vox' grep wasn't enough, but 'vox' should cover it
# as we name our sinks/sources with it.

# Stabilization delay
sleep 1.0

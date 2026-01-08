# Emotiv Hardware Setup Guide

This guide covers setting up your Emotiv EEG headset for use with BCIpyDummies.

## Supported Devices

BCIpyDummies works with any Emotiv headset supported by the Cortex API:

| Device | Channels | Connection | Notes |
|--------|----------|------------|-------|
| EPOC X | 14 | USB Dongle | Best for mental commands |
| EPOC+ | 14 | Bluetooth/USB | Good balance of quality and portability |
| Insight | 5 | Bluetooth | Lightweight, fewer channels |
| EPOC Flex | 32 | USB | Research-grade |

## Initial Setup

### 1. Create Emotiv Account

1. Go to [emotiv.com](https://www.emotiv.com)
2. Create a free account
3. Verify your email

### 2. Install Emotiv Software

Download and install:

1. **Emotiv Cortex** - Background service that handles device communication
   - Download from [emotiv.com/emotiv-cortex](https://www.emotiv.com/emotiv-cortex/)

2. **EmotivBCI** (optional but recommended) - For training mental commands
   - Available from Emotiv website or app stores

### 3. Pair Your Headset

**USB Dongle Method (EPOC X, EPOC+):**
1. Insert the USB dongle
2. Turn on the headset
3. Open Emotiv Cortex
4. Wait for automatic pairing

**Bluetooth Method (Insight, EPOC+):**
1. Turn on the headset
2. Enable Bluetooth on your computer
3. Open Emotiv Cortex
4. Follow pairing prompts

## Training Mental Commands

Mental commands require training in the EmotivBCI app before BCIpyDummies can use them.

### Required Training

| Command | Description | Recommended Training |
|---------|-------------|---------------------|
| `neutral` | Relaxed state | 30+ seconds, multiple sessions |
| `left` | Think "left" | 8+ training samples |
| `right` | Think "right" | 8+ training samples |
| `lift` | Think "up/lift" | 8+ training samples |

### Training Tips

1. **Start with Neutral**
   - Train neutral state first
   - Keep your mind calm and relaxed
   - Train in the same environment you'll use the headset

2. **Consistent Mental Imagery**
   - Use the same mental image each time
   - For "left": imagine your hand moving left, or visualize an arrow pointing left
   - Be consistent across training sessions

3. **Short Sessions**
   - Train for 10-15 minutes at a time
   - Take breaks to avoid fatigue
   - Quality over quantity

4. **Good Contact Quality**
   - Ensure all sensors show green in Cortex
   - Use saline solution on sensors if needed
   - Hair should not block sensors

## Optimizing Signal Quality

### Sensor Placement

1. Position headset according to the device manual
2. Ensure sensors sit flat against scalp
3. Move hair away from sensor areas
4. Apply saline to felt sensors (EPOC devices)

### Contact Quality Indicators

In Emotiv Cortex:
- **Green**: Good contact
- **Orange**: Acceptable, may have noise
- **Red**: Poor contact, reposition
- **Black**: No contact

**Target**: All sensors green before starting BCIpyDummies.

### Environment Tips

- Minimize electrical interference (move away from monitors)
- Avoid fluorescent lighting
- Stay still during use
- Avoid excessive jaw movement or eye blinks

## Cortex API Configuration

### Verify Cortex is Running

1. Open Emotiv Cortex
2. Look for "Cortex running" status
3. Verify headset shows "Connected"

### Default Connection

BCIpyDummies connects to:
```
wss://127.0.0.1:6868
```

This is the default Cortex WebSocket endpoint. Ensure no firewall blocks local connections.

### Getting API Credentials

1. Go to [emotiv.com/developer](https://www.emotiv.com/developer/)
2. Sign in with your Emotiv account
3. Click "Create Application"
4. Fill in application details:
   - Name: BCIpyDummies
   - Type: Desktop
5. Copy your Client ID and Client Secret

## License Considerations

Emotiv offers different license tiers:

| Feature | Free | Pro | Enterprise |
|---------|------|-----|------------|
| Mental Commands | Limited | Full | Full |
| Raw EEG Data | No | Yes | Yes |
| Multiple Headsets | No | Yes | Yes |

BCIpyDummies uses the mental command stream, which works with the free tier but has limitations on detection accuracy.

## Troubleshooting

### Headset Won't Connect

1. Check battery level (charge if low)
2. Try different USB port for dongle
3. Restart Emotiv Cortex
4. Re-pair the headset

### Poor Command Detection

1. Retrain commands with better contact quality
2. Train more samples
3. Reduce environmental noise
4. Ensure consistent mental imagery

### Cortex Not Running

1. Check Windows Services for "Emotiv Cortex"
2. Reinstall Cortex if service is missing
3. Run Cortex as administrator if needed

## Next Steps

- [Quickstart Guide](../getting-started/quickstart.md) - Start using BCIpyDummies
- [Mental Commands Guide](../user-guide/mental-commands.md) - Deep dive into command training

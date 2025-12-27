# 🔊 Among Us Party Game - Sonos Connector

A lightweight, open-source client that connects your local Sonos speakers to the [Among Us Party Game](https://amogus-party.duckdns.org).

> **🔒 Privacy & Security**: This code is 100% open source. You can review every line before running it. The connector only communicates with the game server to receive sound events - it doesn't collect any personal data or access anything else on your network.

## What It Does

When you're playing the Among Us party game, this connector:
1. Discovers Sonos speakers on your local WiFi network
2. Connects to the game server (via secure WebSocket)
3. Plays game sounds (meeting alerts, victory music, etc.) through your Sonos speakers

That's it! No data collection, no background processes, no funny business.

---

## Option 1: Download the Executable

1. Go to [Releases](../../releases) and download the latest version for your OS
2. Run it and enter your game room code

| Platform | File |
|----------|------|
| macOS (Apple Silicon) | `sonos-connector-macos-arm64` |
| macOS (Intel) | `sonos-connector-macos-x64` |
| Windows | `sonos-connector.exe` |

> **Note**: macOS executables don't have a `.exe` extension - that's normal!

### macOS Security Warning

Since this isn't signed with an Apple Developer certificate, macOS will block it. You **must** run it from Terminal:

```bash
# 1. Open Terminal (Cmd+Space, type "Terminal", hit Enter)

# 2. Navigate to your Downloads folder (or wherever you saved it)
cd ~/Downloads

# 3. Remove the quarantine flag
xattr -d com.apple.quarantine ./sonos-connector-macos-arm64

# 4. Make it executable
chmod +x ./sonos-connector-macos-arm64

# 5. Run it!
./sonos-connector-macos-arm64 YOUR_ROOM_CODE
```

> ⚠️ **Double-clicking won't work** - you must use Terminal for unsigned apps.

---

## Option 2: Run from Source (Recommended for the Paranoid 😉)

If you want to verify exactly what's running:

### 1. Clone this repo
```bash
git clone https://github.com/YOUR_USERNAME/amogus-sonos-connector.git
cd amogus-sonos-connector
```

### 2. Run the setup script (handles everything!)
```bash
./start.sh
```

The `start.sh` script will automatically:
- ✅ Check for Python 3.7+
- ✅ Create a virtual environment
- ✅ Install all dependencies
- ✅ Start the connector

That's it! Just one command.

### Alternative: Manual Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Review the code (it's ~500 lines)
cat sonos_connector.py

# Run it
python sonos_connector.py YOUR_ROOM_CODE
```

---

## Command Line Options

```bash
# Basic usage (interactive speaker selection)
./start.sh ABCD

# Or with Python directly
python sonos_connector.py ABCD

# Set volume (0-100)
./start.sh ABCD --volume 50

# Use a different game server
./start.sh ABCD --server https://your-server.com
```

---

## Speaker Selection

When you start the connector, it will discover all Sonos speakers on your network and let you choose which ones to use:

```
📻 AVAILABLE SONOS SPEAKERS
==================================================
  [1] Living Room (192.168.1.100)
  [2] Kitchen (192.168.1.101)
  [3] Bedroom (192.168.1.102)
==================================================

Commands:
  • Enter numbers separated by commas (e.g., 1,3,4)
  • Enter 'all' or 'a' to select all speakers
  • Enter 'ping <number>' to test a speaker
  • Enter 'ping all' to test all speakers

Select speakers: 1,2
✅ Selected 2 speaker(s):
   • Living Room
   • Kitchen
```

Use the **ping** command to play a test sound on a speaker to help identify which is which!

---

## How It Works (Technical Details)

```
┌─────────────────┐         ┌─────────────────┐         ┌─────────────────┐
│   Game Server   │◄───────►│ Sonos Connector │────────►│ Sonos Speakers  │
│  (WebSocket)    │  events │   (this app)    │  audio  │  (your network) │
└─────────────────┘         └─────────────────┘         └─────────────────┘
```

1. The connector joins a Socket.IO room for your game (`sonos_ROOMCODE`)
2. When the game triggers sounds, the server emits events like `play_sound`, `loop_sound`, `stop_sound`
3. The connector receives these events and tells your Sonos to play the corresponding audio file from a public GitHub repo

**Audio source**: `https://raw.githubusercontent.com/siacavazzi/amogus_assets/main/audio/`

---

## Requirements

- Python 3.7+ (if running from source)
- Sonos speakers on the same WiFi network as your computer
- A game room code from [amogus-party.duckdns.org](https://amogus-party.duckdns.org)

---

## Troubleshooting

### "No Sonos speakers found"
- Ensure your computer is on the same WiFi as your Sonos
- Check that Sonos speakers are powered on
- Try restarting the Sonos app

### "Connection failed"
- Verify the room code is correct (4 letters)
- Check your internet connection
- Make sure a game is active in that room

### Sound not playing
- Check the volume setting (`--volume 50`)
- Make sure speakers aren't muted in the Sonos app

---

## Building from Source

```bash
pip install pyinstaller
pyinstaller --onefile --name sonos-connector --clean sonos_connector.py
```

The executable will be in the `dist/` folder.

---

## License

MIT License - do whatever you want with it!

---

## Contributing

Issues and PRs welcome! This is a fun side project for house parties.

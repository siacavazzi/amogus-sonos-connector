# 🔊 Sus Party Sonos Connector

Play [Sus Party](https://susparty.com) game sounds on your Sonos speakers. The meeting bell, the meltdown alarm and the victory music come out of every Sonos in the house instead of one laptop speaker.

> **🔒 Privacy & Security**: This code is 100% open source, and you can read every line before running it. The connector only talks to the game server to receive sound events, and to your Sonos speakers to play them. It collects no personal data and touches nothing else on your network.

## What It Does

While you play Sus Party, this connector:
1. Finds the Sonos speakers on your Wi-Fi and lets you pick which ones to use
2. Joins your game with its room code (over a secure WebSocket)
3. Plays the game's sounds (meeting calls, meltdown alarm, victory music and more) through those speakers
4. When the room closes, asks for the next room code, so you can keep it running all night

You need a computer (Mac, Windows or Linux) on the **same Wi-Fi as your Sonos**. It stays running in a window while you play.

---

## Option 1: Download the App

1. Go to [Releases](https://github.com/siacavazzi/amogus-sonos-connector/releases/latest) and download the file for your computer
2. Start it, pick your speakers, and enter the room code shown on the game screen

| Computer | File |
|----------|------|
| Mac with Apple chip (M1 or newer) | `sonos-connector-macos-arm64` |
| Mac with Intel chip | `sonos-connector-macos-x64` |
| Windows | `sonos-connector.exe` |

> **Note**: The Mac files have no `.exe` or `.app` ending. That's normal.

### Mac: run it from Terminal

The app isn't signed with an Apple Developer certificate, so macOS blocks it if you double-click it. Run it from Terminal instead:

```bash
# 1. Open Terminal (Cmd+Space, type "Terminal", press Enter)

# 2. Go to the folder you saved it in
cd ~/Downloads

# 3. Remove the "downloaded from the internet" block
xattr -d com.apple.quarantine ./sonos-connector-macos-arm64

# 4. Make it runnable
chmod +x ./sonos-connector-macos-arm64

# 5. Run it
./sonos-connector-macos-arm64
```

Use `sonos-connector-macos-x64` in those commands if you have an Intel Mac.

### Windows

Double-click `sonos-connector.exe`. If Windows SmartScreen says it "protected your PC", click **More info**, then **Run anyway**. Allow it on private networks if Windows Firewall asks, since it needs to find your speakers.

---

## Option 2: Run from Source (Mac or Linux)

If you want to see exactly what's running:

```bash
git clone https://github.com/siacavazzi/amogus-sonos-connector.git
cd amogus-sonos-connector
./start.sh
```

`start.sh` does the setup for you:
- ✅ Checks for Python 3.10 or newer
- ✅ Creates a virtual environment in `.venv`
- ✅ Installs the dependencies (and updates them after a `git pull`)
- ✅ Starts the connector

### Manual setup (any computer with Python 3.10+)

```bash
pip install -r requirements.txt
python sonos_connector.py
```

---

## Command Line Options

```bash
# Start and type the room code when asked
./start.sh

# Or pass the room code straight away
./start.sh MAWA

# Set the starting volume (0-100)
./start.sh MAWA --volume 50

# Show the version
python sonos_connector.py --version

# Use your own game server (if you self-host Sus Party)
./start.sh MAWA --server https://your-server.example
```

---

## Speaker Selection

When it starts, the connector lists the Sonos speakers it found and lets you choose:

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
  • Enter 'ping <number>' or 'p <number>' to test a speaker
  • Enter 'ping all' or 'p all' to test all speakers

Select speakers: 1,2
✅ Selected 2 speaker(s):
   • Living Room
   • Kitchen
```

Use **ping** to play a test sound on one speaker, so you can tell which is which. Then set the volume (type `test` to hear it, `done` to continue).

---

## How It Works

```
┌─────────────────┐         ┌─────────────────┐         ┌─────────────────┐
│   Game Server   │◄───────►│ Sonos Connector │────────►│ Sonos Speakers  │
│ (susparty.com)  │  events │   (this app)    │  audio  │  (your Wi-Fi)   │
└─────────────────┘         └─────────────────┘         └─────────────────┘
```

1. The connector sends `sonos_join` with your room code and the server adds it to that game's sound channel
2. When something happens in the game, the server sends `play_sound`, `loop_sound` or `stop_sound` with a sound name
3. The connector tells your Sonos to play that sound's file from the public [amogus_assets](https://github.com/siacavazzi/amogus_assets) repo
4. Every 30 seconds it checks the room is still open. When the game room closes, it stops the sound and asks for the next code
5. If the connection drops (Wi-Fi blip, server update), it reconnects and rejoins on its own

**Audio files**: `https://raw.githubusercontent.com/siacavazzi/amogus_assets/main/audio/`

---

## Troubleshooting

### "No Sonos speakers found"
- Make sure your computer is on the same Wi-Fi as your Sonos (not a guest network)
- Check that the speakers are switched on and show up in the Sonos app
- On Windows, allow the connector through the firewall on private networks
- On a Mac, allow Terminal to find devices on your local network if macOS asks (System Settings → Privacy & Security → Local Network)

### "Game room ... not found"
- Check the room code on the game screen (4 letters)
- The host has to create the room first

### "Lost connection to the game server"
- The connector keeps trying to reconnect by itself. Check the computer's internet connection

### No sound
- Check the volume you picked, and that the speakers aren't muted in the Sonos app
- Make sure no one else started music on the same speakers

---

## Development

```bash
pip install -r requirements.txt
python -m unittest discover tests
```

The tests need no Sonos speakers and no game server. They run on every pull request.

### Building the downloads

The **Build downloads** workflow (Actions tab) builds the Mac (Apple chip and Intel) and Windows files. Run it by hand to get the files as a build artifact, or push a version tag to publish a release:

```bash
git tag v1.0.0
git push origin v1.0.0
```

To build one yourself:

```bash
pip install pyinstaller
pyinstaller --onefile --clean --name sonos-connector sonos_connector.py
```

The file ends up in `dist/`.

---

## License

MIT License. Do whatever you want with it!

## Contributing

Issues and pull requests welcome! This started as a side project for house parties.

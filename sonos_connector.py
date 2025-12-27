#!/usr/bin/env python3
"""
Among Us Sonos Connector
========================
A lightweight client that connects to the hosted Among Us game server
and plays sounds on your local Sonos speakers.

Usage:
    python sonos_connector.py [room_code]
    
    Or run the executable:
    ./sonos_connector [room_code]

Requirements:
    pip install python-socketio soco requests
"""

import sys
import time
import logging
import argparse
from threading import Thread, Lock

try:
    import socketio
except ImportError:
    print("Missing dependency: python-socketio")
    print("Install with: pip install python-socketio")
    sys.exit(1)

try:
    from soco import discover, SoCoException
    from requests.exceptions import ReadTimeout, ConnectTimeout, Timeout
except ImportError:
    print("Missing dependency: soco")
    print("Install with: pip install soco")
    sys.exit(1)


# ============ Configuration ============
DEFAULT_SERVER = "https://susparty.com"
AUDIO_BASE_URL = "https://raw.githubusercontent.com/siacavazzi/amogus_assets/main/audio/"

# Ping sound URL - a short beep/chime for speaker identification
PING_SOUND_URL = AUDIO_BASE_URL + "test.mp3"

# ============ Logging Setup ============
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)


# ============ Speaker Selection ============
def discover_all_speakers():
    """Discover all Sonos speakers on the network."""
    print("\n🔍 Discovering Sonos speakers on your network...")
    
    try:
        discovered = discover(timeout=10)
        if not discovered:
            print("❌ No Sonos speakers found!")
            return []
        
        discovered = list(discovered)
        
        # Filter to only reachable speakers
        reachable = []
        for speaker in discovered:
            try:
                _ = speaker.player_name  # Test if reachable
                reachable.append(speaker)
            except Exception:
                pass
        
        return reachable
        
    except Exception as e:
        print(f"❌ Error discovering speakers: {e}")
        return []


def ping_speaker(speaker, volume=40):
    """Play a short test sound on a specific speaker to identify it."""
    try:
        # If speaker is part of a group and not the coordinator, temporarily ungroup it
        was_grouped = False
        original_group = None
        
        if speaker.group and speaker.group.coordinator != speaker:
            was_grouped = True
            original_group = speaker.group.coordinator
            speaker.unjoin()
            time.sleep(0.5)  # Give it a moment to ungroup
        
        original_volume = speaker.volume
        speaker.volume = volume
        speaker.play_uri(PING_SOUND_URL)
        print(f"  🔔 Pinging: {speaker.player_name}")
        time.sleep(2)  # Let the sound play
        speaker.stop()
        speaker.volume = original_volume
        
        # Rejoin the group if it was grouped before
        if was_grouped and original_group:
            try:
                speaker.join(original_group)
            except Exception:
                pass  # Don't fail if rejoin doesn't work
        
        return True
    except Exception as e:
        print(f"  ❌ Failed to ping {speaker.player_name}: {e}")
        return False


def interactive_speaker_selection(speakers):
    """
    Interactive CLI for selecting which speakers to use.
    Returns a list of selected speakers.
    """
    if not speakers:
        return []
    
    print("\n" + "=" * 50)
    print("📻 AVAILABLE SONOS SPEAKERS")
    print("=" * 50)
    
    for i, speaker in enumerate(speakers, 1):
        try:
            print(f"  [{i}] {speaker.player_name} ({speaker.ip_address})")
        except Exception:
            print(f"  [{i}] Unknown speaker ({speaker.ip_address})")
    
    print("=" * 50)
    print("\nCommands:")
    print("  • Enter numbers separated by commas (e.g., 1,3,4)")
    print("  • Enter 'all' or 'a' to select all speakers")
    print("  • Enter 'ping <number>' or 'p <number>' to test a speaker")
    print("  • Enter 'ping all' or 'p all' to test all speakers")
    print("  • Enter 'list' or 'l' to show speakers again")
    print("  • Enter 'quit' or 'q' to exit")
    print()
    
    while True:
        try:
            user_input = input("Select speakers: ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\n👋 Goodbye!")
            sys.exit(0)
        
        if not user_input:
            print("Please enter a selection.")
            continue
        
        # Handle quit
        if user_input in ('quit', 'q'):
            print("👋 Goodbye!")
            sys.exit(0)
        
        # Handle list
        if user_input in ('list', 'l'):
            print()
            for i, speaker in enumerate(speakers, 1):
                try:
                    print(f"  [{i}] {speaker.player_name} ({speaker.ip_address})")
                except Exception:
                    print(f"  [{i}] Unknown speaker ({speaker.ip_address})")
            print()
            continue
        
        # Handle ping
        if user_input.startswith('ping ') or user_input.startswith('p '):
            parts = user_input.split(maxsplit=1)
            if len(parts) < 2:
                print("Usage: ping <number> or ping all")
                continue
            
            ping_target = parts[1].strip()
            
            if ping_target in ('all', 'a'):
                print("\n🔔 Pinging all speakers...")
                for speaker in speakers:
                    ping_speaker(speaker)
                print()
            else:
                try:
                    idx = int(ping_target) - 1
                    if 0 <= idx < len(speakers):
                        print()
                        ping_speaker(speakers[idx])
                        print()
                    else:
                        print(f"Invalid speaker number. Choose 1-{len(speakers)}")
                except ValueError:
                    print("Usage: ping <number> or ping all")
            continue
        
        # Handle 'all' selection
        if user_input in ('all', 'a'):
            print(f"\n✅ Selected all {len(speakers)} speaker(s)")
            return speakers
        
        # Handle numbered selection
        try:
            # Parse comma-separated numbers
            indices = []
            for part in user_input.replace(' ', ',').split(','):
                part = part.strip()
                if part:
                    # Handle ranges like "1-3"
                    if '-' in part:
                        start, end = part.split('-', 1)
                        for i in range(int(start), int(end) + 1):
                            indices.append(i)
                    else:
                        indices.append(int(part))
            
            # Validate indices
            selected = []
            for idx in indices:
                if 1 <= idx <= len(speakers):
                    speaker = speakers[idx - 1]
                    if speaker not in selected:
                        selected.append(speaker)
                else:
                    print(f"⚠️  Ignoring invalid number: {idx}")
            
            if selected:
                print(f"\n✅ Selected {len(selected)} speaker(s):")
                for speaker in selected:
                    print(f"   • {speaker.player_name}")
                return selected
            else:
                print("No valid speakers selected. Try again.")
                
        except ValueError:
            print("Invalid input. Enter numbers, 'all', 'ping <n>', or 'quit'")


def interactive_volume_selection(speakers, default_volume=30):
    """
    Interactive CLI for selecting and testing volume.
    Returns the chosen volume level.
    """
    print("\n" + "=" * 50)
    print("🔈 VOLUME SETUP")
    print("=" * 50)
    print(f"\nCurrent volume: {default_volume}%")
    print("\nCommands:")
    print("  • Enter a number (0-100) to set volume")
    print("  • Enter 'test' or 't' to play a test sound")
    print("  • Enter 'done' or 'd' to confirm and continue")
    print()
    
    current_volume = default_volume
    
    # Set initial volume on all speakers
    for speaker in speakers:
        try:
            # Ungroup if needed to set volume
            if speaker.group and speaker.group.coordinator != speaker:
                speaker.unjoin()
                time.sleep(0.3)
            speaker.volume = current_volume
        except Exception:
            pass
    
    while True:
        try:
            user_input = input(f"Volume [{current_volume}%]: ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\n👋 Goodbye!")
            sys.exit(0)
        
        if not user_input or user_input in ('done', 'd'):
            print(f"\n✅ Volume set to {current_volume}%")
            return current_volume
        
        if user_input in ('test', 't'):
            print("  🔊 Playing test sound...")
            # Play test on first speaker (others may not be grouped yet)
            try:
                test_speaker = speakers[0]
                # Make sure it's not in another group
                if test_speaker.group and test_speaker.group.coordinator != test_speaker:
                    test_speaker.unjoin()
                    time.sleep(0.3)
                test_speaker.play_uri(PING_SOUND_URL)
                time.sleep(2)
                test_speaker.stop()
            except Exception as e:
                print(f"  ❌ Test failed: {e}")
            continue
        
        # Try to parse as volume number
        try:
            new_volume = int(user_input)
            if 0 <= new_volume <= 100:
                current_volume = new_volume
                # Update volume on all speakers
                for speaker in speakers:
                    try:
                        speaker.volume = current_volume
                    except Exception:
                        pass
                print(f"  Volume set to {current_volume}% (enter 'test' to hear it)")
            else:
                print("  Volume must be between 0 and 100")
        except ValueError:
            print("  Invalid input. Enter a number (0-100), 'test', or 'done'")


# ============ Sonos Controller ============
class SonosController:
    """Controls Sonos speakers on the local network."""
    
    def __init__(self, speakers, volume=30):
        self.volume = volume
        self.speakers = speakers
        self.master_speaker = None
        self.ready = False
        self.stop_loop = False
        self.loop_thread = None
        self.lock = Lock()
        
        if self.speakers:
            self._initialize_master()
    
    def _initialize_master(self):
        """Set up master speaker and join others."""
        # First, ungroup all selected speakers from any existing groups
        logger.info("🔄 Preparing speakers...")
        for speaker in self.speakers:
            try:
                # Check if speaker is in a group and not the coordinator
                if speaker.group and speaker.group.coordinator != speaker:
                    speaker.unjoin()
                    logger.info(f"  ↳ Ungrouped: {speaker.player_name}")
                    time.sleep(0.3)  # Brief pause for Sonos to process
            except Exception as e:
                logger.warning(f"  ↳ Could not ungroup {speaker.player_name}: {e}")
        
        # Now set up our own group with the first speaker as master
        for speaker in self.speakers:
            try:
                self.master_speaker = speaker
                logger.info(f"🔊 Master speaker: {speaker.player_name}")
                
                # Join other speakers to this master
                for other in self.speakers:
                    if other != speaker:
                        try:
                            other.join(speaker)
                            logger.info(f"  ↳ Joined: {other.player_name}")
                        except Exception as e:
                            logger.warning(f"  ↳ Failed to join {other.player_name}: {e}")
                
                # Set volume on master (it should propagate to group)
                speaker.volume = self.volume
                logger.info(f"🔈 Volume set to {self.volume}%")
                
                self.ready = True
                return
                
            except Exception as e:
                logger.warning(f"Failed with {speaker.player_name}, trying next...")
        
        logger.error("❌ Could not initialize any speaker as master")
    
    def play_sound(self, sound, interrupt=True):
        """Play a sound on the Sonos system."""
        if not self.ready:
            logger.warning("Sonos not ready!")
            return False
        
        if interrupt:
            self.stop()
        
        try:
            uri = AUDIO_BASE_URL + sound + ".mp3"
            self.master_speaker.play_uri(uri)
            logger.info(f"🎵 Playing: {sound}")
            return True
        except Exception as e:
            logger.error(f"Failed to play {sound}: {e}")
            return False
    
    def loop_sound(self, sound, duration):
        """Loop a sound for a duration."""
        if not self.ready:
            return False
        
        self.stop()
        self.stop_loop = False
        
        def loop_task():
            with self.lock:
                try:
                    uri = AUDIO_BASE_URL + sound + ".mp3"
                    end_time = time.time() + duration
                    
                    while time.time() < end_time and not self.stop_loop:
                        self.master_speaker.play_uri(uri)
                        logger.info(f"🔁 Looping: {sound}")
                        
                        # Wait for track to finish
                        while not self.stop_loop:
                            info = self.master_speaker.get_current_transport_info()
                            state = info.get('current_transport_state', '').lower()
                            if state not in ('playing', 'transitioning'):
                                break
                            time.sleep(0.5)
                    
                except Exception as e:
                    logger.error(f"Loop error: {e}")
        
        self.loop_thread = Thread(target=loop_task, daemon=True)
        self.loop_thread.start()
        return True
    
    def stop(self):
        """Stop all playback."""
        self.stop_loop = True
        if self.ready and self.master_speaker:
            try:
                self.master_speaker.stop()
                if self.loop_thread and self.loop_thread.is_alive():
                    self.loop_thread.join(timeout=2)
            except Exception:
                pass


# ============ Socket.IO Client ============
class SonosConnector:
    """Connects to the game server and plays sounds on Sonos."""
    
    def __init__(self, server_url, speakers, volume=30):
        self.server_url = server_url
        self.room_code = None
        self.sonos = SonosController(speakers=speakers, volume=volume)
        self.sio = socketio.Client(reconnection=True, reconnection_attempts=0)
        self.connected = False
        self.joined = False
        self.join_error = None
        self.room_disbanded = False
        
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Set up Socket.IO event handlers."""
        
        @self.sio.event
        def connect():
            logger.info(f"✅ Connected to server!")
            self.connected = True
            # If we have a room code, try to join
            if self.room_code:
                self.sio.emit('sonos_join', {'room_code': self.room_code})
        
        @self.sio.event
        def disconnect():
            logger.info("❌ Disconnected from server")
            self.connected = False
            self.joined = False
        
        @self.sio.event
        def connect_error(data):
            logger.error(f"Connection error: {data}")
        
        @self.sio.on('sonos_joined')
        def on_joined(data):
            logger.info(f"🎮 Joined room: {self.room_code}")
            self.joined = True
            self.join_error = None
            self.room_disbanded = False
            if self.sonos.ready:
                self.sonos.play_sound('test')
        
        @self.sio.on('sonos_error')
        def on_error(data):
            error_msg = data.get('message', 'Unknown error')
            logger.error(f"❌ {error_msg}")
            self.join_error = error_msg
            self.joined = False
        
        @self.sio.on('room_disbanded')
        def on_room_disbanded(data=None):
            logger.info("📢 Room has been disbanded by the host")
            self.sonos.stop()
            self.joined = False
            self.room_disbanded = True
        
        # Sound events from the game
        @self.sio.on('play_sound')
        def on_play_sound(data):
            sound = data.get('sound')
            if sound:
                self.sonos.play_sound(sound)
        
        @self.sio.on('loop_sound')
        def on_loop_sound(data):
            sound = data.get('sound')
            duration = data.get('duration', 60)
            if sound:
                self.sonos.loop_sound(sound, duration)
        
        @self.sio.on('stop_sound')
        def on_stop_sound(data=None):
            self.sonos.stop()
    
    def connect(self):
        """Connect to the game server."""
        if not self.sonos.ready:
            logger.error("❌ Sonos not ready - cannot connect")
            return False
        
        try:
            logger.info(f"🔌 Connecting to {self.server_url}...")
            self.sio.connect(self.server_url, transports=['websocket', 'polling'])
            return True
        except Exception as e:
            logger.error(f"❌ Connection failed: {e}")
            return False
    
    def join_room(self, room_code):
        """Attempt to join a game room. Returns True if successful."""
        self.room_code = room_code.upper()
        self.joined = False
        self.join_error = None
        
        if self.connected:
            self.sio.emit('sonos_join', {'room_code': self.room_code})
            
            # Wait for response (with timeout)
            timeout = 5
            start = time.time()
            while time.time() - start < timeout:
                if self.joined:
                    return True
                if self.join_error:
                    return False
                time.sleep(0.1)
            
            logger.error("❌ Timeout waiting for room join response")
            return False
        return False
    
    def disconnect(self):
        """Disconnect from the server."""
        self.sonos.stop()
        if self.connected:
            self.sio.disconnect()
    
    def wait(self):
        """Wait for the connection to end."""
        try:
            self.sio.wait()
        except KeyboardInterrupt:
            logger.info("\n👋 Shutting down...")
            self.disconnect()


# ============ Main ============
def print_banner():
    print("""
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║     🎮 AMONG US - SONOS CONNECTOR 🔊                      ║
║                                                           ║
║     Connect your Sonos speakers to the game!              ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
    """)


def main():
    print_banner()
    
    parser = argparse.ArgumentParser(description='Connect Sonos speakers to Among Us game')
    parser.add_argument('room_code', nargs='?', help='Game room code to join')
    parser.add_argument('--server', default=DEFAULT_SERVER, help='Game server URL')
    parser.add_argument('--volume', type=int, default=30, help='Initial speaker volume (0-100)')
    
    args = parser.parse_args()
    
    # Step 1: Discover and select speakers
    all_speakers = discover_all_speakers()
    selected_speakers = interactive_speaker_selection(all_speakers)
    
    if not selected_speakers:
        logger.error("No speakers selected!")
        sys.exit(1)
    
    # Step 2: Configure volume with testing
    volume = interactive_volume_selection(selected_speakers, args.volume)
    
    # Step 3: Create connector
    connector = SonosConnector(
        server_url=args.server,
        speakers=selected_speakers,
        volume=volume
    )
    
    # Step 4: Connect to server
    if not connector.connect():
        sys.exit(1)
    
    # Step 5: Main room join loop (handles rejoining after room disbands)
    room_code = args.room_code
    while True:
        # Join room with retry logic
        while True:
            if not room_code:
                print()
                try:
                    room_code = input("Enter room code: ").strip()
                except (EOFError, KeyboardInterrupt):
                    print("\n👋 Goodbye!")
                    connector.disconnect()
                    sys.exit(0)
            
            if not room_code:
                print("Room code is required. Try again.")
                continue
            
            if connector.join_room(room_code):
                # Successfully joined!
                break
            else:
                # Failed to join - prompt again
                print()
                print("Please try a different room code.")
                room_code = None  # Clear so we prompt again
        
        logger.info("🎧 Listening for game events... (Ctrl+C to quit)")
        
        # Wait while connected to room
        try:
            while connector.joined and not connector.room_disbanded:
                time.sleep(0.5)
            
            # If room was disbanded, prompt for new room
            if connector.room_disbanded:
                print()
                print("=" * 50)
                print("The room has ended. Join a new room to continue.")
                print("=" * 50)
                room_code = None  # Clear so we prompt again
                connector.room_disbanded = False
                continue
            
            # If we got here without being joined, something went wrong
            if not connector.connected:
                logger.error("Lost connection to server")
                break
                
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            connector.disconnect()
            sys.exit(0)
    
    connector.disconnect()


if __name__ == '__main__':
    main()

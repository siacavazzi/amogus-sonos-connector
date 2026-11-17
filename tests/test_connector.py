"""Checks that need no Sonos speakers and no game server.

Run with:  python -m unittest discover tests
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import sonos_connector as sc  # noqa: E402


class FakeSonos:
    ready = True

    def __init__(self):
        self.events = []

    def play_sound(self, sound, interrupt=True):
        self.events.append(('play', sound))

    def loop_sound(self, sound, duration):
        self.events.append(('loop', sound, duration))

    def stop(self):
        self.events.append(('stop',))


def handler(connector, event):
    return connector.sio.handlers['/'][event]


class SoundUrlTest(unittest.TestCase):
    def test_names_that_match_their_file(self):
        self.assertEqual(sc.sound_url('meeting'), sc.AUDIO_BASE_URL + 'meeting.mp3')
        self.assertEqual(sc.sound_url('50_percent_tasks'), sc.AUDIO_BASE_URL + '50_percent_tasks.mp3')

    def test_crew_victory_plays_the_victory_file(self):
        self.assertEqual(sc.sound_url('crew_victory'), sc.AUDIO_BASE_URL + 'victory.mp3')


class ConnectorEventsTest(unittest.TestCase):
    def setUp(self):
        self.sonos = FakeSonos()
        self.c = sc.SonosConnector('https://example.invalid', sonos=self.sonos)

    def join(self, code='MAWA'):
        self.c.room_code = code
        handler(self.c, 'sonos_joined')({'room_code': code})

    def test_join_sound_plays_once(self):
        self.join()
        self.join()  # the room check asks again every so often
        self.assertEqual(self.sonos.events, [('play', 'test')])

    def test_server_fixes_the_typed_code(self):
        self.c.room_code = 'MAPA'
        handler(self.c, 'sonos_joined')({'room_code': 'MARA'})
        self.assertEqual(self.c.room_code, 'MARA')

    def test_error_before_joining_is_a_bad_code(self):
        handler(self.c, 'sonos_error')({'message': 'Game room ZZZZ not found'})
        self.assertFalse(self.c.room_ended)
        self.assertEqual(self.c.join_error, 'Game room ZZZZ not found')

    def test_error_after_joining_means_the_room_closed(self):
        self.join()
        handler(self.c, 'sonos_error')({'message': 'Game room MAWA not found'})
        self.assertTrue(self.c.room_ended)
        self.assertIn(('stop',), self.sonos.events)

    def test_room_disbanded(self):
        self.join()
        handler(self.c, 'room_disbanded')({'message': 'Room has been closed'})
        self.assertTrue(self.c.room_ended)

    def test_sound_events(self):
        self.join()
        handler(self.c, 'play_sound')({'sound': 'meeting'})
        handler(self.c, 'loop_sound')({'sound': 'meltdown', 'duration': 45})
        handler(self.c, 'stop_sound')({})
        handler(self.c, 'play_sound')({})  # no sound name: ignored
        self.assertEqual(self.sonos.events[1:], [('play', 'meeting'), ('loop', 'meltdown', 45), ('stop',)])


if __name__ == '__main__':
    unittest.main()

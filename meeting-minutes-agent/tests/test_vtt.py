from datetime import datetime, timezone

from meeting_minutes_agent.vtt import parse_vtt

START = datetime(2026, 8, 25, 9, 0, tzinfo=timezone.utc)

TEAMS_VTT = """WEBVTT

0d1b8e5a-1/1-0
00:00:04.120 --> 00:00:07.980
<v Ada Lovelace>We are short thirteen thousand pairs this week.</v>

0d1b8e5a-1/1-1
00:01:10.000 --> 00:01:14.500
<v Bob Stone>The curing oven fault cost us eleven hours.</v>
"""

ZOOM_VTT = """WEBVTT

1
00:00:04.120 --> 00:00:07.980
Ada Lovelace: We are short thirteen thousand pairs this week.

2
00:01:10.000 --> 00:01:14.500
Bob Stone: The curing oven fault cost us eleven hours.
"""


def test_parses_teams_voice_spans():
    utterances = parse_vtt(TEAMS_VTT, START)
    assert [u.speaker for u in utterances] == ["Ada Lovelace", "Bob Stone"]
    assert utterances[0].text == "We are short thirteen thousand pairs this week."
    assert utterances[0].at.second == 4
    assert utterances[1].at.minute == 1


def test_parses_zoom_speaker_prefixes():
    utterances = parse_vtt(ZOOM_VTT, START)
    assert [u.speaker for u in utterances] == ["Ada Lovelace", "Bob Stone"]
    assert all(u.channel == "speech" for u in utterances)


def test_cue_without_a_speaker_still_captures_text():
    vtt = "WEBVTT\n\n00:00:01.000 --> 00:00:02.000\nsomething was said\n"
    (utterance,) = parse_vtt(vtt, START)
    assert utterance.speaker == "Unknown speaker"
    assert utterance.text == "something was said"

from re import split, sub
import sounddevice as sd
from tempfile import NamedTemporaryFile as TemporaryFile
from wave import open as wave
import whisper

from consumers import *

__import__("pyttsx3").speak("I will cum if this works first try")

# Types
type Commands = list[list[str]]

# Constants
SAMPLE_RATE: int = 16000
DURATION: int = 5
BLOCK_SIZE: int = SAMPLE_RATE * DURATION
CALL_WORD: str = "atlas"

# Useful variables
model = whisper.load_model("base.en")
roll: list[str] = []

# Grabs commands in the transcript roll
#
# @param roll The transcript roll (max len 2)
# @return A list of tokenized commands
def lex_cmds(roll: list[str]) -> Commands:
    # Get combined data
    full_script: list[str] = split(r" +", " ".join(roll))
    full_script = [s for s in full_script if len(s) > 0]
    cmds: Commands = []

    # Parse out commands
    for i, s in enumerate(full_script):
        if s != CALL_WORD:
            continue

        try:
            if (n := full_script[i + 1]) in consumers:
                cmds.append(full_script[i + 1:i + consumers[n] + 2])
        except IndexError:
            continue

    # If len(roll) > 1, check that commands aren't exclusive to sector 1
    if len(roll) < 2:
        return cmds

    s1_lex: Commands = lex_cmds([roll[0]])
    cmds_v: Commands = []

    for c in cmds:
        for d in s1_lex:
            if c == d: break
        else:
            cmds_v.append(c)

    return cmds_v

# Processes a chunk of audio
#
# @global roll The transcript roll (max len 2)
# @param indata The audio data
# @param frames The amount of data frames
# @param time How long the audio data is
# @param status A status indicator
def process_aud(indata, frames, time, status):
    global roll

    with TemporaryFile(delete=True, suffix=".wav", prefix="aud_", dir=".") as tmp:
        # Write data to temporary file
        with wave(tmp.name, "wb") as wav:
            wav.setframerate(SAMPLE_RATE)
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.writeframes(indata)

        # Construct roll
        tsc = model.transcribe(tmp.name)

        if len(tsc["segments"]) == 0 or tsc["segments"][0]["no_speech_prob"] > 0.43:
            print("[no speech recorded]")
            del roll[:]
            return

        del roll[:-1]
        roll.append(sub(r"[^a-z ]", "", tsc["text"].lower())[1:])

        # Parse commands
        lexed: Commands = lex_cmds(roll)
        print(lexed)

# The main block
def main():
        # Construct roll
    print("[READ START]")

    try:
        with sd.InputStream(blocksize=BLOCK_SIZE, samplerate=SAMPLE_RATE, dtype="int16", channels=1, callback=process_aud):
            input()
    except KeyboardInterrupt:
        print("[PRESS ENTER BROSKI]")

if __name__ == "__main__":
    main()

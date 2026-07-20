from re import split, sub
import sounddevice as sd
from subprocess import run
from tempfile import NamedTemporaryFile as TemporaryFile
from wave import open as wave
import whisper

from consumers import *

# Types
type Commands = list[list[str]]

# Constants
SAMPLE_RATE: int = 44100
DURATION: int = 5
BLOCK_SIZE: int = SAMPLE_RATE * DURATION

CALL_WORD: str = "atlas"
NEAR_CALLS: str = f"({"|".join([
    "at his",
    "at least",
    "at list",
    "at this",
    "atrisk",
    "lets",
    "that list",
    "that was",
])})"

# Useful variables
model = whisper.load_model("base.en")
roll: list[str] = []

# Makes text easier to parse
#
# @param s The text to prim
# @return The primmed text
def prim(s: str) -> str:
    return sub(r"s$", "", s)

# Removes duplicate elements from commands list
#
# @param l The list of commands
# @return l without duplicates
def remove_dup(l: Commands) -> Commands:
    return [list(e) for e in set(tuple(e) for e in l)]

# Grabs commands in the transcript roll
#
# @param roll The transcript roll (max len 2)
# @return A list of tokenized commands
def lex_cmds(roll: list[str]) -> Commands:
    # Get combined data
    full_script: list[str] = split(
        r" +",
        sub(
            NEAR_CALLS,
            CALL_WORD,
            " ".join(roll)
        )
    )

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
    s2_lex: Commands = lex_cmds([roll[1]])
    cmds_v: Commands = []

    for c in cmds:
        if c not in s1_lex or c in s2_lex:
            cmds_v.append(c)

    return remove_dup(cmds_v)

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
        tsc = model.transcribe(tmp.name, fp16=False)

        if len(tsc["segments"]) == 0 or tsc["segments"][0]["no_speech_prob"] > 0.43:
            print("[no speech recorded]")
            del roll[:]
            return

        del roll[:-1]
        roll.append(sub(r"[^a-z ]", "", tsc["text"].lower())[1:])
        print(roll[-1])

        # Parse commands
        lexed: Commands = lex_cmds(roll)

        for c in lexed:
            try:
                run(["espeak-ng", "'" + consumers_lt[prim(c[0])][c[1]](c[2:]) + "'"])
            except KeyError:
                pass

# The main block
def main():
    print("[READ START]")
    run(["espeak-ng", "'read start'"])

    try:
        with sd.InputStream(blocksize=BLOCK_SIZE, samplerate=SAMPLE_RATE, dtype="int16", channels=1, callback=process_aud):
            input()
    except KeyboardInterrupt:
        print("[PRESS ENTER BROSKI]")

if __name__ == "__main__":
    main()

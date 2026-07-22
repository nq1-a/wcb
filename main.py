from re import split, sub
import sounddevice as sd
from subprocess import run
from tempfile import NamedTemporaryFile as TemporaryFile
from tomllib import loads as toml_load
from wave import open as wave
import whisper

from consumers import *

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
    "atmos",
    "atrisk",
    "lets",
    "ratless",
    "that list",
    "that was",
])})"

STOP_WORD: str = "stop"
NEAR_STOPS: str = f"({"|".join([
    "start",
    "started",
])})"

# Useful variables
config: Config = {}
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
            sub(
                NEAR_STOPS,
                STOP_WORD,
                " ".join(roll)
            )
        )
    )

    full_script = [s for s in full_script if len(s) > 0]
    cmds: Commands = []

    # Parse out commands
    for i, s in enumerate(full_script):
        if s != CALL_WORD:
            continue

        try:
            if (n := prim(full_script[i + 1])) in consumers:
                if consumers[n] >= 0:
                    cmds.append([n] + full_script[i + 2:i + 2 + consumers[n]])
                else:
                    cmds.append([n] + full_script[i + 2:i + 3 + full_script[i + 3:].index("stop")])
        except (IndexError, ValueError):
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
    global config, roll

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
                ce_row = consumers_lt[c[0]]
                ce_row_inc: bool = c[1] in ce_row
                ce: CommandExec = ce_row[c[1] if ce_row_inc else "_"]
                ce_ac: int = ce.__code__.co_argcount
                tel: int = 2 - (1 if not ce_row_inc else 0)

                run(["espeak-ng", "'" + ce(c[tel:]) if ce_ac < 2 else ce(c[tel:], config) + "'"])
            except KeyError:
                pass

# The main block
def main():
    global config

    # Create & check tokens
    with open("config.toml") as f:
        config = toml_load(f.read())

    for k, t in config["tokens"].items():
        if len(t) == 0:
            print(f"[TOKEN {k} IS MISSING]")
            return

    # Begin read loop
    print("[READ START]")
    run(["espeak-ng", "'read start'"])

    try:
        with sd.InputStream(blocksize=BLOCK_SIZE, samplerate=SAMPLE_RATE, dtype="int16", channels=1, callback=process_aud):
            input()
    except KeyboardInterrupt:
        print("[PRESS ENTER BROSKI]")

if __name__ == "__main__":
    main()

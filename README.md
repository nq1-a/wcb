# Dependencies
This program will run with any version of Python >=3.12.
`espeak-ng` is also required for TTS.

To install required dependencies, use:

```bash
pip install -r requirements.txt
```

`cuda` is highly recommended for Nvidia GPUs.

# Before you run
Make a file called `config.toml` that looks like this:
```
[personal]
city = ""
email = ""

[tokens]
weatherapi_com = ""
```
and fill in the blanks. You'll need an API key from each site listed under `[tokens]`.

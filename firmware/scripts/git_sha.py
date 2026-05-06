import subprocess

Import("env")

try:
    sha = subprocess.check_output(["git", "rev-parse", "--short=12", "HEAD"], text=True).strip()
except Exception:
    sha = "unknown"

env.Append(CPPDEFINES=[("FIRMWARE_VERSION", '\\"%s\\"' % sha)])

"""dsdemo-11labs : Voice AI deployment prototype for Brazilian Portuguese customer support.

This package contains the three CLI tools used to demonstrate the deployment:
- generate_voice.py  : single-shot text -> mp3
- batch_generate.py  : reads data/support_scripts.json, generates all
- compare_voices.py  : the A/B/C demo (same line in 3 voices)

The Python is intentionally small. The headline of this repo is the deployment
playbook in docs/; the code exists to show that the playbook is grounded in
a real, runnable artifact.
"""

__version__ = "0.1.0"

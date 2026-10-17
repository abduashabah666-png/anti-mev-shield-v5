Anti-MEV Shield V5.0 — Protection Gate Prototype
What changed
Adds a configurable pre-trade gate using the existing heuristic score, slippage limit, and external reference-price deviation.
Reports explicit PASS/BLOCK reasons in the downloadable JSON evidence.
Fails closed when key analysis data is missing.
Keeps the app read-only: no wallet signing, swap submission, private relay, full transaction simulation, or live mempool monitoring.
Important limitation
The gate is an application-level prototype only. It does not itself prevent on-chain transactions or prove that an attack is detected/prevented. A real protection system needs a wallet/execution layer that enforces checks immediately before signing/submission, full transaction simulation, robust routing, security review, and extensive testing.
Run locally
pip install -r requirements.txt streamlit run app.py
Never enter a seed phrase or private key into this app.

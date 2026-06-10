# PayWire — Python SDK
## Run it (v0.4)

The mock issuer authorization endpoint is now live. To run locally:

```bash
pip install -r requirements.txt
uvicorn authorize:app --reload
``

Then open http://127.0.0.1:8000/docs to test `/authorize` and `/audit` interactively.
Two lines of code to give any AI agent a wallet with programmatic spend rules.

```python
from paywire import PayWire

agent = PayWire().agents.create(spend_limit_usd=100)
```

Coming soon. See [paywire-protocol](https://github.com/Paywire-dev/paywire-protocol) for the design doc.

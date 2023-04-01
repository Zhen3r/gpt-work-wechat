# WEWORK Gpt bot

## Install
1. create a new file `api-keys.env` in `conf`
```env
OPENAI_API_KEY="xxxxxxxxxxxxxx"
all_proxy="socks5h://127.0.0.1:xxxx"

WEWORK_TOKEN="xxxxxxx"
WEWORK_AES_KEY="xxxxxxxxxxxxxxxxxxxxxxxxx"
WEWORK_CORPID="xxxxxxxxxxxxxxxx"

WEWORK_GPT_AGENTID="1000002"
WEWOEK_GPT_SECRET="xxxxxxxxxxxxxxxxxxxxx"
```

2. `pip install -r requirements.txt`

3. run `uvicorn wework_api.api:app`
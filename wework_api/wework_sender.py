import os
import time
import json
from loguru import logger
import requests
from dotenv import load_dotenv

project_path = os.path.dirname(os.path.dirname(__file__))
env_path = os.path.join(project_path, "conf/api-keys.env")
load_dotenv(env_path)

CORPID = os.getenv("WEWORK_CORPID")
CORPSECRET = os.getenv("WEWOEK_GPT_SECRET")
AGENT_ID = os.getenv("WEWORK_GPT_AGENTID")
TOKEN_TIMEOUT = 6000  # get a new token after 6000 sec

project_path = os.path.dirname(os.path.dirname(__file__))
token_path = os.path.join(project_path, "sessions/sender.json")

class WechatSender():
    def __init__(self) -> None:
        self.token_time, self.token = self._get_cached_token()

    def send_text_msg(self, msg, user, agentid=AGENT_ID):
        logger.info(f"Sending msg to {user}: {msg}")
        url = "https://qyapi.weixin.qq.com/cgi-bin/message/send"
        params = {"access_token": self._get_token()}
        data = {
            "touser": user,
            "msgtype": "text",
            "agentid": agentid,
            "text": {
                "content": msg,
            },
            "duplicate_check_interval": 10,
            "debug": 1,
        }
        if os.environ["all_proxy"] is not None:
            all_proxy = os.environ["all_proxy"]
            os.environ["all_proxy"] = ""
            resp = requests.post(url, params=params, json=data, proxies={}).json()
            os.environ["all_proxy"] = all_proxy
        return resp
    
    def _get_token(self):
        now = time.time()
        if now - self.token_time >= TOKEN_TIMEOUT:
            self.token_time, self.token = self._get_new_access_token()
            self._cache_token(self.token_time, self.token)
        else:
            logger.info("Using cached token!")
        return self.token

    def _get_new_access_token(self):
        logger.info("Obtaining new access token!")
        url = "https://qyapi.weixin.qq.com/cgi-bin/gettoken"
        params = {"corpid": CORPID, "corpsecret": CORPSECRET, "debug":"1"}
        resp = requests.get(url, params=params).json()
        if resp["errcode"] != 0:
            logger.error(str(resp))
        return time.time(), resp["access_token"]
    
    def _cache_token(self, time, token):
        with open(token_path, "w") as f:
            json.dump({"time": time, "token": token}, f)
    
    def _get_cached_token(self):
        if os.path.exists(token_path):
            with open(token_path, "r") as f:
                data = json.load(f)
                return data["time"], data["token"]
        else:
            return 0, None




if __name__ == "__main__":
    print(WechatSender().send_text_msg("你的快递到了", "1", os.getenv("WEWORK_GPT_AGENTID")))
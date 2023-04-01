import os
import uvicorn
import fastapi
from lxml import etree
from dotenv import load_dotenv
from loguru import logger
from wework_api.utils import WXBizMsgCrypt
from wework_api.wework_sender import WechatSender
from gpt.utils import fake_chat, chat

project_path = os.path.dirname(os.path.dirname(__file__))
env_path = os.path.join(project_path, "conf/api-keys.env")
load_dotenv(env_path)

def get_chat_respond_and_send(from_user, content, agent_id):
    respond_msg = chat(from_user, content)
    # respond_msg = fake_chat(from_user, content)
    res = wechat_sender.send_text_msg(respond_msg, from_user, agent_id)
    logger.info(res)

app = fastapi.FastAPI()
wechat_sender = WechatSender()

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/callback")
def callback(msg_signature: str, timestamp: str, nonce: str, echostr: str):
    # http://home.orifish.tech:20052/callback
    wxcpt=WXBizMsgCrypt()
    ret, sEchoStr=wxcpt.VerifyURL(msg_signature, timestamp, nonce, echostr)
    # return plain text
    return fastapi.responses.PlainTextResponse(sEchoStr)

@app.post("/callback")
async def get_msg(request: fastapi.Request, msg_signature: str, 
                  timestamp: str, nonce: str, 
                  background_tasks: fastapi.BackgroundTasks, 
                  response: fastapi.Response):
    wxcpt=WXBizMsgCrypt()
    body = await request.body()
    _, decryped_msg = wxcpt.DecryptMsg(body, msg_signature, timestamp, nonce)
    decryped_root = etree.fromstring(decryped_msg.decode("utf-8"))
    msg_type = decryped_root.find("MsgType").text
    from_user = decryped_root.find("FromUserName").text
    to_user = decryped_root.find("ToUserName").text
    agent_id = decryped_root.find("AgentID").text
    response.status_code = 200

    if msg_type == "text":
        content = decryped_root.find("Content").text
        print(from_user, msg_type, content, agent_id)

        if agent_id == os.getenv("WEWORK_GPT_AGENTID"):
            # send the msg asynchronously
            background_tasks.add_task(get_chat_respond_and_send, from_user, content, agent_id)
        else:
            logger.info("Not GPT agent")
    elif msg_type == "event":
        event_key = decryped_root.find("EventKey").text
        logger.info(f"Event: {event_key}")
        if "_0_0" in event_key:
            content = "//新建多轮对话"
        elif "_0_1" in event_key:
            content = "//新建单轮对话"
        background_tasks.add_task(get_chat_respond_and_send, from_user, content, agent_id)
    else:
        logger.error(f"Unsupported msg type: {msg_type}")
        # respond = wxcpt.EncryptMsg("[Error]不支持的消息类型", nonce, timestamp)
        return wechat_sender.send_text_msg("[Error]不支持的消息类型", from_user, agent_id)
    



if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", 
                port=20052, 
                )
import os
import json
import datetime
import traceback

import openai
from loguru import logger
from dotenv import load_dotenv

project_path = os.path.dirname(os.path.dirname(__file__))
env_path = os.path.join(project_path, "conf/api-keys.env")
session_folder = os.path.join(project_path, "sessions")
load_dotenv(env_path)

openai.organization = "org-WL8jaKbBRVLeKS4Qjls4ZAhT"
openai.api_key = os.getenv("OPENAI_API_KEY")


class Messages:
    """
    Messages class for storing gpt chat history.
    """
    def __init__(self, user_id, session_id):
        self.user_id = user_id
        self.session_id = session_id
        self.messages = self.load()
    
    def init_message(self, init_content=None):
        # init messages, return a list of dict
        if init_content == None:
            return []
        else:
            return [
                {"role": "system", "content": init_content},
            ]
    
    def load(self):
        # loads local message history by users, if not exists, init a new one
        session_path = os.path.join(session_folder, self.user_id, self.session_id + ".json")
        if os.path.exists(session_path):
            with open(session_path, "r") as f:
                return json.load(f)
        else:
            return self.init_message()
        
    def save(self):
        # save the msg history to local
        session_path = os.path.join(session_folder, self.user_id, self.session_id + ".json")
        with open(session_path, "w", encoding="utf8") as f:
            json.dump(self.messages, f, ensure_ascii=False)
        

class ChatApp:
    """
    ChatApp class for gpt chat.
    """
    def __init__(self, user_id, user_session):
        session_type, session_id = user_session.get_session()
        self.msg = Messages(user_id, session_id)
        self.session_type = session_type
        if self.session_type:
            # multi conversation
            self.chat_params = {
                "max_tokens": 512,
            }
        else: 
            self.chat_params = {}
    
    def chat(self, message):
        self.msg.messages.append({"role": "user", "content": message})
        logger.info(("chat_params", self.chat_params))
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=self.msg.messages,
                **self.chat_params
            )
        except Exception as e:
            logger.error(traceback.format_exc())
            self.msg.messages.pop()
            return "抱歉，网络出现了一些问题，请稍后再试。"
        self.msg.messages.append({"role": "assistant", "content": response["choices"][0]["message"].content})
        self.msg.save()
        return response["choices"][0]["message"].content


class FakeChatApp(ChatApp):
    def chat(self, message):
        self.msg.messages.append({"role": "user", "content": message})
        response = f"Hi, zhen! This is my {sum(1 for msg in self.msg.messages if msg['role']=='assistant')}th message to you."
        self.msg.messages.append({"role": "assistant", "content": response})
        self.msg.save()
        return response


class UserSession:
    """
    UserSession class for storing user session.
    """
    def __init__(self, user_id):
        self.user_id = user_id
        self.lastest_session = self.load()
    
    def init_session(self):
        return {"session_id": 0, "iso_time": None, "multi_conversion": False}
    
    def load(self) -> list[dict]:
        # loads local session history by users, if not exists, init a new one
        session_path = os.path.join(session_folder, self.user_id, "latest_session.json")
        if os.path.exists(session_path):
            with open(session_path, "r") as f:
                return json.load(f)
        else:
            return self.init_session()
        
    def save(self):
        # save the session history to local
        session_path = os.path.join(session_folder, self.user_id, "latest_session.json")
        os.makedirs(os.path.dirname(session_path), exist_ok=True)
        with open(session_path, "w") as f:
            json.dump(self.lastest_session, f)
        
    def create_session(self, multi_conversion: bool):
        # create a new session, with a param to control if the session is multi-conversation.
        # replace the lastsession
        isotime = datetime.datetime.now().isoformat()
        session_id = self.lastest_session["session_id"] + 1
        self.lastest_session = {"session_id": session_id, "iso_time": isotime, "multi_conversion": multi_conversion}
        self.save()
        return None
    
    def get_session(self):
        # if the last session is not multi_conversion, create a new one with multi_conversion as false.
        if not self.lastest_session["multi_conversion"]:
            self.create_session(False)
        return (self.lastest_session["multi_conversion"],
                f"{self.lastest_session['session_id']}_{self.lastest_session['iso_time']}")
            

def chat(user, message):
    if message == "//新建多轮对话":
        msg = create_session(user, multi_conversion=True)
    elif message == "//新建单轮对话":
        msg = create_session(user, multi_conversion=False)
    else:
        user_session = UserSession(user)
        chatapp = ChatApp(user, user_session)
        msg = chatapp.chat(message)
    return msg

def fake_chat(user, message):
    if message == "//新建多轮对话":
        msg = create_session(user, multi_conversion=True)
    elif message == "//新建单轮对话":
        msg = create_session(user, multi_conversion=False)
    else:
        user_session = UserSession(user)
        chatapp = FakeChatApp(user, user_session)
        msg = chatapp.chat(message)
    return msg

def create_session(user, multi_conversion: bool):
    user_session = UserSession(user)
    user_session.create_session(multi_conversion)
    return f"您好，我是GPT-3.5-turbo，您可以和我进行{'多轮' if multi_conversion else '单轮'}聊天了。"


if __name__ == "__main__":
    print(create_session("zhen", multi_conversion=False))
    print(fake_chat("zhen", "如何使用企业微信bot进行回复？请举出python的例子。"))

    
    


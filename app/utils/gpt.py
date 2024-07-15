import copy
import json
import re

import openai
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse
from sqlalchemy.future import select

from app.models import GptUserContent
from app.utils.base64_decode import decode_env
import httpx
import asyncio

# from app.settings import redis_client

data = decode_env()
app = FastAPI()


class OpenAiGPT:
    def __init__(self):
        self.api_type = "azure"
        self.api_base = data["AZURE_OPENAI_URL"]
        self.api_version = "2023-05-15"
        self.api_key = data["AZURE_OPENAI_KEY"]

    async def send_messages(self, username, db, uid, messages_list):
        headers = {
            "Content-Type": "application/json",
            "api-key": self.api_key,
        }
        result = await db.execute(select(GptUserContent).filter(GptUserContent.uid == uid))
        gpt_user_content = result.scalar_one_or_none()
        if gpt_user_content:
            list_last5 = gpt_user_content.content[-5:]
            list_last5.extend(messages_list)
            messages_list = list_last5
        json_data = {
            "messages": messages_list,
            "model": "gpt-4o",
            "stream": True
        }

        async with (httpx.AsyncClient() as client):
            try:
                async with client.stream("POST",
                                         f"{self.api_base}/openai/deployments/gpt-4o/chat/completions?api-version={self.api_version}",
                                         headers=headers, json=json_data) as response:
                    # await redis_client.redis.delete(uid)
                    list_ = []
                    async for line in response.aiter_lines():
                        if line:
                            res = json.loads(re.search(r'data: (.*)', line).groups()[0])
                            if res.get("choices")[0].get("finish_reason") == "stop":
                                break
                            if res.get("choices")[0].get("delta").get("content"):
                                content = str(res.get("choices")[0].get("delta").get("content"))
                                # await redis_client.redis.rpush(uid, content)
                            if not res.get("choices")[0].get("delta").get("role"):
                                yield line
                                list_.append(str(res.get("choices")[0].get("delta").get("content")))
                    dict_user = {'role': 'user', 'content': messages_list[-1]['content']}
                    dict_assistant = {'role': 'assistant', 'content': ''.join(list_)}
                    list_db = [dict_user, dict_assistant]
                    result = await db.execute(select(GptUserContent).filter(GptUserContent.uid == uid))
                    gpt_user_content = result.scalar_one_or_none()

                    if not gpt_user_content:
                        # 插入操作
                        gpt_user_content = GptUserContent(username=username, content=list_db, uid=uid)
                        db.add(gpt_user_content)
                    else:
                        # 更新操作
                        gpt_user_content.content.extend(list_db)
                        # 手动标记为修改
                        from sqlalchemy.orm.attributes import flag_modified
                        flag_modified(gpt_user_content, "content")

                    # 尝试提交事务
                    await db.commit()
            except Exception as e:
                yield f"Error: {str(e)}"
                return

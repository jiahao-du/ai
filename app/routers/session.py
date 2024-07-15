import asyncio
import copy
import threading
import time
import uuid
from typing import List
import re
from fastapi import APIRouter, Body, Depends

from app.models import GptUserContent, Fkinds, Tkinds, user_tkinds_association, SensitiveWordRecord
from app.schemas import PromptRequest, User
from sse_starlette.sse import EventSourceResponse

from app.settings import get_db
from app.utils.gpt import OpenAiGPT
from app.utils.jwt_util import get_current_active_user
from sqlalchemy.ext.asyncio import AsyncSession
from functools import wraps
from app.settings import redis_client
from sqlalchemy.future import select

router = APIRouter()


def test_decorator(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        content = kwargs.get('request').prompt[0].get('content')
        db = kwargs.get('db')
        user_id = kwargs.get('current_user').id
        username = kwargs.get('current_user').username
        # 第一步：根据 user_id 选择 user_tkinds_association
        stmt = select(user_tkinds_association).filter_by(user_id=user_id)

        result = await db.execute(stmt)
        associations = result.all()

        # 第二步：遍历 associations
        for association in associations:
            # 根据 association 中的 tkinds_id 选择 Tkinds
            stmt = select(Tkinds).filter_by(id=association.tkinds_id)

            result = await db.execute(stmt)
            tkinds_item = result.scalar_one_or_none()

            # 第三步：检查 tkinds_item 是否具有 sen_word 属性
            if tkinds_item and tkinds_item.sen_word:
                # 第四步：遍历 sen_word，检查内容中是否存在任何敏感词
                list_sen_word = []
                for sen_word in tkinds_item.sen_word:
                    if sen_word in content:
                        list_sen_word.append(sen_word)
                if list_sen_word:
                    record = SensitiveWordRecord(content=tkinds_item.name + ':' + ','.join(list_sen_word),
                                                 username=username)
                    db.add(record)
                    await db.commit()
                    return "error"
            if tkinds_item and tkinds_item.regex:
                records = re.findall(rf'{tkinds_item.regex}', content)
                if records:
                    record = SensitiveWordRecord(content=tkinds_item.name + ':' + ",".join(records), username=username)
                    db.add(record)
                    await db.commit()
                    return "error"
        result = await func(*args, **kwargs)
        return result

    return wrapper


@router.post("/prompt/")
@test_decorator
async def process_prompt(request: PromptRequest,
                         current_user: User = Depends(get_current_active_user),
                         db: AsyncSession = Depends(get_db)):
    gpt = OpenAiGPT()
    message_stream = gpt.send_messages(current_user.username, db, request.uid, messages_list=request.prompt)
    return EventSourceResponse(message_stream)


@router.delete("/prompt/{uid}/")
async def process_prompt(uid: str,
                         current_user: User = Depends(get_current_active_user),
                         db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(GptUserContent).filter(GptUserContent.uid == uid))
    gpt_user_content = result.scalar_one_or_none()
    if gpt_user_content:
        await db.delete(gpt_user_content)
        await db.commit()
        return "success"
    return "error"

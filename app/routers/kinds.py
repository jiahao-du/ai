import copy
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Body, status
from sqlalchemy import delete, insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import SQLAlchemyError
from app.models import Fkinds, Skinds, Tkinds, User, user_tkinds_association
from app.schemas import KindsBase
from app.settings import get_db
from app.utils.pagination import paginate
from app.schemas import PaginationRequest

router = APIRouter()


@router.get("/kinds")
async def read_all(db: AsyncSession = Depends(get_db)):
    result = []
    async with db.begin():
        query = select(Fkinds).options(
            selectinload(Fkinds.skinds).selectinload(Skinds.tkinds)
        )
        fkinds_result = await db.execute(query)
        fkinds = fkinds_result.scalars().all()

        for fkind in fkinds:
            fkind_dict = {
                "id": fkind.id,
                "name": fkind.name,
                "description": fkind.description,
                "created_at": fkind.created_at,
                "children": []
            }
            for skind in fkind.skinds:
                skind_dict = {
                    "id": skind.id,
                    "name": skind.name,
                    "description": skind.description,
                    "created_at": skind.created_at,
                    "children": []
                }
                for tkind in skind.tkinds:
                    tkind_dict = {
                        "id": tkind.id,
                        "name": tkind.name,
                        "data_level": tkind.data_level,
                        "regex": tkind.regex,
                        "sen_word": tkind.sen_word,
                        "if_sen": tkind.if_sen,
                        "description": tkind.description,
                        "created_at": tkind.created_at
                    }
                    skind_dict["children"].append(tkind_dict)
                fkind_dict["children"].append(skind_dict)
            result.append(fkind_dict)
    return {"data": result}


@router.post("/kinds/")
async def create_kind(
        db: AsyncSession = Depends(get_db),
        kindsbase: KindsBase = Body(..., description="KindsBase")
) -> Dict[str, Any]:
    try:
        # if not (kindsbase.fname or kindsbase.sname or kindsbase.tname):
        #     raise HTTPException(status_code=400, detail="parameter error")
        if not kindsbase.fname:
            raise HTTPException(status_code=400, detail="parameter error")
        stmt = select(Fkinds).filter_by(name=kindsbase.fname)
        result = await db.execute(stmt)
        existing_fkind = result.scalar_one_or_none()
        if existing_fkind is None:
            # 如果不存在，创建新的
            fkind = Fkinds(name=kindsbase.fname, description=kindsbase.fdescription)
            db.add(fkind)
            await db.commit()
            await db.refresh(fkind)
        else:
            # 如果已存在，使用已存在的记录
            fkind = existing_fkind
        if kindsbase.sname:
            stmt = select(Skinds).filter_by(name=kindsbase.sname, parent_id=fkind.id)
            result = await db.execute(stmt)
            existing_skind = result.scalar_one_or_none()
            if existing_skind is None:
                # 如果不存在，创建新的
                skind = Skinds(name=kindsbase.sname, parent_id=fkind.id, description=kindsbase.sdescription)
                db.add(skind)
                await db.commit()
                await db.refresh(skind)
            else:
                # 如果已存在，使用已存在的记录
                skind = existing_skind
            if kindsbase.tname:
                stmt = select(Tkinds).filter_by(name=kindsbase.tname, parent_id=skind.id)
                result = await db.execute(stmt)
                existing_tkind = result.scalar_one_or_none()
                if existing_tkind is None:
                    # 如果不存在，创建新的
                    tkind = Tkinds(name=kindsbase.tname, parent_id=skind.id, data_level=kindsbase.tdata_level,
                                   regex=kindsbase.tregex, sen_word=kindsbase.tsen_word, if_sen=kindsbase.tif_sen,
                                   description=kindsbase.tdescription)
                    db.add(tkind)
                    await db.commit()
                    await db.refresh(tkind)
                else:
                    # 如果已存在，使用已存在的记录
                    tkind = existing_tkind
                    return {
                        "results": "分级分类已存在"
                    }
        return {
            "results": "分级分类创建成功"
        }
    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=f"Error occurred: {str(e)}")


@router.delete("/fkinds/{fkind_id}")
async def delete_fkinds(fkind_id: int, db: AsyncSession = Depends(get_db)):
    query = select(Fkinds).filter(Fkinds.id == fkind_id)
    result = await db.execute(query)
    fkind = result.scalar_one_or_none()

    if not fkind:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fkind not found")

    await db.delete(fkind)
    await db.commit()

    return {"message": "Fkind deleted successfully"}


@router.delete("/skinds/{skind_id}")
async def delete_skinds(skind_id: int, db: AsyncSession = Depends(get_db)):
    query = select(Skinds).filter(Skinds.id == skind_id)
    result = await db.execute(query)
    skind = result.scalar_one_or_none()

    if not skind:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Skind not found")

    await db.delete(skind)
    await db.commit()

    return {"message": "Skind deleted successfully"}


@router.delete("/tkinds/{tkind_id}")
async def delete_tkinds(tkind_id: int, db: AsyncSession = Depends(get_db)):
    query = select(Tkinds).filter(Tkinds.id == tkind_id)
    result = await db.execute(query)
    tkind = result.scalar_one_or_none()

    if not tkind:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tkind not found")

    await db.delete(tkind)
    await db.commit()

    return {"message": "Tkind deleted successfully"}


@router.put("/fkinds/{fkind_id}")
async def put_fkinds(fkind_id: int, db: AsyncSession = Depends(get_db),
                     fkindsbase: KindsBase = Body(..., description="KindsBase")):
    try:
        query = select(Fkinds).filter(Fkinds.id == fkind_id)
        result = await db.execute(query)
        fkind = result.scalar_one_or_none()

        if not fkind:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fkind not found")
        if fkindsbase.fname:
            fkind.name = fkindsbase.fname
        if fkindsbase.fdescription:
            fkind.description = fkindsbase.fdescription
        await db.commit()

        return {"message": "Fkind updated successfully"}
    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=f"Error occurred: {str(e)}")


@router.put("/skinds/{skind_id}")
async def put_skinds(skind_id: int, db: AsyncSession = Depends(get_db),
                     skindsbase: KindsBase = Body(..., description="KindsBase")):
    try:
        query = select(Skinds).filter(Skinds.id == skind_id)
        result = await db.execute(query)
        skind = result.scalar_one_or_none()

        if not skind:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Skind not found")
        if skindsbase.sname:
            skind.name = skindsbase.sname
        if skindsbase.sdescription:
            skind.description = skindsbase.sdescription
        await db.commit()

        return {"message": "Skind updated successfully"}
    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=f"Error occurred: {str(e)}")


@router.put("/tkinds/{tkind_id}")
async def put_tkinds(tkind_id: int, db: AsyncSession = Depends(get_db),
                     tkindsbase: KindsBase = Body(..., description="KindsBase")):
    try:
        query = select(Tkinds).filter(Tkinds.id == tkind_id)
        result = await db.execute(query)
        tkind = result.scalar_one_or_none()

        if not tkind:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tkind not found")
        if tkindsbase.tname:
            tkind.name = tkindsbase.tname
        if tkindsbase.tdescription:
            tkind.description = tkindsbase.tdescription
        if tkindsbase.tdata_level:
            tkind.data_level = tkindsbase.tdata_level
        if tkindsbase.tregex:
            tkind.regex = tkindsbase.tregex
        if tkindsbase.tsen_word:
            tkind.sen_word = tkindsbase.tsen_word
        if tkindsbase.tif_sen:
            tkind.if_sen = tkindsbase.tif_sen

        await db.commit()

        return {"message": "Tkind updated successfully"}
    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=f"Error occurred: {str(e)}")


@router.get("/fkinds/")
async def get_fkinds(db: AsyncSession = Depends(get_db)):
    query = select(Fkinds)
    result = await db.execute(query)
    fkinds = result.scalars().all()

    return fkinds


@router.get("/skinds/")
async def get_skinds(db: AsyncSession = Depends(get_db)):
    query = select(Skinds)
    result = await db.execute(query)
    skinds = result.scalars().all()

    return skinds


@router.get("/tkinds/")
async def get_tkinds(db: AsyncSession = Depends(get_db)):
    query = select(Tkinds)
    result = await db.execute(query)
    tkinds = result.scalars().all()

    return tkinds


@router.get("/kinds/{kind_id}")
async def get_kind(
        kind_id: int,
        db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    try:
        # 查询 Tkinds
        stmt = select(Tkinds).filter_by(id=kind_id)
        result = await db.execute(stmt)
        tkind = result.scalar_one_or_none()

        if not tkind:
            raise HTTPException(status_code=400, detail="kind not found")

        # 查询 Skinds
        stmt = select(Skinds).filter_by(id=tkind.parent_id)
        result = await db.execute(stmt)
        skind = result.scalar_one_or_none()

        # 查询 Fkinds
        stmt = select(Fkinds).filter_by(id=skind.parent_id)
        result = await db.execute(stmt)
        fkind = result.scalar_one_or_none()

        return {
            "tkind": {
                "id": tkind.id,
                "name": tkind.name,
                "data_level": tkind.data_level,
                "regex": tkind.regex,
                "sen_word": tkind.sen_word,
                "if_sen": tkind.if_sen,
                "description": tkind.description
            },
            "skind": {
                "id": skind.id,
                "name": skind.name,
                "description": skind.description
            },
            "fkind": {
                "id": fkind.id,
                "name": fkind.name,
                "description": fkind.description
            }
        }

    except SQLAlchemyError as e:
        raise HTTPException(status_code=400, detail=f"Error occurred: {str(e)}")


# @router.delete("/kinds/{id}")
# async def delete_kind(id: int, db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
#     try:
#         # 尝试删除 Tkinds
#         stmt = select(Tkinds).filter_by(id=id)
#         result = await db.execute(stmt)
#         tkind = result.scalar_one_or_none()
#         if len((await db.execute(select(Tkinds).filter_by(parent_id=tkind.parent_id))).all()) == 1:
#             result = await db.execute(select(Skinds).filter_by(id=tkind.parent_id))
#             skind = result.scalar_one_or_none()
#             if len((await db.execute(select(Skinds).filter_by(parent_id=skind.parent_id))).all()) == 1:
#                 result = await db.execute(select(Fkinds).filter_by(id=skind.parent_id))
#                 fkind = result.scalar_one_or_none()
#                 await db.delete(fkind)
#             else:
#                 await db.delete(skind)
#         else:
#             await db.delete(tkind)
#         await db.commit()
#         return {"results": f""}
#     except SQLAlchemyError as e:
#         await db.rollback()
#         raise HTTPException(status_code=400, detail=f"Error occurred: {str(e)}")
#
#
# @router.put("/kinds/{kind_id}")
# async def update_kind(
#         kind_id: int,
#         db: AsyncSession = Depends(get_db),
#         kindsbase: KindsBase = Body(..., description="KindsBase")
# ) -> Dict[str, Any]:
#     try:
#         # 更新 Fkinds
#         stmt = select(Tkinds).filter_by(id=kind_id)
#         result = await db.execute(stmt)
#         tkind = result.scalar_one_or_none()
#
#         if not tkind:
#             raise HTTPException(status_code=400, detail="kind not found")
#
#         tkind.name = kindsbase.tname
#         tkind.data_level = kindsbase.tdata_level
#         tkind.regex = kindsbase.tregex
#         tkind.sen_word = kindsbase.tsen_word
#         tkind.if_sen = kindsbase.tif_sen
#         tkind.description = kindsbase.tdescription
#
#         await db.commit()
#         await db.refresh(tkind)
#
#         stmt = select(Skinds).filter_by(id=tkind.parent_id)
#         result = await db.execute(stmt)
#         skind = result.scalar_one_or_none()
#
#         skind.name = kindsbase.sname
#         skind.description = kindsbase.sdescription
#         await db.commit()
#         await db.refresh(skind)
#
#         stmt = select(Fkinds).filter_by(id=skind.parent_id)
#         result = await db.execute(stmt)
#         fkind = result.scalar_one_or_none()
#         fkind.name = kindsbase.fname
#         fkind.description = kindsbase.fdescription
#         await db.commit()
#         await db.refresh(fkind)
#
#         return {
#             "results": "Data updated successfully"
#         }
#
#     except SQLAlchemyError as e:
#         await db.rollback()
#         raise HTTPException(status_code=400, detail=f"Error occurred: {str(e)}")


from fastapi.responses import JSONResponse


# @router.get("/kinds1/")
# async def read_kinds(
#         db: AsyncSession = Depends(get_db),
#         pagination: PaginationRequest = Depends(),
#         fname: Optional[str] = Query(None, description="fkinds name"),
#         sname: Optional[str] = Query(None, description="skinds name"),
#         tname: Optional[str] = Query(None, description="tkinds name")
# ) -> Dict[str, Any]:
#     # 构建基本查询语句
#     stmt = select(Fkinds).options(selectinload(Fkinds.skinds).selectinload(Skinds.tkinds))
#
#     # 添加模糊查询条件
#     if fname:
#         stmt = stmt.where(Fkinds.name.ilike(f"%{fname}%"))
#
#     if sname:
#         stmt = stmt.where(Skinds.name.ilike(f"%{sname}%"))
#
#     if tname:
#         stmt = stmt.where(Tkinds.name.ilike(f"%{tname}%"))
#
#     result = await db.execute(stmt)
#     fkinds = result.scalars().all()
#
#     response = [
#         {
#             "fkind": {
#                 "id": fkind.id,
#                 "name": fkind.name,
#                 "description": fkind.description,
#                 "created_at": fkind.created_at
#             },
#             "skind": {
#                 "id": skind.id,
#                 "name": skind.name,
#                 "parent_id": skind.parent_id,
#                 "description": skind.description,
#                 "created_at": skind.created_at
#             },
#             "tkind": {
#                 "id": tkind.id,
#                 "name": tkind.name,
#
#                 "parent_id": tkind.parent_id,
#                 "data_level": tkind.data_level,
#                 "regex": tkind.regex,
#                 "sen_word": tkind.sen_word,
#                 "if_sen": tkind.if_sen,
#                 "description": tkind.description,
#                 "created_at": tkind.created_at
#             }
#         }
#         for fkind in fkinds
#         for skind in fkind.skinds
#         for tkind in skind.tkinds
#         if (not fname or fname.lower() in fkind.name.lower())
#         if (not sname or sname.lower() in skind.name.lower())
#         if (not tname or tname.lower() in tkind.name.lower())
#     ]
#
#     paginated_response = paginate(response, pagination.page, pagination.page_size)
#     return paginated_response

#
# @router.get("/kinds2")
# async def read_all(db: AsyncSession = Depends(get_db),
#                    pagination: PaginationRequest = Depends()):
#     result = []
#     async with db.begin():
#         query = select(Fkinds).options(
#             selectinload(Fkinds.skinds).selectinload(Skinds.tkinds)
#         )
#         fkinds_result = await db.execute(query)
#         fkinds = fkinds_result.scalars().all()
#         kind_dict = {}
#         for fkind in fkinds:
#             fkind_dict = {
#                 "id": fkind.id,
#                 "name": fkind.name,
#                 "description": fkind.description,
#                 "created_at": fkind.created_at,
#             }
#             kind_dict['fkind'] = fkind_dict
#             if not fkind.skinds:
#                 kind_dict['id'] = fkind.id
#                 kind_dict["skinds"] = {}
#                 kind_dict["tkinds"] = {}
#                 result.append(copy.deepcopy(kind_dict))
#                 continue
#             for skind in fkind.skinds:
#                 skind_dict = {
#                     "id": skind.id,
#                     "name": skind.name,
#                     "description": skind.description,
#                     "created_at": skind.created_at,
#                 }
#                 kind_dict['skind'] = skind_dict
#                 if not skind.tkinds:
#                     kind_dict['id'] = skind.id
#                     kind_dict["tkinds"] = {}
#                     result.append(copy.deepcopy(kind_dict))
#
#                     continue
#                 for tkind in skind.tkinds:
#                     tkind_dict = {
#                         "id": tkind.id,
#                         "name": tkind.name,
#                         "data_level": tkind.data_level,
#                         "regex": tkind.regex,
#                         "sen_word": tkind.sen_word,
#                         "if_sen": tkind.if_sen,
#                         "description": tkind.description,
#                         "created_at": tkind.created_at
#                     }
#                     kind_dict['id'] = tkind.id
#                     kind_dict["tkinds"] = tkind_dict
#                     result.append(copy.deepcopy(kind_dict))
#     paginated_response = paginate(result, pagination.page, pagination.page_size)
#     return paginated_response
#
#
# # 新增的特定 id 查询路由
# @router.get("/kinds2/{id}")
# async def read_by_id(id: int, db: AsyncSession = Depends(get_db)):
#     try:
#         # 查询 Tkinds
#         stmt = select(Tkinds).filter_by(id=id)
#         result = await db.execute(stmt)
#         tkind = result.scalar_one_or_none()
#         if tkind:
#             # 查询 Skinds
#             stmt = select(Skinds).filter_by(id=tkind.parent_id)
#             result = await db.execute(stmt)
#             skind = result.scalar_one_or_none()
#
#             stmt = select(Fkinds).filter_by(id=skind.parent_id)
#             result = await db.execute(stmt)
#             fkind = result.scalar_one_or_none()
#
#             dict_kind = {
#                 "tkind": {
#                     "id": tkind.id,
#                     "name": tkind.name,
#                     "data_level": tkind.data_level,
#                     "regex": tkind.regex,
#                     "sen_word": tkind.sen_word,
#                     "if_sen": tkind.if_sen,
#                     "description": tkind.description
#                 },
#                 "skind": {
#                     "id": skind.id,
#                     "name": skind.name,
#                     "description": skind.description
#                 },
#                 "fkind": {
#                     "id": fkind.id,
#                     "name": fkind.name,
#                     "description": fkind.description
#                 }
#             }
#             return dict_kind
#         # 查询 Skinds
#         stmt = select(Skinds).filter_by(id=id)
#         result = await db.execute(stmt)
#         skind = result.scalar_one_or_none()
#         if not skind:
#             # 查询 Fkinds
#             stmt = select(Fkinds).filter_by(id=id)
#             result = await db.execute(stmt)
#             fkind = result.scalar_one_or_none()
#             dict_kind = {
#                 "tkind": {},
#                 "skind": {},
#                 "fkind": {
#                     "id": fkind.id,
#                     "name": fkind.name,
#                     "description": fkind.description
#                 }
#             }
#             return dict_kind
#         else:
#             # 查询 Fkinds
#             stmt = select(Fkinds).filter_by(id=skind.parent_id)
#             result = await db.execute(stmt)
#             fkind = result.scalar_one_or_none()
#             dict_kind = {
#                 "skind": {
#                     "id": skind.id,
#                     "name": skind.name,
#                     "description": skind.description
#                 },
#                 "fkind": {
#                     "id": fkind.id,
#                     "name": fkind.name,
#                     "description": fkind.description
#                 }
#             }
#             return dict_kind
#
#     except SQLAlchemyError as e:
#         raise HTTPException(status_code=400, detail=f"Error occurred: {str(e)}")

@router.post("/add_tkind_to_user/")
async def add_tkind_to_user(
        db: AsyncSession = Depends(get_db),
        users: List[int] = Body(...),
        tkinds: List[int] = Body(...)
):
    try:
        # 异步执行删除操作
        await db.execute(delete(user_tkinds_association))

        for user_id in users:
            for tkind_id in tkinds:
                await db.execute(insert(user_tkinds_association).values(user_id=user_id, tkinds_id=tkind_id))
        await db.commit()
        return {"message": "Added successfully"}
    except SQLAlchemyError as e:
        await db.rollback()  # 回滚事务以保证数据一致性
        raise HTTPException(status_code=400, detail=f"Error occurred: {str(e)}")


@router.get("/add_tkind_to_user/")
async def add_tkind_to_user(
        db: AsyncSession = Depends(get_db),
):
    stmt = select(user_tkinds_association)
    results = await db.execute(stmt)
    results = results.all()
    list_users = []
    list_tkinds = []
    for result in results:
        if result[0] not in list_users:
            list_users.append(result[0])
        if result[1] not in list_tkinds:
            list_tkinds.append(result[1])
    return {"users": list_users, "tkinds": list_tkinds}

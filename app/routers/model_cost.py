from fastapi import Depends, APIRouter, Body
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import ModelCost
from app.settings import get_db
from app.schemas import ModelCostBase, PaginationRequest
from sqlalchemy.future import select

from app.utils.openai_data import get_openai
from app.utils.pagination import paginate
from app.utils.tongyiqianwen_data import get_tongyiqianwen
from app.utils.wenxinyiyan import get_wenxinyiyan

router = APIRouter()


@router.post("/model_cost")
async def create_model_cost(model_cost: ModelCostBase = Body(..., description="ModelCostBase"),
                            db: AsyncSession = Depends(get_db)):
    try:
        ob = ModelCost(manufacturer=model_cost.manufacturer, model_name=model_cost.model_name,
                       input_price=model_cost.input_price, date=model_cost.date, unit=model_cost.unit,
                       output_price=model_cost.output_price, train_price=model_cost.train_price)
        db.add(ob)
        await db.commit()
        return {"result": "新增成功"}
    except Exception as e:
        return {"result": "新增失敗", "error": str(e)}


@router.get("/model_cost")
async def get_model_cost(db: AsyncSession = Depends(get_db),
                         pagination: PaginationRequest = Depends(),
                         manufacturer: str = None,
                         model_name: str = None,
                         ):
    stmt = select(ModelCost)
    if manufacturer:
        stmt = stmt.where(ModelCost.manufacturer.ilike(f'%{manufacturer}%'))
    if model_name:
        stmt = stmt.where(ModelCost.model_name.ilike(f'%{model_name}%'))
    result = await db.execute(stmt)
    response = result.scalars().all()
    paginated_response = paginate(response, pagination.page, pagination.page_size)
    return paginated_response


@router.get("/model_cost/pull_data")
async def pull_tongyiqianwen(db: AsyncSession = Depends(get_db),
                             model_name: str = ...):
    list_ = []
    if model_name == 'ty':
        data = get_tongyiqianwen()
    elif model_name == 'op':
        data = get_openai()
    elif model_name == 'wx':
        data = get_wenxinyiyan()
    else:
        return {'result': '请输入ty或op或wx'}
    for i in data:
        if model_name == 'ty':
            result = await db.execute(select(ModelCost).filter(ModelCost.manufacturer == i.get('manufacturer'),
                                                               ModelCost.model_name == i.get('model_name'),
                                                               ModelCost.input_price == i.get('input_price'),
                                                               ModelCost.output_price == i.get('output_price'), ))
            result = result.scalar_one_or_none()
            if result:
                continue
            dict_ = {
                "manufacturer": i.get('manufacturer'),
                "model_name": i.get('model_name'),
                "input_price": i.get('input_price'),
                "output_price": i.get('output_price'),
                "date": i.get('date'),
                "unit": i.get('unit'),
            }
        elif model_name == 'op':
            result = await db.execute(select(ModelCost).filter(ModelCost.manufacturer == i.get('Manufacturer'),
                                                               ModelCost.model_name == i.get('Model'),
                                                               ModelCost.input_price == i.get('Input'),
                                                               ModelCost.output_price == i.get('Output'),
                                                               ModelCost.train_price == i.get('Train'), ))
            result = result.scalar_one_or_none()
            if result:
                continue
            dict_ = {
                "manufacturer": i.get('Manufacturer'),
                "model_name": i.get('Model'),
                "input_price": i.get('Input'),
                "output_price": i.get('Output'),
                "train_price": i.get('Train'),
                "date": i.get('Date'),
                "unit": i.get('Unit'),
            }
        elif model_name == 'wx':
            result = await db.execute(select(ModelCost).filter(ModelCost.manufacturer == i.get('manufacturer'),
                                                               ModelCost.model_name == i.get('model_name'),
                                                               ModelCost.input_price == i.get('input'),
                                                               ModelCost.output_price == i.get('output'),
                                                               ModelCost.train_price == i.get('train'), ))
            result = result.scalar_one_or_none()
            if result:
                continue
            dict_ = {
                "manufacturer": i.get('manufacturer'),
                "model_name": i.get('model_name'),
                "input_price": i.get('input'),
                "output_price": i.get('output'),
                "train_price": i.get('train'),
                "date": i.get('date'),
                "unit": i.get('unit'),
            }
        list_.append(dict_)
        ob = ModelCost(**dict_)
        db.add(ob)
        await db.commit()
    if list_:
        return {"result": f"大模型价格表爬取{len(list_)}条数据"}
    return {"result": "大模型价格表已是最新数据"}


@router.get("/model_cost/pull_openai")
async def pull_tongyiqianwen(db: AsyncSession = Depends(get_db)):
    list_ = []
    for i in get_openai():
        result = await db.execute(select(ModelCost).filter(ModelCost.manufacturer == i.get('manufacturer'),
                                                           ModelCost.model_name == i.get('model_name'),
                                                           ModelCost.input_price == i.get('input_price'),
                                                           ModelCost.output_price == i.get('output_price'), ))
        result = result.scalar_one_or_none()
        if result:
            continue
        dict_ = {
            "manufacturer": i.get('manufacturer'),
            "model_name": i.get('model_name'),
            "input_price": i.get('input_price'),
            "output_price": i.get('output_price'),
            "date": i.get('date'),
            "unit": i.get('unit'),
        }
        list_.append(dict_)
        ob = ModelCost(**dict_)
        db.add(ob)
        await db.commit()
    if list_:
        return {"result": f"通义千问模型价格表爬取{len(list_)}条数据"}
    return {"result": "通义千问模型价格表已是最新数据"}


@router.get("/model_cost/{model_cost_id}")
async def get_model_cost(model_cost_id: int, db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(select(ModelCost).filter(ModelCost.id == model_cost_id))
        return result.scalar_one_or_none()
    except Exception as e:
        return {"message": "ModelCost not found", "error": str(e)}


@router.put("/model_cost/{model_cost_id}")
async def update_model_cost(model_cost_id: int, model_cost: ModelCostBase, db: AsyncSession = Depends(get_db)):
    try:
        db_model_cost = await db.get(ModelCost, model_cost_id)
        if db_model_cost:
            if model_cost.manufacturer:
                db_model_cost.manufacturer = model_cost.manufacturer
            if model_cost.model_name:
                db_model_cost.model_name = model_cost.model_name
            if model_cost.input_price:
                db_model_cost.input_price = model_cost.input_price
            if model_cost.output_price:
                db_model_cost.output_price = model_cost.output_price
            if model_cost.train_price:
                db_model_cost.train_price = model_cost.train_price
            if model_cost.date:
                db_model_cost.date = model_cost.date
            if model_cost.unit:
                db_model_cost.unit = model_cost.unit
            await db.commit()
            await db.refresh(db_model_cost)
            return db_model_cost
        else:
            return {"message": "ModelCost not found"}
    except Exception as e:
        return {"message": "Update failed", "error": str(e)}


@router.delete("/model_cost/{model_cost_id}")
async def delete_model_cost(model_cost_id: int, db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(select(ModelCost).filter(ModelCost.id == model_cost_id))
        db_model_cost = result.scalar_one_or_none()
        if db_model_cost:
            await db.delete(db_model_cost)
            await db.commit()
            return {"message": "ModelCost deleted"}
        else:
            return {"message": "ModelCost not found"}
    except Exception as e:
        return {"message": "Delete failed", "error": str(e)}

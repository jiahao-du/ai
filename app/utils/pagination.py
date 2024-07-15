from typing import List, Any, Dict


def paginate(
        items: List[Dict[str, Any]],
        page: int,
        page_size: int
) -> Dict[str, Any]:
    total = len(items)
    start = (page - 1) * page_size
    end = start + page_size

    paginated_items = items[start:end]
    # for item in paginated_items:
    #     if isinstance(item, dict):
    #         for key, value in item.items():
    #             if value is None:
    #                 item[key] = ""
    #     else:
    #         for key in item.__dict__:
    #             if getattr(item, key) is None:
    #                 setattr(item, key, "")

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "results": paginated_items
    }

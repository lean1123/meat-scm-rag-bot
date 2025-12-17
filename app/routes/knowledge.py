from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone



from app.services.auth_service import get_current_user, User
from app.configurations.weaviate_config import get_weaviate_client

# weaviate 4.x query helpers
try:
    from weaviate.classes.query import Filter
except Exception:
    Filter = None

router = APIRouter(tags=["Knowledge"], prefix="/knowledge")


def _ensure_collection(client, name: str):
    if not client.collections.exists(name):
        raise HTTPException(status_code=400, detail=f"Collection '{name}' chưa tồn tại. Vui lòng khởi tạo trước.")
    return client.collections.get(name)


@router.post("/upload", summary="Upload tri thức chăn nuôi vào Weaviate")
def upload_knowledge(items: List[Dict[str, Any]], user: User = Depends(get_current_user)):
    client = get_weaviate_client()
    if client is None:
        raise HTTPException(status_code=500, detail="Weaviate client chưa sẵn sàng")

    collection_name = "FarmingKnowledge"
    collection = _ensure_collection(client, collection_name)

    inserted = 0
    errors: List[str] = []

    for idx, item in enumerate(items):
        try:
            content = item.get("content")
            if not content:
                stage = item.get("stage", "")
                species = item.get("species", "")
                min_age_days = item.get("min_age_days", "")
                max_age_days = item.get("max_age_days", "")
                recommended_feed = item.get("recommended_feed", "")
                feed_dosage = item.get("feed_dosage", "")
                medication = item.get("medication", "")
                notes = item.get("notes", "")
                content = (
                    f"Tri thức: Giai đoạn {stage} của {species} từ {min_age_days} đến {max_age_days} ngày. "
                    f"Thức ăn: {recommended_feed} ({feed_dosage}). Thuốc: {medication}. Ghi chú: {notes}. "
                    f"Nguồn: {user.email} tại cơ sở {user.facilityID}."
                )

            data_object = {
                "content": content,
                "stage": item.get("stage"),
                "species": item.get("species"),
                "min_age_days": item.get("min_age_days"),
                "max_age_days": item.get("max_age_days"),
                "recommended_feed": item.get("recommended_feed"),
                "feed_dosage": item.get("feed_dosage"),
                "medication": item.get("medication"),
                "notes": item.get("notes"),
                # tag theo tổ chức (facilityID) để lọc
                "facilityID": user.facilityID,
            }
            # Không thay đổi schema, nhưng gắn email vào nội dung để phân biệt người dùng
            # Nếu schema có sẵn trường createdByEmail, ta có thể thêm: data_object["createdByEmail"] = user.email

            collection.data.insert(data_object)
            inserted += 1
        except Exception as e:
            errors.append(f"Item {idx}: {e}")

    if errors:
        return {"inserted": inserted, "errors": errors}
    return {"inserted": inserted, "facilityID": user.facilityID, "by": user.email, "timestamp": datetime.now(timezone.utc).isoformat()}


# New endpoint: list my uploaded knowledge
@router.get("/mine", summary="Danh sách tri thức đã upload của user hiện tại")
def get_my_knowledge(
    limit: int = Query(20, ge=1, le=200),
    offset: int = Query(0, ge=0),
    include_email: Optional[bool] = Query(False, description="Nếu true sẽ cố gắng lọc theo email (nếu schema có trường createdByEmail)."),
    user: User = Depends(get_current_user),
):
    """Trả về danh sách các document tri thức mà user hiện tại đã upload.

    Lọc chính theo facilityID; nếu include_email=True và schema chứa trường createdByEmail thì sẽ lọc thêm theo email.
    """
    client = get_weaviate_client()
    if client is None:
        raise HTTPException(status_code=500, detail="Weaviate client chưa sẵn sàng")

    collection_name = "FarmingKnowledge"
    collection = _ensure_collection(client, collection_name)

    try:
        # chua trien khai Filter API trong weaviate client hien tai
        include_email = false
        if Filter is None:
            raise HTTPException(status_code=500, detail="Weaviate Filter API không khả dụng trong phiên bản client hiện tại")

        base_filter = Filter.by_property("facilityID").equal(user.facilityID)
        if include_email:
            email_filter = Filter.by_property("createdByEmail").equal(user.email)
            final_filter = base_filter & email_filter
        else:
            final_filter = base_filter

        result = collection.query.fetch_objects(
            limit=limit,
            offset=offset,
            filters=final_filter,
        )

        mapped: List[Dict[str, Any]] = []
        # result.objects is a list of Objects with .properties and .uuid
        for obj in getattr(result, "objects", []):
            props = dict(getattr(obj, "properties", {}) or {})
            obj_id = getattr(obj, "uuid", None)
            if obj_id:
                props["_id"] = obj_id
            mapped.append(props)

        return {"count": len(mapped), "items": mapped, "facilityID": user.facilityID}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi truy vấn Weaviate: {e}")

from fastapi import APIRouter, Depends, Query, HTTPException
from pymongo.database import Database
from bson import ObjectId
from app.configurations.mongo_config import get_db
from app.repositories.message_repository import MessageRepository
from app.services.auth_service import get_current_user, User

router = APIRouter()


@router.get("/conversations/{conversation_id}/messages")
async def get_messages_by_conversation(
        conversation_id: str,
        limit: int = Query(default=50, le=100, ge=1),
        offset: int = Query(default=0, ge=0),
        db: Database = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """
    Get messages by conversation ID with optional limit
    Query parameters:
    - limit: number of messages to return (default: 50, max: 100)
    - offset: number of messages to skip (default: 0)
    """
    try:

        if current_user is None:
            raise HTTPException(status_code=401, detail="Unauthorized")

        # Validate and convert conversation_id to ObjectId
        try:
            convo_id = ObjectId(conversation_id)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid conversation ID format")

        # Get messages using repository
        message_repo = MessageRepository(db)
        all_messages = message_repo.get_by_conversation_id(convo_id)

        # Apply pagination
        total_messages = len(all_messages)
        paginated_messages = all_messages[offset:offset + limit]

        # Convert to response format
        messages_data = []
        for message in paginated_messages:
            messages_data.append({
                'id': str(message.id),
                'conversation_id': str(message.conversation_id),
                'content': message.content,
                'sender_type': message.sender_type,
                'sender_id': message.sender_id,
                'timestamp': message.timestamp.isoformat()
            })

        return {
            'success': True,
            'data': {
                'messages': messages_data,
                'total': len(messages_data),
                'total_messages': total_messages,
                'limit': limit,
                'offset': offset
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

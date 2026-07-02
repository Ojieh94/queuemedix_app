from fastapi import APIRouter, Depends, status
from src.app.core.dependencies import get_current_user
from sqlalchemy.ext.asyncio.session import AsyncSession
from src.app.schemas import ReviewCreate, ReviewRead
from src.app.models import User
from src.app.services import review
from src.app.database.main import get_session


review_router = APIRouter(
    tags=['Reviews']
)


@review_router.post("/reviews", response_model=ReviewRead, status_code=status.HTTP_201_CREATED,)
async def create_review(
    review_data: ReviewCreate,
    current_user: User=Depends(get_current_user),
    session: AsyncSession=Depends(get_session),
):
    return await review.create_review(
        review_data=review_data,
        current_user=current_user,
        session=session,
    )
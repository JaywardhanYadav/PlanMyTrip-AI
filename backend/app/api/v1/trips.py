import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ...core.database import get_db_session
from ...models.trip import Trip
from ...models.trip_thread import TripThread
from ...models.user import User
from ...schemas.trip import TripCreate, TripResponse
from ..dependencies import get_current_user

router = APIRouter(prefix="/trips", tags=["trips"])


@router.post("", response_model=TripResponse, status_code=status.HTTP_201_CREATED)
async def create_trip(
    data: TripCreate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> TripResponse:
    trip = Trip(
        user_id=user.id,
        title=data.title,
        destination=data.destination,
        start_date=data.start_date,
        end_date=data.end_date,
        budget_total=data.budget_total,
        currency=data.currency,
        status="planning",
    )
    session.add(trip)
    await session.flush()

    langgraph_thread_id = f"thread_{uuid.uuid4().hex}"
    thread = TripThread(
        trip_id=trip.id,
        user_id=user.id,
        langgraph_thread_id=langgraph_thread_id,
    )
    session.add(thread)
    await session.commit()
    await session.refresh(trip)

    return TripResponse(
        id=trip.id,
        user_id=trip.user_id,
        title=trip.title,
        destination=trip.destination,
        start_date=trip.start_date,
        end_date=trip.end_date,
        budget_total=trip.budget_total,
        currency=trip.currency,
        status=trip.status,
        created_at=trip.created_at,
        thread_id=langgraph_thread_id,
    )


@router.get("", response_model=list[TripResponse])
async def list_trips(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> list[TripResponse]:
    stmt = (
        select(Trip)
        .where(Trip.user_id == user.id)
        .options(selectinload(Trip.thread))
        .order_by(Trip.created_at.desc())
    )
    result = await session.execute(stmt)
    trips = result.scalars().all()

    return [
        TripResponse(
            id=t.id,
            user_id=t.user_id,
            title=t.title,
            destination=t.destination,
            start_date=t.start_date,
            end_date=t.end_date,
            budget_total=t.budget_total,
            currency=t.currency,
            status=t.status,
            created_at=t.created_at,
            thread_id=t.thread.langgraph_thread_id if t.thread else None,
        )
        for t in trips
    ]


@router.get("/{trip_id}", response_model=TripResponse)
async def get_trip(
    trip_id: uuid.UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> TripResponse:
    stmt = (
        select(Trip)
        .where(Trip.id == trip_id, Trip.user_id == user.id)
        .options(selectinload(Trip.thread))
    )
    result = await session.execute(stmt)
    trip = result.scalar_one_or_none()
    if not trip:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trip not found")

    return TripResponse(
        id=trip.id,
        user_id=trip.user_id,
        title=trip.title,
        destination=trip.destination,
        start_date=trip.start_date,
        end_date=trip.end_date,
        budget_total=trip.budget_total,
        currency=trip.currency,
        status=trip.status,
        created_at=trip.created_at,
        thread_id=trip.thread.langgraph_thread_id if trip.thread else None,
    )

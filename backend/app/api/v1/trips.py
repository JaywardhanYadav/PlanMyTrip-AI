import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ...core.database import get_db_session
from ...models.chat_message import ChatMessage
from ...models.conversation_intake import ConversationIntake
from ...models.trip import Trip
from ...models.trip_thread import TripThread
from ...models.user import User
from ...schemas.trip import (
    ChatMessageResponse,
    ConversationIntakeResponse,
    ConversationIntakeUpdate,
    TripCreate,
    TripResponse,
)
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
        departure_station=data.departure_station,
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

    intake = ConversationIntake(
        trip_id=trip.id,
        user_id=user.id,
        departure_station=data.departure_station,
        destination=data.destination,
        start_date=data.start_date,
        end_date=data.end_date,
        budget_amount=data.budget_total,
        currency=data.currency,
    )
    session.add(intake)

    await session.commit()
    await session.refresh(trip)

    return TripResponse(
        id=trip.id,
        user_id=trip.user_id,
        title=trip.title,
        departure_station=trip.departure_station,
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
            departure_station=t.departure_station,
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
        departure_station=trip.departure_station,
        destination=trip.destination,
        start_date=trip.start_date,
        end_date=trip.end_date,
        budget_total=trip.budget_total,
        currency=trip.currency,
        status=trip.status,
        created_at=trip.created_at,
        thread_id=trip.thread.langgraph_thread_id if trip.thread else None,
    )


@router.get("/{trip_id}/messages", response_model=list[ChatMessageResponse])
async def list_trip_messages(
    trip_id: uuid.UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> list[ChatMessageResponse]:
    stmt = (
        select(ChatMessage)
        .where(ChatMessage.trip_id == trip_id, ChatMessage.user_id == user.id)
        .order_by(ChatMessage.created_at.asc())
    )
    result = await session.execute(stmt)
    messages = result.scalars().all()

    return [
        ChatMessageResponse(
            id=m.id,
            trip_id=m.trip_id,
            role=m.role,
            content=m.content,
            created_at=m.created_at,
        )
        for m in messages
    ]


@router.get("/{trip_id}/intake", response_model=ConversationIntakeResponse)
async def get_conversation_intake(
    trip_id: uuid.UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> ConversationIntakeResponse:
    stmt = select(ConversationIntake).where(
        ConversationIntake.trip_id == trip_id,
        ConversationIntake.user_id == user.id,
    )
    result = await session.execute(stmt)
    intake = result.scalar_one_or_none()
    if not intake:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation intake not found")

    return ConversationIntakeResponse(
        id=intake.id,
        trip_id=intake.trip_id,
        departure_station=intake.departure_station,
        destination=intake.destination,
        start_date=intake.start_date,
        end_date=intake.end_date,
        budget_amount=intake.budget_amount,
        currency=intake.currency,
        created_at=intake.created_at,
    )


@router.put("/{trip_id}/intake", response_model=ConversationIntakeResponse)
async def update_conversation_intake(
    trip_id: uuid.UUID,
    update_data: ConversationIntakeUpdate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> ConversationIntakeResponse:
    stmt = select(ConversationIntake).where(
        ConversationIntake.trip_id == trip_id,
        ConversationIntake.user_id == user.id,
    )
    result = await session.execute(stmt)
    intake = result.scalar_one_or_none()
    if not intake:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation intake not found")

    if update_data.departure_station is not None:
        intake.departure_station = update_data.departure_station
    if update_data.destination is not None:
        intake.destination = update_data.destination
    if update_data.start_date is not None:
        intake.start_date = update_data.start_date
    if update_data.end_date is not None:
        intake.end_date = update_data.end_date
    if update_data.budget_amount is not None:
        intake.budget_amount = update_data.budget_amount
    if update_data.currency:
        intake.currency = update_data.currency

    trip_stmt = select(Trip).where(Trip.id == trip_id, Trip.user_id == user.id)
    trip_res = await session.execute(trip_stmt)
    trip = trip_res.scalar_one_or_none()
    if trip:
        if update_data.departure_station:
            trip.departure_station = update_data.departure_station
        if update_data.destination:
            trip.destination = update_data.destination
        if update_data.start_date is not None:
            trip.start_date = update_data.start_date
        if update_data.end_date is not None:
            trip.end_date = update_data.end_date
        if update_data.budget_amount is not None:
            trip.budget_total = update_data.budget_amount
        if update_data.currency:
            trip.currency = update_data.currency

    await session.commit()
    await session.refresh(intake)

    return ConversationIntakeResponse(
        id=intake.id,
        trip_id=intake.trip_id,
        departure_station=intake.departure_station,
        destination=intake.destination,
        start_date=intake.start_date,
        end_date=intake.end_date,
        budget_amount=intake.budget_amount,
        currency=intake.currency,
        created_at=intake.created_at,
    )


@router.delete("/{trip_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_trip(
    trip_id: uuid.UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> None:
    stmt = (
        select(Trip)
        .where(Trip.id == trip_id, Trip.user_id == user.id)
        .options(
            selectinload(Trip.thread),
            selectinload(Trip.messages),
            selectinload(Trip.intake),
        )
    )
    result = await session.execute(stmt)
    trip = result.scalar_one_or_none()
    if not trip:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trip not found")

    await session.delete(trip)
    await session.commit()


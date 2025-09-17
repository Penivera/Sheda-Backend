from fastapi import APIRouter, status, Query
from app.services.user_service import ActiveUser, ActiveClient, ActiveAgent
from app.services.profile import (
    update_user,
    create_new_payment_info,
    get_account_info,
    update_account_info,
    run_account_info_deletion,
)
from core.dependecies import DBSession
from app.schemas.user_schema import (
    UserShow,
    UserUpdate,
    AccountInfoBase,
    AccountInfoShow,
)
from typing import List
from app.schemas.property_schema import (
    AppointmentSchema,
    AppointmentShow,
    AvailabilityShow,
    AgentAvailabilitySchema,
    ContractResponse,
    ContractCreate,
)
from app.services.listing import (
    run_book_appointment,
    create_availability,
    fetch_schedule,
    update_agent_availabilty,
    cancel_appointment_by_id,
    get_payment_info,  # type: ignore # type: ignore # type: ignore
    confirm_payment,
    proccess_approve_payment,
    run_create_contract,
)
from typing import Optional


router = APIRouter(
    tags=["User"],
    prefix="/user",
)


# NOTE -  Get the current user data
@router.get(
    "/me",
    response_model=UserShow,
    description="Get Current User Profile",
    status_code=status.HTTP_200_OK,
)
async def get_me(current_user: ActiveUser):
    return current_user


update_desc = """pick the target field and exclude the rest,
the server will dynamically update,all fields are optional"""


# NOTE - Update User Profile
@router.put(
    "/update/me",
    response_model=UserUpdate,
    description=update_desc,
    status_code=status.HTTP_202_ACCEPTED,
)
async def update_me(current_user: ActiveUser, update_data: UserUpdate, db: DBSession) -> ActiveUser:
    return await update_user(update_data, db, current_user)


# NOTE - Delete
@router.delete("/me", status_code=status.HTTP_202_ACCEPTED)
async def delete_account(current_user: ActiveUser, db: DBSession):
    current_user.is_active = False
    current_user.is_deleted = True
    db.add(current_user)
    await db.commit()
    await db.refresh(current_user)


# NOTE Get agent availability
@router.get(
    "/book-appointment", status_code=status.HTTP_200_OK, response_model=AppointmentShow
)
async def book_appointment(
    current_user: ActiveClient, payload: AppointmentSchema, db: DBSession
):
    return await run_book_appointment(
        client_id=current_user.id,
        agent_id=payload.agent_id,
        property_id=payload.property_id,
        requested_time=payload.requested_time,
        db=db,
    )


# NOTE Cancel Appointment
@router.delete(
    "/cancel-appointment/{appointment_id}",
    status_code=status.HTTP_200_OK,
    response_model=dict,
)
async def cancel_aappointment(
    appointment_id: int, current_user: ActiveUser, db: DBSession
):
    return await cancel_appointment_by_id(appointment_id, current_user, db)


@router.post(
    "/create-payment-info",
    status_code=status.HTTP_200_OK,
    response_model=AccountInfoShow,
)
async def create_payment_info(
    data: AccountInfoBase, db: DBSession, current_user: ActiveUser
):
    return await create_new_payment_info(data, db, current_user)


# NOTE Get user account info by the current user or a specified ID
@router.get(
    "/payment-info",
    status_code=status.HTTP_200_OK,
    response_model=List[AccountInfoShow],
)
async def get_payment_info( # type: ignore
    *, user_id: Optional[int] = Query(None), db: DBSession, current_user: ActiveUser
):  # type: ignore # type: ignore
    user_id = user_id or current_user.id
    return await get_account_info(db, user_id)  # type: ignore


@router.put(
    "/update-account-info/{account_info_id}",
    status_code=status.HTTP_200_OK,
    response_model=AccountInfoShow,
)
async def update_payment_info(
    update_data: AccountInfoBase,
    account_info_id: int,
    current_user: ActiveUser,
    db: DBSession,
):
    return await update_account_info(update_data, db, current_user, account_info_id)


@router.delete(
    "/delete-accnt-info/{account_info_id}",
    status_code=status.HTTP_201_CREATED,
    response_model=dict,
)
async def delete_account_info(
    account_info_id: int, current_user: ActiveUser, db: DBSession
):
    return await run_account_info_deletion(current_user, db, account_info_id)


@router.get(
    "/payment-info/{contract_id}",
    response_model=AccountInfoBase,
    status_code=status.HTTP_200_OK,
)
async def get_payment_info(contract_id: int, db: DBSession, current_user: ActiveUser):
    return await get_payment_info(contract_id, db)  # type: ignore


# NOTE create availability
@router.post(
    "/create-available-time",
    status_code=status.HTTP_201_CREATED,
    response_model=AvailabilityShow,
)
async def create_schedule(
    request: AgentAvailabilitySchema, current_user: ActiveAgent, db: DBSession
):
    return await create_availability(request, db, current_user)


@router.get(
    "/get-schedule/me",
    status_code=status.HTTP_200_OK,
    response_model=List[AvailabilityShow],
)
async def get_schedule(current_user: ActiveAgent, db: DBSession):
    return await fetch_schedule(current_user.id, db)


@router.put(
    "/update-schedule/{schedule_id}",
    response_model=AvailabilityShow,
    status_code=status.HTTP_200_OK,
)
async def update_schedule(
    schedule_id: int,
    update_data: AgentAvailabilitySchema,
    current_user: ActiveAgent,
    db: DBSession,
):
    return await update_agent_availabilty(update_data, db, schedule_id, current_user)  # type: ignore # type: ignore


@router.post(
    "/confirm-payment/{contract_id}",
    status_code=status.HTTP_200_OK,
    response_model=dict,
)
async def confirm_client_payment(contract_id: int, db: DBSession, user: ActiveClient):
    return await confirm_payment(contract_id, db)


@router.post(
    "/approve-payment/{contract_id}",
    status_code=status.HTTP_200_OK,
    response_model=dict,
)
async def approve_payment(contract_id: int, db: DBSession, user: ActiveAgent):
    return await proccess_approve_payment(contract_id, db)


@router.post(
    "/contracts/", response_model=ContractResponse, status_code=status.HTTP_201_CREATED
)
async def create_contract(
    data: ContractCreate, current_user: ActiveClient, db: DBSession
):
    return await run_create_contract(data, db, current_user)

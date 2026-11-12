from fastapi import APIRouter

from app.schemas.participant import DisqualifyRequest
from app.services import participant_service

router = APIRouter(prefix="/api/participants", tags=["Participants"])


@router.get("/{participant_id}")
def get_participant(participant_id: int):
    p = participant_service.find_participant(participant_id)
    return participant_service.with_details(p)


@router.delete("/{participant_id}", status_code=204)
def withdraw_participant(participant_id: int):
    participant_service.withdraw_participant(participant_id)


@router.post("/{participant_id}/disqualify")
def disqualify_participant(participant_id: int, data: DisqualifyRequest):
    return participant_service.disqualify_participant(participant_id, data)
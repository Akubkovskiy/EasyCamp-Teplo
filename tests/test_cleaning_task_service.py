from app.models import CleaningTaskStatus
from app.services.cleaning_task_service import CleaningTaskService


def test_can_transition_valid_paths():
    assert CleaningTaskService.can_transition(CleaningTaskStatus.PENDING, CleaningTaskStatus.ACCEPTED)
    assert CleaningTaskService.can_transition(CleaningTaskStatus.ACCEPTED, CleaningTaskStatus.IN_PROGRESS)
    assert CleaningTaskService.can_transition(CleaningTaskStatus.IN_PROGRESS, CleaningTaskStatus.DONE)


def test_can_transition_reject_invalid_paths():
    assert not CleaningTaskService.can_transition(CleaningTaskStatus.PENDING, CleaningTaskStatus.DONE)
    assert not CleaningTaskService.can_transition(CleaningTaskStatus.DONE, CleaningTaskStatus.ACCEPTED)

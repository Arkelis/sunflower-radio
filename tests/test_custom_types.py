from sunflower.core.custom_types import Step, UpdateInfo


def test_update_info_unpacking():
    should_notify, step = UpdateInfo(should_notify_update=True, step=Step.none())
    assert (should_notify, step) == (True, Step.none())

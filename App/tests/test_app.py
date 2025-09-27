import os, tempfile, pytest, logging, unittest
from werkzeug.security import check_password_hash, generate_password_hash

from App.main import create_app
from App.database import db, create_db
from App.models import User, Shift, TimeLog, LeaveRequest, SwapRequest
from App.controllers import (
    create_user,
    get_all_users_json,
    get_user
)
from datetime import datetime, date, time


LOGGER = logging.getLogger(__name__)

'''
   Unit Tests
'''
class UserUnitTests(unittest.TestCase):

    def test_new_user(self):
        user = User("bob", "bobpass", "staff")
        assert user.username == "bob"
        assert user.role == "staff"

    # pure function no side effects or integrations called
    def test_get_json(self):
        user = User("bob", "bobpass", "staff")
        user_json = user.get_json()
        expected = {"id": None, "username": "bob", "role": "staff"}
        self.assertDictEqual(user_json, expected)
    
    def test_hashed_password(self):
        password = "mypass"
        user = User("bob", password, "staff")
        assert user.password != password

    def test_check_password(self):
        password = "mypass"
        user = User("bob", password, "staff")
        assert user.check_password(password)

'''
    Integration Tests
'''

# This fixture creates an empty database for the test and deletes it after the test
# scope="class" would execute the fixture once and resued for all methods in the class
@pytest.fixture(autouse=True, scope="module")
def empty_db():
    app = create_app({'TESTING': True, 'SQLALCHEMY_DATABASE_URI': 'sqlite:///test.db'})
    create_db()
    yield app.test_client()
    db.drop_all()


def test_authenticate():
    user = create_user("bob", "bobpass", "staff")
    assert user is not None

class UsersIntegrationTests(unittest.TestCase):

    def test_create_user(self):
        user = create_user("rick", "bobpass", "staff")
        assert user.username == "rick"

    def test_get_all_users_json(self):
        users_json = get_all_users_json()
        # Test that we get a list back
        assert isinstance(users_json, list)

    def test_get_user(self):
        user = create_user("test_user", "testpass", "staff")
        retrieved_user = get_user(user.id)
        assert retrieved_user.username == "test_user"


class ShiftUnitTests(unittest.TestCase):

    def test_new_shift(self):
        shift = Shift(
            user_id=1,
            start_time=datetime(2025, 10, 1, 9, 0),
            end_time=datetime(2025, 10, 1, 17, 0)
        )
        assert shift.user_id == 1
        assert shift.status == "scheduled"

    def test_duration_hours(self):
        shift = Shift(
            user_id=1,
            start_time=datetime(2025, 10, 1, 9, 0),
            end_time=datetime(2025, 10, 1, 17, 0)
        )
        assert shift.duration_hours() == 8.0

    def test_overlaps(self):
        shift = Shift(
            user_id=1,
            start_time=datetime(2025, 10, 1, 9, 0),
            end_time=datetime(2025, 10, 1, 17, 0)
        )
        # Test overlap
        overlaps = shift.overlaps(
            datetime(2025, 10, 1, 15, 0),
            datetime(2025, 10, 1, 18, 0)
        )
        assert overlaps is True
        
        # Test no overlap
        no_overlap = shift.overlaps(
            datetime(2025, 10, 1, 18, 0),
            datetime(2025, 10, 1, 22, 0)
        )
        assert no_overlap is False


class TimeLogUnitTests(unittest.TestCase):

    def test_new_timelog(self):
        timelog = TimeLog(shift_id=1, user_id=1)
        assert timelog.shift_id == 1
        assert timelog.user_id == 1

    def test_worked_minutes(self):
        timelog = TimeLog(shift_id=1, user_id=1)
        timelog.clock_in = datetime(2025, 10, 1, 9, 0)
        timelog.clock_out = datetime(2025, 10, 1, 10, 30)
        assert timelog.worked_minutes() == 90

    def test_is_open(self):
        timelog = TimeLog(shift_id=1, user_id=1)
        timelog.clock_in = datetime.now()
        assert timelog.is_open() is True
        
        timelog.clock_out = datetime.now()
        assert timelog.is_open() is False


class LeaveRequestUnitTests(unittest.TestCase):

    def test_new_leave_request(self):
        leave_req = LeaveRequest(
            requester_id=1,
            start_date=date(2025, 10, 1),
            end_date=date(2025, 10, 3),
            type="vacation",
            reason="Family vacation"
        )
        assert leave_req.requester_id == 1
        assert leave_req.type == "vacation"
        assert leave_req.status == "pending"

    def test_approve_leave(self):
        leave_req = LeaveRequest(
            requester_id=1,
            start_date=date(2025, 10, 1),
            end_date=date(2025, 10, 3),
            type="vacation"
        )
        leave_req.approve(2)
        assert leave_req.status == "approved"
        assert leave_req.approver_id == 2


class SwapRequestUnitTests(unittest.TestCase):

    def test_new_swap_request(self):
        swap_req = SwapRequest(
            shift_id=1,
            from_user_id=1,
            to_user_id=2,
            note="Need to swap"
        )
        assert swap_req.shift_id == 1
        assert swap_req.from_user_id == 1
        assert swap_req.to_user_id == 2
        assert swap_req.status == "pending"
        


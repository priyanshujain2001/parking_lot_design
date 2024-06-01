from src.slots import Slots 
from src.parking_gate_system import ParkingGateSystem
from src.user import User
class ParkingLot:
    def __init__(self):
        self.slot_manager = Slots()
        self.gate_system = ParkingGateSystem()

    def park_vehicle(self, user_id, vehicle_type):
        ticket_id = self.gate_system.create_new_ticket(user_id, vehicle_type)
        return ticket_id

    def leave_parking(self, ticket_id):
        price = self.gate_system.add_out_time(ticket_id)
        return price

    def get_available_slots(self):
        return self.slot_manager.return_all_available_slots()

    def add_user_balance(self, user_id, amount):
        user = User(user_id)
        user.add_balance(amount)
    def check_user_balance(self, user_id):
        user = User(user_id)
        return user.get_balance()


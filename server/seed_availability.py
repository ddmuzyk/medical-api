from db_connection import DbPool
from queries.appointment import AppointmentQueryManager
from queries.user import UserQueryManager
import datetime as dt


def generate_time_slots_for_day(date: dt.date):
    """Generate 30-minute slots from 09:00 to 15:00 (last slot 14:30-15:00)"""
    slots = []
    start_hour = 9
    end_hour = 15
    current = dt.datetime.combine(date, dt.time(hour=start_hour, minute=0))
    end_dt = dt.datetime.combine(date, dt.time(hour=end_hour, minute=0))
    while current < end_dt:
        slot_start = current
        slot_end = current + dt.timedelta(minutes=30)
        if slot_end <= end_dt:
            slots.append((slot_start, slot_end))
        current = slot_end
    return slots


def seed_availability(days_ahead: int = 14):
    today = dt.date.today()
    end_date = today + dt.timedelta(days=days_ahead - 1)

    with DbPool.cursor() as cur:
        user_mgr = UserQueryManager(cur)
        appt_mgr = AppointmentQueryManager(cur)

        # Fetch all doctors
        cur.execute("SELECT id, first_name, last_name, specialization FROM doctors")
        doctors = cur.fetchall() or []

        if not doctors:
            print("No doctors found in database. Nothing to seed.")
            return

        total_created = 0
        total_skipped = 0

        for doctor in doctors:
            doctor_id = doctor.get('id')
            print(f"Seeding availability for doctor id={doctor_id}...")

            # iterate days
            curr = today
            while curr <= end_date:
                # only weekdays Mon-Fri
                if curr.weekday() < 5:
                    slots = generate_time_slots_for_day(curr)
                    for start_dt, end_dt in slots:
                        try:
                            appt_mgr.create_doctor_availability(
                                doctor_id=doctor_id,
                                start_time=start_dt,
                                end_time=end_dt,
                                is_available=True,
                            )
                            total_created += 1
                        except Exception as e:
                            # Overlaps or existing slot -> skip without failing
                            total_skipped += 1
                curr = curr + dt.timedelta(days=1)

        print(f"Seeding completed. Created: {total_created}, Skipped (existing/overlap): {total_skipped}")


if __name__ == '__main__':
    print("Starting availability seeding for next 14 days (weekdays only)...")
    seed_availability(14)
    print("Done.")

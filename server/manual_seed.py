from db_connection import DbPool
import datetime as dt


def main():
    conn = DbPool.getconn()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM doctor_availability WHERE EXTRACT(DOW FROM start_time) IN (0,6)")
        email = 'seed_doctor@example.com'
        password_hash = ''
        role = 'doctor'
        is_active = True
        created_at = dt.datetime.now()

        cur.execute(
            """
            INSERT INTO users (email, password_hash, role, is_active, created_at)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id
            """,
            (email, password_hash, role, is_active, created_at)
        )
        res = cur.fetchone()
        if not res:
            raise Exception('Inserting user affected 0 rows')
        user_id = res[0]
        print('inserted user_id', user_id)

        
        first_name = 'Seed'
        last_name = 'Doctor'
        specialization = 'cardiology'
        license_number = 'SEED-001'

        cur.execute(
            """
            INSERT INTO doctors (user_id, first_name, last_name, specialization, license_number)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id
            """,
            (user_id, first_name, last_name, specialization, license_number)
        )
        res = cur.fetchone()
        if not res:
            raise Exception('Inserting doctor affected 0 rows')
        doctor_id = res[0]
        print('inserted doctor_id', doctor_id)

        
        slots_to_create = 5
        created = 0
        day = dt.date.today() + dt.timedelta(days=1)
        while created < slots_to_create:
            if day.weekday() < 5:
                start_hour = 9
                minutes = [0, 30]
                for m in minutes:
                    if created >= slots_to_create:
                        break
                    start_dt = dt.datetime.combine(day, dt.time(hour=start_hour, minute=m))
                    end_dt = start_dt + dt.timedelta(minutes=30)
                    cur.execute(
                        """
                        INSERT INTO doctor_availability (doctor_id, is_available, start_time, end_time)
                        VALUES (%s, %s, %s, %s)
                        RETURNING id
                        """,
                        (doctor_id, True, start_dt, end_dt)
                    )
                    res = cur.fetchone()
                    if not res:
                        raise Exception('Inserting availability affected 0 rows')
                    created += 1
            day = day + dt.timedelta(days=1)

        conn.commit()

        print('created availability_slots', created)

    finally:
        try:
            cur.close()
        except Exception:
            pass
        DbPool.putconn(conn)


if __name__ == '__main__':
    main()

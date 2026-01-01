COMMENT ON COLUMN users.role IS 'PATIENT | DOCTOR | ADMIN';

COMMENT ON COLUMN appointments.status IS 'SCHEDULED | COMPLETED | CANCELLED';

COMMENT ON COLUMN notifications.type IS 'PRESCRIPTION | APPOINTMENT | SYSTEM';

-- User deletion cascades to patient/doctor (account deletion removes profile)
ALTER TABLE patients ADD FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE;

ALTER TABLE doctors ADD FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE;

-- Doctor deletion cascades to availability (no orphaned slots)
ALTER TABLE doctor_availability ADD FOREIGN KEY (doctor_id) REFERENCES doctors (id) ON DELETE CASCADE;

-- Patient/Doctor deletion keeps appointment history but nullifies reference
ALTER TABLE appointments ADD FOREIGN KEY (patient_id) REFERENCES patients (id) ON DELETE SET NULL;

ALTER TABLE appointments ADD FOREIGN KEY (doctor_id) REFERENCES doctors (id) ON DELETE SET NULL;

-- Availability deletion doesn't delete appointment (keep history)
ALTER TABLE appointments ADD FOREIGN KEY (availability_id) REFERENCES doctor_availability (id) ON DELETE SET NULL;

-- Prescriptions: keep history but remove doctor/patient link if deleted
ALTER TABLE prescriptions ADD FOREIGN KEY (doctor_id) REFERENCES doctors (id) ON DELETE SET NULL;

ALTER TABLE prescriptions ADD FOREIGN KEY (patient_id) REFERENCES patients (id) ON DELETE SET NULL;

-- Appointment deleted cascades to prescriptions (no orphaned prescriptions)
ALTER TABLE prescriptions ADD FOREIGN KEY (appointment_id) REFERENCES appointments (id) ON DELETE CASCADE;

-- Prescription deleted cascades to items
ALTER TABLE prescription_items ADD FOREIGN KEY (prescription_id) REFERENCES prescriptions (id) ON DELETE CASCADE;

-- User deletion cascades to notifications and sessions
ALTER TABLE notifications ADD FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
-- Create schema for appointment management
CREATE SCHEMA IF NOT EXISTS appointments;

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create tables in appointments schema
CREATE TABLE IF NOT EXISTS appointments.doctors (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    specialization_id UUID NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS appointments.specializations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS appointments.appointments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id VARCHAR(255) NOT NULL,
    doctor_id UUID NOT NULL REFERENCES appointments.doctors(id),
    scheduled_date TIMESTAMP WITH TIME ZONE NOT NULL,
    service_type VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'confirmed',
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT valid_status CHECK (status IN ('confirmed', 'cancelled', 'completed'))
);

-- Add foreign key constraint
ALTER TABLE appointments.doctors 
    ADD CONSTRAINT fk_doctor_specialization 
    FOREIGN KEY (specialization_id) 
    REFERENCES appointments.specializations(id);

-- Create indexes for better query performance
CREATE INDEX idx_appointments_user_id ON appointments.appointments(user_id);
CREATE INDEX idx_appointments_doctor_id ON appointments.appointments(doctor_id);
CREATE INDEX idx_appointments_status ON appointments.appointments(status);
CREATE INDEX idx_appointments_scheduled_date ON appointments.appointments(scheduled_date);

-- Add trigger for updating timestamps
CREATE OR REPLACE FUNCTION update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_appointments_timestamp
    BEFORE UPDATE ON appointments.appointments
    FOR EACH ROW
    EXECUTE FUNCTION update_timestamp();

CREATE TRIGGER update_doctors_timestamp
    BEFORE UPDATE ON appointments.doctors
    FOR EACH ROW
    EXECUTE FUNCTION update_timestamp();

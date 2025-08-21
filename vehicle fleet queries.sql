-- SQL Schema for the Vehicle Fleet Management Application

-- Drop the table if it already exists to start fresh.
-- This is useful for development and testing.
DROP TABLE IF EXISTS vehicles;

-- Create the 'vehicles' table to store fleet information.
CREATE TABLE vehicles (
    -- vehicle_id: A unique identifier for each vehicle (e.g., license plate or internal ID).
    -- It's the PRIMARY KEY, which means it must be unique and cannot be null.
    vehicle_id VARCHAR(255) PRIMARY KEY,

    -- make: The manufacturer of the vehicle (e.g., 'Ford', 'Toyota').
    -- NOT NULL constraint ensures this field must have a value.
    make VARCHAR(50) NOT NULL,

    -- model: The specific model of the vehicle (e.g., 'F-150', 'Camry').
    model VARCHAR(50),

    -- status: The current operational status of the vehicle.
    -- Examples: 'In Use', 'Maintenance', 'Parked'.
    status VARCHAR(50),

    -- current_mileage: The vehicle's current odometer reading in miles.
    current_mileage INTEGER,

    -- last_service_date: The date of the vehicle's most recent service.
    last_service_date DATE
);

-- Insert some sample data into the 'vehicles' table.
-- This provides initial data for the application to display.
INSERT INTO vehicles (vehicle_id, make, model, status, current_mileage, last_service_date) VALUES
('TRUCK-001', 'Ford', 'F-150', 'In Use', 85000, '2023-11-15'),
('SEDAN-101', 'Toyota', 'Camry', 'In Use', 52000, '2024-01-20'),
('VAN-202', 'Mercedes-Benz', 'Sprinter', 'Maintenance', 120000, '2023-09-01'),
('TRUCK-002', 'Chevrolet', 'Silverado', 'Parked', 95000, '2023-10-05'),
('SEDAN-102', 'Honda', 'Accord', 'In Use', 45000, '2024-02-10'),
('SUV-301', 'Ford', 'Explorer', 'Parked', 61000, '2023-12-22'),
('VAN-203', 'Ford', 'Transit', 'Maintenance', 150000, '2023-08-18');

-- A message to confirm the script has run.
-- In a psql client, this will be displayed after execution.
\echo 'Vehicles table created and populated with sample data.'


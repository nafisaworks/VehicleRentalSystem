from flask import Flask, jsonify, request
from flask_cors import CORS
import mysql.connector
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)
CORS(app)


def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT")),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME")
    )


# ---------------- HOME ----------------

@app.route("/")
def home():
    return jsonify({
        "message": "Vehicle Rental Management System Backend is running"
    })


# ---------------- GET VEHICLES ----------------

@app.route("/vehicles", methods=["GET"])
def get_vehicles():

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute("""
            SELECT
                v.vehicle_id,
                v.vehicle_name,
                v.registration_no,
                v.type_id,
                v.model_year,
                v.price_per_day,
                v.availability_status,
                v.owner_id,
                o.owner_name,
                v.location,
                v.condition_description
            FROM VEHICLE v
            JOIN OWNER o
                ON v.owner_id = o.owner_id
        """)

        vehicles = cursor.fetchall()

        cursor.close()
        connection.close()

        for vehicle in vehicles:
            vehicle["price_per_day"] = float(vehicle["price_per_day"])

        return jsonify(vehicles)

    except mysql.connector.Error as error:
        return jsonify({
            "error": str(error)
        }), 500


# ---------------- GET OWNERS ----------------

@app.route("/owners", methods=["GET"])
def get_owners():

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute("""
            SELECT owner_id, owner_name
            FROM OWNER
        """)

        owners = cursor.fetchall()

        cursor.close()
        connection.close()

        return jsonify(owners)

    except mysql.connector.Error as error:
        return jsonify({
            "error": str(error)
        }), 500


# ---------------- ADD VEHICLE ----------------

@app.route("/vehicles", methods=["POST"])
def add_vehicle():

    try:

        data = request.get_json()

        vehicle_name = data["vehicle_name"]
        registration_no = data["registration_no"]
        type_id = data["type_id"]
        model_year = data["model_year"]
        price_per_day = data["price_per_day"]
        owner_id = data["owner_id"]
        location = data["location"]
        condition_description = data["condition_description"]

        connection = get_db_connection()
        cursor = connection.cursor()

        query = """
            INSERT INTO VEHICLE
            (
                vehicle_name,
                registration_no,
                type_id,
                model_year,
                price_per_day,
                availability_status,
                owner_id,
                location,
                condition_description
            )
            VALUES (%s, %s, %s, %s, %s, 'Available', %s, %s, %s)
        """

        values = (
            vehicle_name,
            registration_no,
            type_id,
            model_year,
            price_per_day,
            owner_id,
            location,
            condition_description
        )

        cursor.execute(query, values)

        connection.commit()

        new_vehicle_id = cursor.lastrowid

        cursor.close()
        connection.close()

        return jsonify({
            "message": "Vehicle listed successfully",
            "vehicle_id": new_vehicle_id
        }), 201

    except mysql.connector.Error as error:

        return jsonify({
            "error": str(error)
        }), 500

# ---------------- CREATE BOOKING ----------------

@app.route("/bookings", methods=["POST"])
def create_booking():

    try:

        data = request.get_json()

        customer_id = data["customer_id"]
        vehicle_id = data["vehicle_id"]
        start_date = data["start_date"]
        end_date = data["end_date"]

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        # Get vehicle price
        cursor.execute("""
            SELECT price_per_day, availability_status
            FROM VEHICLE
            WHERE vehicle_id = %s
        """, (vehicle_id,))

        vehicle = cursor.fetchone()

        if vehicle is None:
            cursor.close()
            connection.close()

            return jsonify({
                "error": "Vehicle not found"
            }), 404

        if vehicle["availability_status"] != "Available":
            cursor.close()
            connection.close()

            return jsonify({
                "error": "Vehicle is not available"
            }), 400

        # Calculate number of rental days
        cursor.execute("""
            SELECT DATEDIFF(%s, %s) AS days
        """, (end_date, start_date))

        result = cursor.fetchone()

        days = result["days"]

        if days <= 0:
            cursor.close()
            connection.close()

            return jsonify({
                "error": "End date must be after start date"
            }), 400

        total_amount = days * float(vehicle["price_per_day"])

        # Create booking
        cursor.execute("""
            INSERT INTO BOOKING
            (
                customer_id,
                vehicle_id,
                start_date,
                end_date,
                total_amount,
                booking_status
            )
            VALUES (%s, %s, %s, %s, %s, 'Pending')
        """, (
            customer_id,
            vehicle_id,
            start_date,
            end_date,
            total_amount
        ))

        connection.commit()

        booking_id = cursor.lastrowid

        cursor.close()
        connection.close()

        return jsonify({
            "message": "Booking created successfully",
            "booking_id": booking_id,
            "total_amount": total_amount
        }), 201

    except mysql.connector.Error as error:

        return jsonify({
            "error": str(error)
        }), 500
# ---------------- GET AVAILABLE DRIVERS ----------------

@app.route("/drivers", methods=["GET"])
def get_drivers():
    try:
        location = request.args.get("location")

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        if location:
            cursor.execute("""
                SELECT
                    driver_id,
                    driver_name,
                    location,
                    experience_years,
                    availability_status
                FROM DRIVER
                WHERE availability_status = 'Available'
                AND LOWER(location) = LOWER(%s)
            """, (location,))
        else:
            cursor.execute("""
                SELECT
                    driver_id,
                    driver_name,
                    location,
                    experience_years,
                    availability_status
                FROM DRIVER
                WHERE availability_status = 'Available'
            """)

        drivers = cursor.fetchall()

        cursor.close()
        connection.close()

        return jsonify(drivers)

    except mysql.connector.Error as error:
        return jsonify({
            "error": str(error)
        }), 500
    # ---------------- GET OWNER VEHICLES ----------------

@app.route("/owner-vehicles/<int:owner_id>", methods=["GET"])
def get_owner_vehicles(owner_id):

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute("""
            SELECT
                vehicle_id,
                vehicle_name,
                registration_no,
                model_year,
                price_per_day,
                availability_status,
                location,
                condition_description
            FROM VEHICLE
            WHERE owner_id = %s
        """, (owner_id,))

        vehicles = cursor.fetchall()

        cursor.close()
        connection.close()

        for vehicle in vehicles:
            vehicle["price_per_day"] = float(
                vehicle["price_per_day"]
            )

        return jsonify(vehicles)

    except mysql.connector.Error as error:

        return jsonify({
            "error": str(error)
        }), 500

@app.route("/customer-bookings/<int:customer_id>", methods=["GET"])
def get_customer_bookings(customer_id):
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute("""
            SELECT
                b.booking_id,
                b.start_date,
                b.end_date,
                b.total_amount,
                b.booking_status,
                v.vehicle_name,
                v.registration_no,
                v.location,
                v.price_per_day
            FROM BOOKING b
            JOIN VEHICLE v
                ON b.vehicle_id = v.vehicle_id
            WHERE b.customer_id = %s
            ORDER BY b.booking_id DESC
        """, (customer_id,))

        bookings = cursor.fetchall()

        cursor.close()
        connection.close()

        for booking in bookings:
            booking["total_amount"] = float(booking["total_amount"])
            booking["price_per_day"] = float(booking["price_per_day"])

        return jsonify(bookings)

    except mysql.connector.Error as error:
        return jsonify({"error": str(error)}), 500


@app.route("/driver-requests", methods=["POST"])
def create_driver_request():
    try:
        data = request.get_json()

        booking_id = data["booking_id"]
        customer_id = data["customer_id"]
        driver_id = data["driver_id"]

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        # Check that the booking belongs to the customer
        cursor.execute("""
            SELECT booking_id
            FROM BOOKING
            WHERE booking_id = %s
            AND customer_id = %s
        """, (booking_id, customer_id))

        booking = cursor.fetchone()

        if booking is None:
            cursor.close()
            connection.close()

            return jsonify({
                "error": "Booking not found for this customer"
            }), 404

        # Check that the driver is available
        cursor.execute("""
            SELECT driver_id, driver_name, availability_status
            FROM DRIVER
            WHERE driver_id = %s
        """, (driver_id,))

        driver = cursor.fetchone()

        if driver is None:
            cursor.close()
            connection.close()

            return jsonify({
                "error": "Driver not found"
            }), 404

        if driver["availability_status"] != "Available":
            cursor.close()
            connection.close()

            return jsonify({
                "error": "Driver is not available"
            }), 400

        # Create driver request
        cursor.execute("""
            INSERT INTO DRIVER_REQUEST
            (
                booking_id,
                customer_id,
                driver_id,
                request_date,
                request_status
            )
            VALUES (%s, %s, %s, CURDATE(), 'Pending')
        """, (
            booking_id,
            customer_id,
            driver_id
        ))

        connection.commit()

        request_id = cursor.lastrowid

        cursor.close()
        connection.close()

        return jsonify({
            "message": "Driver request created successfully",
            "request_id": request_id
        }), 201

    except mysql.connector.Error as error:
        return jsonify({"error": str(error)}), 500
    # ---------------- RUN SERVER ----------------

if __name__ == "__main__":
    app.run(debug=True, port=5000)
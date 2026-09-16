from flask import Flask, jsonify
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

@app.route("/")
def home():
    return jsonify({
        "message": "Vehicle Rental Management System Backend is running"
    })

@app.route("/vehicles", methods=["GET"])
def get_vehicles():
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute("""
            SELECT
                vehicle_id,
                vehicle_name,
                registration_no,
                type_id,
                model_year,
                price_per_day,
                availability_status
            FROM VEHICLE
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

if __name__ == "__main__":
    app.run(debug=True, port=5000)
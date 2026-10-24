
from flask import Flask, jsonify, request, session
from functools import wraps
import hmac
from flask_cors import CORS
from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    logout_user,
    login_required,
    current_user,
)
from flask_bcrypt import Bcrypt
import mysql.connector
from dotenv import load_dotenv
import os


load_dotenv()

app = Flask(__name__)
CORS(
    app,
    origins=["http://127.0.0.1:5500"],
    supports_credentials=True
)

app.config["SECRET_KEY"] = os.getenv("FLASK_SECRET_KEY")
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = False  # Local HTTP demo only

if not app.config["SECRET_KEY"]:
    raise RuntimeError("FLASK_SECRET_KEY is missing from backend/.env")

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "admin_login"
@login_manager.unauthorized_handler
def unauthorized():
    return jsonify({
        "error": "Admin login required"
    }), 401

bcrypt = Bcrypt(app)

class AdminUser(UserMixin):
    def __init__(self, employee_id, email, role):
        self.id = f"admin:{employee_id}"
        self.employee_id = int(employee_id)
        self.email = email
        self.role = role


class CustomerUser(UserMixin):
    def __init__(self, customer_id, email, customer_name):
        self.id = f"customer:{customer_id}"
        self.customer_id = int(customer_id)
        self.email = email
        self.customer_name = customer_name
        self.role = "customer"

class OwnerUser(UserMixin):
    def __init__(self, owner_id, email, owner_name):
        self.id = f"owner:{owner_id}"
        self.owner_id = int(owner_id)
        self.email = email
        self.owner_name = owner_name
        self.role = "owner"



@login_manager.user_loader
def load_user(user_id):
    # Prefixes prevent an employee ID and customer ID from colliding.
    if not isinstance(user_id, str) or ":" not in user_id:
        return None

    account_type, raw_id = user_id.split(":", 1)
    if not raw_id.isdigit():
        return None

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        if account_type == "admin":
            cursor.execute(
                """
                SELECT employee_id, email, role
                FROM EMPLOYEE
                WHERE employee_id = %s
                """,
                (int(raw_id),)
            )
            employee = cursor.fetchone()

            if not employee or employee["role"].lower() not in (
                "manager", "admin", "administrator"
            ):
                return None

            return AdminUser(
                employee["employee_id"],
                employee["email"],
                employee["role"]
            )


        if account_type == "customer":
            cursor.execute(
                """
                SELECT customer_id, email, customer_name
                FROM CUSTOMER
                WHERE customer_id = %s
                """,
                (int(raw_id),)
            )
            customer = cursor.fetchone()
            if not customer:
                return None
            return CustomerUser(
                customer["customer_id"],
                customer["email"],
                customer["customer_name"]
            )

        if account_type == "owner":
            cursor.execute(
                """
                SELECT owner_id, email, owner_name
                FROM OWNER
                WHERE owner_id = %s
                """,
                (int(raw_id),)
            )
            owner = cursor.fetchone()
            if not owner:
                return None
            return OwnerUser(
                owner["owner_id"],
                owner["email"],
                owner["owner_name"]
            )

        return None

    finally:
        cursor.close()
        connection.close()


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not current_user.is_authenticated or not (
            getattr(current_user, "role", "").lower()
            in ("manager", "admin", "administrator")
        ):
            return jsonify({"error": "Admin login required"}), 401
        return view(*args, **kwargs)
    return wrapped

def owner_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not current_user.is_authenticated or getattr(
            current_user, "role", ""
        ) != "owner":
            return jsonify({
                "error": "Please log in with an owner account"
            }), 401
        return view(*args, **kwargs)
    return wrapped



def customer_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not current_user.is_authenticated or getattr(
            current_user, "role", ""
        ) != "customer":
            return jsonify({
                "error": "Please log in with a customer account"
            }), 401
        return view(*args, **kwargs)
    return wrapped




# ---------------- ADMIN LOGIN ----------------

@app.route("/admin/login", methods=["POST"])
def admin_login():
    data = request.get_json(silent=True) or {}

    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if not email or not password:
        return jsonify({
            "error": "Email and password are required"
        }), 400

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT employee_id, email, role, password_hash
            FROM EMPLOYEE
            WHERE email = %s
            """,
            (email,)
        )
        employee = cursor.fetchone()

        if (
            not employee
            or not employee["password_hash"]
            or employee["role"].lower() not in (
                "manager", "admin", "administrator"
            )
            or not bcrypt.check_password_hash(
                employee["password_hash"], password
            )
        ):
            return jsonify({
                "error": "Invalid email or password"
            }), 401

        login_user(
            AdminUser(
                employee["employee_id"],
                employee["email"],
                employee["role"]
            )
        )

        return jsonify({
            "message": "Admin login successful"
        })

    finally:
        cursor.close()
        connection.close()


# ---------------- ADMIN LOGOUT ----------------

@app.route("/admin/logout", methods=["POST"])
@admin_required
def admin_logout():
    logout_user()
    return jsonify({
        "message": "Admin logout successful"
    })

def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT")),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME")
    )


# ---------------- OWNER REGISTRATION ----------------

@app.route("/owner/register", methods=["POST"])
def owner_register():
    data = request.get_json(silent=True) or {}

    name = str(data.get("owner_name", "")).strip()
    email = str(data.get("email", "")).strip().lower()
    phone = str(data.get("phone", "")).strip()
    address = str(data.get("address", "")).strip() or None
    password = data.get("password", "")

    if not name or not email or not phone or not isinstance(password, str):
        return jsonify({
            "error": "Name, email, phone and password are required"
        }), 400

    if len(name) > 100 or len(email) > 100 or len(phone) > 15:
        return jsonify({"error": "A field exceeds the allowed length"}), 400

    if address and len(address) > 255:
        return jsonify({"error": "Address is too long"}), 400

    if "@" not in email or "." not in email.rsplit("@", 1)[-1]:
        return jsonify({"error": "Enter a valid email address"}), 400

    if len(password) < 8:
        return jsonify({
            "error": "Password must be at least 8 characters"
        }), 400

    if len(password.encode("utf-8")) > 72:
        return jsonify({
            "error": "Password must be 72 UTF-8 bytes or fewer"
        }), 400

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            "SELECT owner_id FROM OWNER WHERE email = %s",
            (email,)
        )
        if cursor.fetchone():
            return jsonify({
                "error": "An account with this email already exists"
            }), 409

        password_hash = bcrypt.generate_password_hash(
            password
        ).decode("utf-8")

        cursor.execute(
            """
            INSERT INTO OWNER
                (owner_name, email, phone, address, password)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (name, email, phone, address, password_hash)
        )

        connection.commit()
        owner_id = cursor.lastrowid

        login_user(OwnerUser(owner_id, email, name))

        return jsonify({
            "message": "Owner account created successfully",
            "owner": {
                "owner_id": owner_id,
                "owner_name": name,
                "email": email
            }
        }), 201

    except mysql.connector.IntegrityError:
        if connection:
            connection.rollback()
        return jsonify({
            "error": "An account with this email already exists"
        }), 409

    except mysql.connector.Error:
        if connection:
            connection.rollback()
        app.logger.exception("Owner registration database error")
        return jsonify({
            "error": "Unable to create owner account"
        }), 500

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


# ---------------- OWNER LOGIN ----------------

@app.route("/owner/login", methods=["POST"])
def owner_login():
    data = request.get_json(silent=True) or {}

    email = str(data.get("email", "")).strip().lower()
    password = data.get("password", "")

    if not email or not isinstance(password, str) or not password:
        return jsonify({
            "error": "Email and password are required"
        }), 400

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT owner_id, owner_name, email, password
            FROM OWNER
            WHERE email = %s
            """,
            (email,)
        )
        owner = cursor.fetchone()

        if not owner or not owner["password"]:
            return jsonify({"error": "Invalid email or password"}), 401

        stored = owner["password"]

        try:
            valid = bcrypt.check_password_hash(stored, password)
        except (ValueError, TypeError):
            valid = False

        # Support older owner records with plain-text passwords.
        # Upgrade the password to bcrypt after a successful login.
        if not valid:
            try:
                valid = hmac.compare_digest(str(stored), password)
            except (TypeError, ValueError):
                valid = False

        if not valid:
            return jsonify({"error": "Invalid email or password"}), 401

        try:
            already_hashed = bcrypt.check_password_hash(stored, password)
        except (ValueError, TypeError):
            already_hashed = False

        if not already_hashed:
            password_hash = bcrypt.generate_password_hash(
                password
            ).decode("utf-8")

            cursor.execute(
                "UPDATE OWNER SET password = %s WHERE owner_id = %s",
                (password_hash, owner["owner_id"])
            )
            connection.commit()

        login_user(OwnerUser(
            owner["owner_id"],
            owner["email"],
            owner["owner_name"]
        ))

        return jsonify({
            "message": "Owner login successful",
            "owner": {
                "owner_id": owner["owner_id"],
                "owner_name": owner["owner_name"],
                "email": owner["email"]
            }
        })

    except mysql.connector.Error:
        if connection:
            connection.rollback()
        app.logger.exception("Owner login database error")
        return jsonify({"error": "Unable to log in right now"}), 500

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


# ---------------- OWNER SESSION ----------------

@app.route("/owner/me", methods=["GET"])
@owner_required
def owner_me():
    return jsonify({
        "owner_id": current_user.owner_id,
        "owner_name": current_user.owner_name,
        "email": current_user.email
    })


# ---------------- OWNER LOGOUT ----------------

@app.route("/owner/logout", methods=["POST"])
@owner_required
def owner_logout():
    logout_user()
    return jsonify({"message": "Owner logout successful"})


# ---------------- CUSTOMER AUTHENTICATION ----------------

@app.route("/customer/register", methods=["POST"])
def customer_register():
    data = request.get_json(silent=True) or {}
    name = str(data.get("customer_name", "")).strip()
    email = str(data.get("email", "")).strip().lower()
    phone = str(data.get("phone", "")).strip()
    address = str(data.get("address", "")).strip() or None
    password = data.get("password", "")

    if not name or not email or not phone or not isinstance(password, str):
        return jsonify({"error": "Name, email, phone and password are required"}), 400
    if len(name) > 100 or len(email) > 100 or len(phone) > 15:
        return jsonify({"error": "One or more fields exceed the allowed length"}), 400
    if "@" not in email or "." not in email.rsplit("@", 1)[-1]:
        return jsonify({"error": "Enter a valid email address"}), 400
    if len(password) < 8:
        return jsonify({"error": "Password must be at least 8 characters"}), 400
    if len(password.encode("utf-8")) > 72:
        return jsonify({"error": "Password must be 72 UTF-8 bytes or fewer"}), 400

    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT customer_id FROM CUSTOMER WHERE email = %s", (email,))
        if cursor.fetchone():
            return jsonify({"error": "An account with this email already exists"}), 409

        password_hash = bcrypt.generate_password_hash(password).decode("utf-8")
        cursor.execute(
            """
            INSERT INTO CUSTOMER (customer_name, email, phone, address, password)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (name, email, phone, address, password_hash)
        )
        connection.commit()
        customer_id = cursor.lastrowid
        login_user(CustomerUser(customer_id, email, name))
        return jsonify({
            "message": "Customer account created successfully",
            "customer": {"customer_id": customer_id, "customer_name": name, "email": email}
        }), 201
    except mysql.connector.IntegrityError:
        if connection:
            connection.rollback()
        return jsonify({"error": "An account with this email already exists"}), 409
    except mysql.connector.Error:
        if connection:
            connection.rollback()
        app.logger.exception("Customer registration database error")
        return jsonify({"error": "Unable to create customer account"}), 500
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


@app.route("/customer/login", methods=["POST"])
def customer_login():
    data = request.get_json(silent=True) or {}
    email = str(data.get("email", "")).strip().lower()
    password = data.get("password", "")
    if not email or not isinstance(password, str) or not password:
        return jsonify({"error": "Email and password are required"}), 400

    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT customer_id, customer_name, email, password
            FROM CUSTOMER WHERE email = %s
            """,
            (email,)
        )
        customer = cursor.fetchone()
        stored = customer["password"] if customer else None
        valid = False
        if stored:
            try:
                valid = bcrypt.check_password_hash(stored, password)
            except (ValueError, TypeError):
                # Legacy account support: if the old value is plain text,
                # upgrade it to bcrypt only after a successful login.
                valid = False
            if not valid:
                # Legacy records in the original project may be plain text.
                # Never return or log the stored value.
                try:
                    valid = hmac.compare_digest(str(stored), password)
                except (TypeError, ValueError):
                    valid = False

        if not customer or not valid:
            return jsonify({"error": "Invalid email or password"}), 401

        # Migrate any legacy plain-text password after the user proves it.
        try:
            already_hashed = bcrypt.check_password_hash(stored, password)
        except (ValueError, TypeError):
            already_hashed = False
        if not already_hashed:
            upgraded = bcrypt.generate_password_hash(password).decode("utf-8")
            cursor.execute(
                "UPDATE CUSTOMER SET password = %s WHERE customer_id = %s",
                (upgraded, customer["customer_id"])
            )
            connection.commit()

        login_user(CustomerUser(
            customer["customer_id"], customer["email"], customer["customer_name"]
        ))
        return jsonify({
            "message": "Customer login successful",
            "customer": {
                "customer_id": customer["customer_id"],
                "customer_name": customer["customer_name"],
                "email": customer["email"]
            }
        })
    except mysql.connector.Error:
        if connection:
            connection.rollback()
        app.logger.exception("Customer login database error")
        return jsonify({"error": "Unable to log in right now"}), 500
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


@app.route("/customer/me", methods=["GET"])
@customer_required
def customer_me():
    return jsonify({
        "customer_id": current_user.customer_id,
        "customer_name": current_user.customer_name,
        "email": current_user.email
    })


@app.route("/customer/logout", methods=["POST"])
@customer_required
def customer_logout():
    logout_user()
    return jsonify({"message": "Customer logout successful"})


# ---------------- CUSTOMER DRIVING LICENCE ----------------

from datetime import date

@app.route("/customer/license", methods=["GET"])
@customer_required
def get_customer_license():
    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute("""
            SELECT license_number, issuing_authority,
                   issue_date, expiry_date, license_class
            FROM CUSTOMER_LICENSE
            WHERE customer_id = %s
        """, (current_user.customer_id,))

        licence = cursor.fetchone()

        if not licence:
            return jsonify({"license": None})

        for field in ("issue_date", "expiry_date"):
            if licence[field]:
                licence[field] = licence[field].isoformat()

        return jsonify({"license": licence})

    except mysql.connector.Error:
        app.logger.exception("Customer licence retrieval failed")
        return jsonify({"error": "Unable to retrieve licence details"}), 500

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


@app.route("/customer/license", methods=["POST"])
@customer_required
def save_customer_license():
    data = request.get_json(silent=True) or {}

    license_number = str(data.get("license_number", "")).strip()
    authority = str(data.get("issuing_authority", "")).strip()
    issue_date = str(data.get("issue_date", "")).strip()
    expiry_date = str(data.get("expiry_date", "")).strip()
    license_class = str(data.get("license_class", "")).strip()

    if not all([
        license_number, authority, issue_date,
        expiry_date, license_class
    ]):
        return jsonify({"error": "Please complete all licence fields"}), 400

    if (
        len(license_number) > 50
        or len(authority) > 100
        or len(license_class) > 50
    ):
        return jsonify({"error": "One or more fields are too long"}), 400

    try:
        issued = date.fromisoformat(issue_date)
        expires = date.fromisoformat(expiry_date)
    except ValueError:
        return jsonify({"error": "Enter valid licence dates"}), 400

    if issued > date.today():
        return jsonify({"error": "Issue date cannot be in the future"}), 400

    if expires <= issued:
        return jsonify({
            "error": "Expiry date must be later than issue date"
        }), 400

    if expires <= date.today():
        return jsonify({
            "error": "This licence has expired. Enter a valid licence."
        }), 400

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute("""
            INSERT INTO CUSTOMER_LICENSE (
                customer_id, license_number, issuing_authority,
                issue_date, expiry_date, license_class
            )
            VALUES (%s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                license_number = VALUES(license_number),
                issuing_authority = VALUES(issuing_authority),
                issue_date = VALUES(issue_date),
                expiry_date = VALUES(expiry_date),
                license_class = VALUES(license_class)
        """, (
            current_user.customer_id,
            license_number, authority,
            issued, expires, license_class
        ))

        connection.commit()

        return jsonify({
            "message": "Driving licence details saved successfully",
            "note": "Licence details have not been independently verified."
        })

    except mysql.connector.IntegrityError:
        if connection:
            connection.rollback()
        return jsonify({
            "error": "This licence number is already registered under that authority"
        }), 409

    except mysql.connector.Error:
        if connection:
            connection.rollback()
        app.logger.exception("Customer licence save failed")
        return jsonify({"error": "Unable to save licence details"}), 500

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

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
                WHERE v.verification_status = 'Approved'
                AND v.commercial_eligibility_status = 'Verified'
                AND v.availability_status = 'Available'

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


# ---------------- ADMIN: PENDING VEHICLES ----------------

@app.route("/admin/pending-vehicles", methods=["GET"])
@admin_required
def get_pending_vehicles():
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute("""
            SELECT
                v.vehicle_id,
                v.vehicle_name,
                v.registration_no,
                v.model_year,
                v.price_per_day,
                v.availability_status,
                v.verification_status,
                v.owner_id,
                o.owner_name,
                o.email AS owner_email,
                o.phone AS owner_phone,
                v.location,
                v.condition_description
            FROM VEHICLE v
            JOIN OWNER o
                ON v.owner_id = o.owner_id
            WHERE v.verification_status = 'Pending'
            ORDER BY v.vehicle_id
        """)

        vehicles = cursor.fetchall()

        cursor.close()
        connection.close()

        for vehicle in vehicles:
            vehicle["price_per_day"] = float(
                vehicle["price_per_day"]
            )

        return jsonify(vehicles)

    except mysql.connector.Error:
        return jsonify({
            "error": "Unable to retrieve pending vehicles"
        }), 500

# ---------------- ADMIN: REVIEW VEHICLE ----------------

@app.route("/admin/review-vehicle", methods=["POST"])
@admin_required
def review_vehicle():
    data = request.get_json(silent=True) or {}

    vehicle_id = data.get("vehicle_id")
    decision = data.get("decision")
    reason = (data.get("reason") or "").strip()

    allowed_decisions = {
        "Approved", "Rejected", "Needs Correction"
    }

    if (
        not isinstance(vehicle_id, int)
        or isinstance(vehicle_id, bool)
        or vehicle_id <= 0
    ):
        return jsonify({"error": "Invalid vehicle ID"}), 400

    if decision not in allowed_decisions:
        return jsonify({"error": "Invalid review decision"}), 400

    if len(reason) > 500:
        return jsonify({"error": "Reason must be 500 characters or fewer"}), 400

    if decision in ("Rejected", "Needs Correction") and not reason:
        return jsonify({"error": "Please provide a reason"}), 400

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        connection.start_transaction()
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT vehicle_id, verification_status
            FROM VEHICLE
            WHERE vehicle_id = %s
            FOR UPDATE
            """,
            (vehicle_id,)
        )
        vehicle = cursor.fetchone()

        if not vehicle:
            connection.rollback()
            return jsonify({"error": "Vehicle not found"}), 404

        if vehicle["verification_status"] != "Pending":
            connection.rollback()
            return jsonify({
                "error": "This vehicle has already been reviewed"
            }), 409

        cursor.execute(
            """
            UPDATE VEHICLE
            SET verification_status = %s
            WHERE vehicle_id = %s
            """,
            (decision, vehicle_id)
        )

        cursor.execute(
            """
            INSERT INTO VEHICLE_VERIFICATION_LOG
                (vehicle_id, employee_id, decision, reason)
            VALUES (%s, %s, %s, %s)
            """,
            (
                vehicle_id,
                current_user.employee_id,
                decision,
                reason or None
            )
        )

        connection.commit()

        return jsonify({
            "message": "Vehicle review saved successfully",
            "vehicle_id": vehicle_id,
            "decision": decision
        }), 200

    except mysql.connector.Error:
        if connection:
            connection.rollback()
        app.logger.exception("Vehicle review database error")
        return jsonify({
            "error": "Unable to save vehicle review"
        }), 500

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

# ---------------- ADMIN: COMMERCIAL ELIGIBILITY REVIEW ----------------

@app.route("/admin/review-commercial-eligibility", methods=["POST"])
@admin_required
def review_commercial_eligibility():
    data = request.get_json(silent=True) or {}

    vehicle_id = data.get("vehicle_id")
    decision = data.get("decision")
    reason = (data.get("reason") or "").strip()

    allowed_decisions = {
        "Verified", "Rejected", "Needs Correction"
    }

    if (
        not isinstance(vehicle_id, int)
        or isinstance(vehicle_id, bool)
        or vehicle_id <= 0
    ):
        return jsonify({"error": "Invalid vehicle ID"}), 400

    if decision not in allowed_decisions:
        return jsonify({"error": "Invalid commercial review decision"}), 400

    if len(reason) > 500:
        return jsonify({"error": "Reason must be 500 characters or fewer"}), 400

    if decision in ("Rejected", "Needs Correction") and not reason:
        return jsonify({"error": "Please provide a reason"}), 400

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        connection.start_transaction()
        cursor = connection.cursor(dictionary=True)

        cursor.execute("""
            SELECT vehicle_id, commercial_eligibility_status
            FROM VEHICLE
            WHERE vehicle_id = %s
            FOR UPDATE
        """, (vehicle_id,))
        vehicle = cursor.fetchone()

        if not vehicle:
            connection.rollback()
            return jsonify({"error": "Vehicle not found"}), 404

        if vehicle["commercial_eligibility_status"] != "Pending":
            connection.rollback()
            return jsonify({
                "error": "This commercial eligibility review is no longer pending"
            }), 409

        # Do not verify a vehicle without supporting document records.
        cursor.execute("""
            SELECT COUNT(*) AS total,
                   SUM(review_status = 'Approved') AS approved
            FROM VEHICLE_DOCUMENT
            WHERE vehicle_id = %s
        """, (vehicle_id,))
        document_summary = cursor.fetchone()

        if decision == "Verified" and (
            not document_summary["total"]
            or document_summary["approved"] != document_summary["total"]
        ):
            connection.rollback()
            return jsonify({
                "error": "All required supporting documents must be recorded as approved before verifying eligibility"
            }), 400

        cursor.execute("""
            UPDATE VEHICLE
            SET commercial_eligibility_status = %s
            WHERE vehicle_id = %s
        """, (decision, vehicle_id))

        # Keep an audit trail in the existing vehicle verification log.
        cursor.execute("""
            INSERT INTO VEHICLE_VERIFICATION_LOG
                (vehicle_id, employee_id, decision, reason)
            VALUES (%s, %s, %s, %s)
        """, (
            vehicle_id,
            current_user.employee_id,
            "Commercial " + decision,
            reason or None
        ))

        connection.commit()

        return jsonify({
            "message": "Commercial eligibility review saved",
            "vehicle_id": vehicle_id,
            "commercial_eligibility_status": decision
        }), 200

    except mysql.connector.Error:
        if connection:
            connection.rollback()
        app.logger.exception("Commercial eligibility review database error")
        return jsonify({
            "error": "Unable to save commercial eligibility review"
        }), 500

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

# ---------------- ADMIN: REVIEW VEHICLE DOCUMENT ----------------

@app.route("/admin/review-vehicle-document", methods=["POST"])
@admin_required
def review_vehicle_document():
    data = request.get_json(silent=True) or {}

    document_id = data.get("document_id")
    decision = data.get("decision")
    notes = (data.get("notes") or "").strip()

    if (
        not isinstance(document_id, int)
        or isinstance(document_id, bool)
        or document_id <= 0
    ):
        return jsonify({"error": "Invalid document ID"}), 400

    if decision not in ("Approved", "Rejected", "Needs Correction"):
        return jsonify({"error": "Invalid document review decision"}), 400

    if len(notes) > 500:
        return jsonify({"error": "Notes must be 500 characters or fewer"}), 400

    if decision != "Approved" and not notes:
        return jsonify({"error": "Please provide notes for this decision"}), 400

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        connection.start_transaction()
        cursor = connection.cursor(dictionary=True)

        cursor.execute("""
            SELECT document_id, vehicle_id, review_status
            FROM VEHICLE_DOCUMENT
            WHERE document_id = %s
            FOR UPDATE
        """, (document_id,))
        document = cursor.fetchone()

        if not document:
            connection.rollback()
            return jsonify({"error": "Document not found"}), 404

        if document["review_status"] != "Pending":
            connection.rollback()
            return jsonify({
                "error": "This document has already been reviewed"
            }), 409

        cursor.execute("""
            UPDATE VEHICLE_DOCUMENT
            SET review_status = %s,
                review_notes = %s,
                reviewed_at = CURRENT_TIMESTAMP
            WHERE document_id = %s
        """, (decision, notes or None, document_id))

        cursor.execute("""
            INSERT INTO VEHICLE_VERIFICATION_LOG
                (vehicle_id, employee_id, decision, reason)
            VALUES (%s, %s, %s, %s)
        """, (
            document["vehicle_id"],
            current_user.employee_id,
            decision,
            "Document ID " + str(document_id) + ": " + (notes or "Document approved")
        ))

        connection.commit()

        return jsonify({
            "message": "Document review saved",
            "document_id": document_id,
            "review_status": decision
        }), 200

    except mysql.connector.Error:
        if connection:
            connection.rollback()
        app.logger.exception("Document review database error")
        return jsonify({
            "error": "Unable to save document review"
        }), 500

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

# ---------------- ADMIN: PENDING COMMERCIAL REVIEWS ----------------

@app.route("/admin/pending-commercial-vehicles", methods=["GET"])
@admin_required
def get_pending_commercial_vehicles():
    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute("""
            SELECT
                v.vehicle_id,
                v.vehicle_name,
                v.registration_no,
                v.model_year,
                v.price_per_day,
                v.location,
                v.verification_status,
                v.commercial_use_declared,
                v.commercial_eligibility_status,
                v.permit_number,
                v.permit_expiry_date,
                v.insurance_expiry_date,
                o.owner_name,
                o.email AS owner_email
            FROM VEHICLE v
            JOIN OWNER o ON o.owner_id = v.owner_id
            WHERE v.commercial_eligibility_status = 'Pending'
            ORDER BY v.vehicle_id
        """)

        vehicles = cursor.fetchall()

        for vehicle in vehicles:
            vehicle["price_per_day"] = float(vehicle["price_per_day"])
            for field in ("permit_expiry_date", "insurance_expiry_date"):
                if vehicle[field]:
                    vehicle[field] = vehicle[field].isoformat()
            vehicle["commercial_use_declared"] = bool(
                vehicle["commercial_use_declared"]
            )

        return jsonify(vehicles), 200

    except mysql.connector.Error:
        app.logger.exception("Unable to load commercial reviews")
        return jsonify({"error": "Unable to load commercial reviews"}), 500

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


# ---------------- ADMIN: LIST VEHICLE DOCUMENTS ----------------

@app.route("/admin/vehicle-documents/<int:vehicle_id>", methods=["GET"])
@admin_required
def get_vehicle_documents(vehicle_id):
    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute("""
            SELECT
                document_id,
                vehicle_id,
                document_type,
                document_reference,
                expiry_date,
                review_status,
                review_notes,
                uploaded_at,
                reviewed_at
            FROM VEHICLE_DOCUMENT
            WHERE vehicle_id = %s
            ORDER BY document_id
        """, (vehicle_id,))

        documents = cursor.fetchall()

        for document in documents:
            for field in ("expiry_date", "uploaded_at", "reviewed_at"):
                if document[field]:
                    document[field] = document[field].isoformat()

        return jsonify(documents), 200

    except mysql.connector.Error:
        app.logger.exception("Unable to load vehicle documents")
        return jsonify({"error": "Unable to load vehicle documents"}), 500

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

# ---------------- ADD VEHICLE ----------------



@app.route("/vehicles", methods=["POST"])
@owner_required
def add_vehicle():
    data = request.get_json(silent=True) or {}
    data["owner_id"] = current_user.owner_id

    required_fields = [
    "vehicle_name", "registration_no", "type_id",
    "model_year", "price_per_day",
    "location", "condition_description"
]

    missing = [
        field for field in required_fields
        if data.get(field) is None or data.get(field) == ""
    ]
    if missing:
        return jsonify({
            "error": "Missing required fields: " + ", ".join(missing)
        }), 400
    commercial_declared = data.get("commercial_use_declared", False)

    if not isinstance(commercial_declared, bool):
        return jsonify({
            "error": "Commercial-use declaration must be true or false."
        }), 400
    documents = data.get("documents", [])
    if not isinstance(documents, list):
        return jsonify({"error": "Documents must be a list"}), 400

    if len(documents) > 20:
        return jsonify({"error": "Too many document references"}), 400

    for document in documents:
        if not isinstance(document, dict):
            return jsonify({"error": "Invalid document entry"}), 400

        if not all(document.get(field) for field in (
            "document_type", "document_reference"
        )):
            return jsonify({
                "error": "Each document needs a type and reference"
            }), 400

        if len(str(document["document_type"])) > 50:
            return jsonify({"error": "Document type is too long"}), 400

        if len(str(document["document_reference"])) > 500:
            return jsonify({"error": "Document reference is too long"}), 400

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        connection.start_transaction()
        cursor = connection.cursor()

        cursor.execute("""
            INSERT INTO VEHICLE (
                vehicle_name,
                registration_no,
                type_id,
                model_year,
                price_per_day,
                availability_status,
                owner_id,
                location,
                condition_description,
                commercial_use_declared,
                commercial_eligibility_status,
                permit_number,
                permit_expiry_date,
                insurance_expiry_date
            )
            VALUES (
                %s, %s, %s, %s, %s, 'Available',
                %s, %s, %s, %s, 'Pending', %s, %s, %s
            )
        """, (
            data["vehicle_name"],
            data["registration_no"],
            data["type_id"],
            data["model_year"],
            data["price_per_day"],
            data["owner_id"],
            data["location"],
            data["condition_description"],
            int(commercial_declared),
            data.get("permit_number") or None,
            data.get("permit_expiry_date") or None,
            data.get("insurance_expiry_date") or None
        ))

        new_vehicle_id = cursor.lastrowid

        for document in documents:
            cursor.execute("""
                INSERT INTO VEHICLE_DOCUMENT (
                    vehicle_id,
                    document_type,
                    document_reference,
                    expiry_date
                )
                VALUES (%s, %s, %s, %s)
            """, (
                new_vehicle_id,
                document["document_type"],
                document["document_reference"],
                document.get("expiry_date") or None
            ))

        connection.commit()

        return jsonify({
            "message": "Vehicle submitted for review",
            "vehicle_id": new_vehicle_id,
            "verification_status": "Pending",
            "commercial_eligibility_status": "Pending"
        }), 201


    except mysql.connector.IntegrityError as error:
        if connection:
            connection.rollback()

        if error.errno == 1062:
            return jsonify({
                "error": "A vehicle with this registration number already exists."
            }), 409

        app.logger.exception("Vehicle listing integrity error")
        return jsonify({
            "error": "Vehicle data violates a database constraint."
        }), 400

    except mysql.connector.Error:
        if connection:
            connection.rollback()

        app.logger.exception("Vehicle listing database error")
        return jsonify({
            "error": "Unable to save vehicle listing"
        }), 500

    except (ValueError, TypeError):
        if connection:
            connection.rollback()

        return jsonify({
            "error": "Invalid vehicle data"
        }), 400


    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


# ---------------- CREATE BOOKING ----------------
@app.route("/bookings", methods=["POST"])
@customer_required
def create_booking():
    connection = None
    cursor = None

    try:
        data = request.get_json(silent=True) or {}

        required = ["vehicle_id", "start_date", "end_date"]
        if any(data.get(key) is None for key in required):
            return jsonify({"error": "Missing required booking details"}), 400

        # The booking owner comes from the authenticated session, never the request body.
        customer_id = current_user.customer_id
        vehicle_id = data["vehicle_id"]
        start_date = data["start_date"]
        end_date = data["end_date"]

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        # Validate that the customer exists
        cursor.execute("""
            SELECT customer_id
            FROM CUSTOMER
            WHERE customer_id = %s
        """, (customer_id,))

        customer = cursor.fetchone()

        if customer is None:
            connection.rollback()
            return jsonify({
                "error": "Customer not found"
            }), 404

        # Require saved, currently valid-by-date licence details.
        cursor.execute("""
            SELECT issue_date, expiry_date
            FROM CUSTOMER_LICENSE
            WHERE customer_id = %s
        """, (customer_id,))

        licence = cursor.fetchone()

        if licence is None:
            connection.rollback()
            return jsonify({
                "error": "Please add your driving licence details before booking."
            }), 400

        today = date.today()

        if licence["issue_date"] > today or licence["expiry_date"] <= today:
            connection.rollback()
            return jsonify({
                "error": "Your licence dates are invalid or expired. Please update your licence details."
            }), 400

        # Lock the vehicle row to prevent simultaneous overlapping bookings.
        cursor.execute("""
            SELECT
    price_per_day,
    availability_status,
    verification_status,
    commercial_eligibility_status
FROM VEHICLE
WHERE vehicle_id = %s
FOR UPDATE
        """, (vehicle_id,))
        vehicle = cursor.fetchone()

        if vehicle is None:
            connection.rollback()
            return jsonify({"error": "Vehicle not found"}), 404


        if vehicle["verification_status"] != "Approved":
            connection.rollback()
            return jsonify({
                "error": "Vehicle has not been approved for rental"
            }), 403

                # Demo listings are allowed for academic demonstration only.
        # Real listings must pass commercial verification.
        cursor.execute("""
            SELECT registration_no, condition_description
            FROM VEHICLE
            WHERE vehicle_id = %s
        """, (vehicle_id,))
        demo_vehicle = cursor.fetchone()

        is_demo_vehicle = (
            demo_vehicle
            and demo_vehicle["registration_no"].startswith(("ODDEMO", "BGDEMO"))
            and demo_vehicle["condition_description"].startswith("Demo listing")
        )

        if (
            vehicle["commercial_eligibility_status"] != "Verified"
            and not is_demo_vehicle
        ):
            connection.rollback()
            return jsonify({
                "error": "Vehicle has not been commercially verified"
            }), 403


        if vehicle["availability_status"] != "Available":
            connection.rollback()
            return jsonify({"error": "Vehicle is not available"}), 400

        # Validate the rental period.
        cursor.execute(
            "SELECT DATEDIFF(%s, %s) AS days",
            (end_date, start_date)
        )
        days = cursor.fetchone()["days"]

        if days is None or days <= 0:
            connection.rollback()
            return jsonify({
                "error": "End date must be after start date"
            }), 400

        # Check for overlapping pending or confirmed bookings.
        cursor.execute("""
            SELECT booking_id
            FROM BOOKING
            WHERE vehicle_id = %s
              AND booking_status IN ('Pending', 'Confirmed')
              AND start_date < %s
              AND end_date > %s
            LIMIT 1
        """, (vehicle_id, end_date, start_date))

        if cursor.fetchone():
            connection.rollback()
            return jsonify({
                "error": "Vehicle already has a booking for these dates"
            }), 409

        total_amount = days * float(vehicle["price_per_day"])

        cursor.execute("""
            INSERT INTO BOOKING (
                customer_id, vehicle_id, start_date, end_date,
                total_amount, booking_status
            )
            VALUES (%s, %s, %s, %s, %s, 'Confirmed')
        """, (
            customer_id, vehicle_id, start_date, end_date, total_amount
        ))

        booking_id = cursor.lastrowid
        connection.commit()

        return jsonify({
            "message": "Booking created successfully",
            "booking_id": booking_id,
            "total_amount": total_amount
        }), 201

    except mysql.connector.Error as error:
        if connection:
            connection.rollback()
        return jsonify({"error": str(error)}), 500

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


    # ---------------- GET OWNER VEHICLES ----------------

@app.route("/owner-vehicles", methods=["GET"])
@owner_required
def get_owner_vehicles():
    owner_id = current_user.owner_id

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
        verification_status,
        commercial_eligibility_status,
        commercial_use_declared,
        permit_number,
        permit_expiry_date,
        insurance_expiry_date,
        location,
        condition_description
    FROM VEHICLE
    WHERE owner_id = %s
""", (owner_id,))

        vehicles = cursor.fetchall()

        cursor.close()
        connection.close()

        for vehicle in vehicles:
            vehicle["price_per_day"] = float(vehicle["price_per_day"])

            for field in ("permit_expiry_date", "insurance_expiry_date"):
                if vehicle[field]:
                    vehicle[field] = vehicle[field].isoformat()

            vehicle["commercial_use_declared"] = bool(
                vehicle["commercial_use_declared"]
            )

        return jsonify(vehicles)

    except mysql.connector.Error as error:

        return jsonify({
            "error": str(error)
        }), 500

@app.route("/my-bookings", methods=["GET"])
@customer_required
def get_my_bookings():
    return get_customer_bookings(current_user.customer_id)


@app.route("/customer-bookings/<int:customer_id>", methods=["GET"])
@customer_required
def get_customer_bookings(customer_id):
    if customer_id != current_user.customer_id:
        return jsonify({"error": "You can only view your own bookings"}), 403
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


@app.route("/owner-earnings", methods=["GET"])
@owner_required
def get_owner_earnings():
    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute("""
            SELECT
                p.payment_id,
                p.booking_id,
                p.payment_date,
                p.amount,
                p.payment_method,
                p.payment_status,
                v.vehicle_name
            FROM PAYMENT p
            JOIN BOOKING b ON p.booking_id = b.booking_id
            JOIN VEHICLE v ON b.vehicle_id = v.vehicle_id
            WHERE v.owner_id = %s
              AND p.payment_status = 'Paid'
            ORDER BY p.payment_id DESC
        """, (current_user.owner_id,))

        payments = cursor.fetchall()

        total_earnings = sum(
            float(payment["amount"]) for payment in payments
        )

        for payment in payments:
            payment["amount"] = float(payment["amount"])
            payment["payment_date"] = (
                payment["payment_date"].isoformat()
                if payment["payment_date"] else None
            )

        return jsonify({
            "total_earnings": total_earnings,
            "paid_transactions": len(payments),
            "payments": payments
        })

    except mysql.connector.Error:
        app.logger.exception("Could not load owner earnings")
        return jsonify({"error": "Could not load earnings"}), 500

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

# ---------------- CUSTOMER PAYMENTS ----------------

@app.route("/my-payments", methods=["GET"])
@customer_required
def get_my_payments():
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute("""
            SELECT
                p.payment_id,
                p.booking_id,
                p.payment_date,
                p.amount,
                p.payment_method,
                p.payment_status,
                v.vehicle_name
            FROM PAYMENT p
            JOIN BOOKING b ON p.booking_id = b.booking_id
            JOIN VEHICLE v ON b.vehicle_id = v.vehicle_id
            WHERE b.customer_id = %s
            ORDER BY p.payment_id DESC
        """, (current_user.customer_id,))

        payments = cursor.fetchall()

        for payment in payments:
            payment["amount"] = float(payment["amount"])
            payment["payment_date"] = payment["payment_date"].isoformat()

        cursor.close()
        connection.close()
        return jsonify(payments)

    except mysql.connector.Error:
        return jsonify({"error": "Could not load payments"}), 500


@app.route("/payments", methods=["POST"])
@customer_required
def create_payment():
    data = request.get_json(silent=True) or {}
    booking_id = data.get("booking_id")
    method = data.get("payment_method")

    if not booking_id or method not in ("Demo UPI", "Demo Card", "Cash"):
        return jsonify({"error": "Choose a valid booking and payment method"}), 400

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute("""
            SELECT booking_id, total_amount, booking_status
            FROM BOOKING
            WHERE booking_id = %s AND customer_id = %s
            FOR UPDATE
        """, (booking_id, current_user.customer_id))

        booking = cursor.fetchone()

        if not booking:
            connection.rollback()
            return jsonify({"error": "Booking not found"}), 404

        if booking["booking_status"] != "Confirmed":
            connection.rollback()
            return jsonify({
                "error": "Payment is available only for confirmed bookings"
            }), 400

        cursor.execute("""
            SELECT payment_id
            FROM PAYMENT
            WHERE booking_id = %s AND payment_status = 'Paid'
            LIMIT 1
        """, (booking_id,))

        if cursor.fetchone():
            connection.rollback()
            return jsonify({"error": "This booking is already paid"}), 409

        cursor.execute("""
            INSERT INTO PAYMENT
                (booking_id, payment_date, amount, payment_method, payment_status)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            booking_id,
            date.today(),
            booking["total_amount"],
            method,
            "Paid"
        ))

        payment_id = cursor.lastrowid
        connection.commit()

        return jsonify({
            "message": "Demo payment successful",
            "payment_id": payment_id,
            "booking_id": booking_id,
            "amount": float(booking["total_amount"]),
            "payment_status": "Paid",
            "demo_only": True
        }), 201

    except mysql.connector.Error:
        if connection:
            connection.rollback()
        return jsonify({"error": "Payment could not be processed"}), 500

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

# ---------------- OWNER RENTAL REQUESTS ----------------


@app.route("/owner-bookings", methods=["GET"])
@owner_required
def get_owner_bookings():
    owner_id = current_user.owner_id

    connection = None
    cursor = None

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
                c.customer_id,
                v.vehicle_id,
                v.vehicle_name,
                v.registration_no
            FROM BOOKING b
            JOIN VEHICLE v ON b.vehicle_id = v.vehicle_id
            JOIN CUSTOMER c ON b.customer_id = c.customer_id
            WHERE v.owner_id = %s
            ORDER BY b.booking_id DESC
        """, (owner_id,))

        bookings = cursor.fetchall()

        for booking in bookings:
            booking["total_amount"] = float(booking["total_amount"])
            booking["start_date"] = booking["start_date"].isoformat()
            booking["end_date"] = booking["end_date"].isoformat()

        return jsonify(bookings)

    except mysql.connector.Error:
        app.logger.exception("Could not load owner bookings")
        return jsonify({"error": "Could not load rental requests"}), 500

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


    # ---------------- RUN SERVER ----------------

if __name__ == "__main__":
    app.run(debug=True, port=5000)
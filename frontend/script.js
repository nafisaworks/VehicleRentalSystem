const container = document.getElementById("vehicle-container");

// Create search/filter section
const filterSection = document.createElement("div");

filterSection.innerHTML = `
    <div class="filter-box">
        <input
            type="text"
            id="location-search"
            placeholder="📍 Enter location (e.g. Chennai)"
        >

        <button id="search-button">Search</button>

        <button id="show-all-button">Show All</button>
    </div>
`;

container.parentElement.insertBefore(filterSection, container);

const searchInput = document.getElementById("location-search");
const searchButton = document.getElementById("search-button");
const showAllButton = document.getElementById("show-all-button");

let allVehicles = [];

// Get vehicles from Flask API
fetch("http://127.0.0.1:5000/vehicles")
    .then(response => response.json())
    .then(vehicles => {

        allVehicles = vehicles;

        displayVehicles(allVehicles);

    })
    .catch(error => {

        container.innerHTML =
            "<p>Unable to load vehicles. Please make sure the backend is running.</p>";

        console.error(error);
    });


// Display vehicle cards
function displayVehicles(vehicles) {

    container.innerHTML = "";

    if (vehicles.length === 0) {

        container.innerHTML =
            "<p>No vehicles available in this location.</p>";

        return;
    }

    vehicles.forEach(vehicle => {

        const card = document.createElement("div");

        card.className = "vehicle-card";

        card.innerHTML = `
            <h3>${vehicle.vehicle_name}</h3>

            <p>
                <strong>Owner:</strong>
                ${vehicle.owner_name}
            </p>

            <p>
                <strong>📍 Location:</strong>
                ${vehicle.location}
            </p>

            <p>
                <strong>Registration:</strong>
                ${vehicle.registration_no}
            </p>

            <p>
                <strong>Model Year:</strong>
                ${vehicle.model_year}
            </p>

            <p>
                <strong>💰 Price:</strong>
                ₹${vehicle.price_per_day} / day
            </p>

            <p>
                <strong>🛠 Condition:</strong>
                ${vehicle.condition_description}
            </p>

            <p>
                <strong>Status:</strong>
                ${vehicle.availability_status}
            </p>

            <button class="book-button">
                Request to Book
            </button>

            <div class="booking-form" style="display: none;">

                <label>Customer</label>

                <select class="customer-select">
                    <option value="1">Rahul Kumar</option>
                </select>

                <label>Start Date</label>

                <input
                    type="date"
                    class="start-date"
                >

                <label>End Date</label>

                <input
                    type="date"
                    class="end-date"
                >

                <button class="calculate-price-button">
    Calculate Total
</button>

<p class="total-price"></p>

<button class="confirm-booking-button" style="display: none;">
    Confirm Booking
</button>

<p class="booking-message"></p>

            </div>
        `;

        container.appendChild(card);

        // Request to Book button
        const bookButton =
            card.querySelector(".book-button");

        const bookingForm =
            card.querySelector(".booking-form");

        bookButton.addEventListener("click", () => {

            bookingForm.style.display = "block";

            bookButton.style.display = "none";

        });


        // Confirm booking
// Calculate total price
const calculateButton =
    card.querySelector(".calculate-price-button");

const totalPrice =
    card.querySelector(".total-price");

const confirmButton =
    card.querySelector(".confirm-booking-button");


calculateButton.addEventListener("click", () => {

    const startDate =
        card.querySelector(".start-date").value;

    const endDate =
        card.querySelector(".end-date").value;


    if (!startDate || !endDate) {

        totalPrice.textContent =
            "Please select both dates.";

        return;
    }


    const start = new Date(startDate);
    const end = new Date(endDate);

    const difference =
        end - start;

    const days =
        difference / (1000 * 60 * 60 * 24);


    if (days <= 0) {

        totalPrice.textContent =
            "End date must be after start date.";

        return;
    }


    const total =
        days * vehicle.price_per_day;


    totalPrice.textContent =
        "Total Price: ₹" + total;


    confirmButton.style.display = "block";

});


// Confirm booking
confirmButton.addEventListener("click", () => {

    const customerId =
        card.querySelector(".customer-select").value;

    const startDate =
        card.querySelector(".start-date").value;

    const endDate =
        card.querySelector(".end-date").value;

    const message =
        card.querySelector(".booking-message");


    if (!customerId) {

        message.textContent =
            "Please select a customer.";

        return;
    }


    fetch("http://127.0.0.1:5000/bookings", {

        method: "POST",

        headers: {
            "Content-Type": "application/json"
        },

        body: JSON.stringify({

            customer_id:
                parseInt(customerId),

            vehicle_id:
                vehicle.vehicle_id,

            start_date:
                startDate,

            end_date:
                endDate

        })

    })

    .then(response => response.json())

    .then(result => {

        if (result.error) {

            message.textContent =
                "Error: " + result.error;

        } else {

            message.textContent =
                "Booking successful! Booking ID: "
                + result.booking_id
                + " | Total: ₹"
                + result.total_amount;

            confirmButton.style.display = "none";

        }

    })

        .catch(error => {

        console.error(error);

        message.textContent =
            "Unable to create booking.";

    });

}); // closes confirmButton.addEventListener

}); // closes vehicles.forEach

} // closes displayVehicles


// Search by location
searchButton.addEventListener("click", () => {

    const location = searchInput.value.trim().toLowerCase();

    if (location === "") {
        displayVehicles(allVehicles);
        return;
    }

    const filteredVehicles = allVehicles.filter(vehicle =>
        vehicle.location.toLowerCase().includes(location)
    );

    displayVehicles(filteredVehicles);
});


// Show all vehicles
showAllButton.addEventListener("click", () => {

    searchInput.value = "";

    displayVehicles(allVehicles);
    });
    
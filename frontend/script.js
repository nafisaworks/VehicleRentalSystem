const container = document.getElementById("vehicle-container");

fetch("http://127.0.0.1:5000/vehicles")
    .then(response => response.json())
    .then(vehicles => {

        container.innerHTML = "";

        vehicles.forEach(vehicle => {

            const card = document.createElement("div");

            card.className = "vehicle-card";

            card.innerHTML = `
                <h3>${vehicle.vehicle_name}</h3>
                <p><strong>Registration:</strong> ${vehicle.registration_no}</p>
                <p><strong>Model Year:</strong> ${vehicle.model_year}</p>
                <p><strong>Price per Day:</strong> ₹${vehicle.price_per_day}</p>
                <p><strong>Status:</strong> ${vehicle.availability_status}</p>
            `;

            container.appendChild(card);
        });

    })
    .catch(error => {

        container.innerHTML =
            "<p>Unable to load vehicles. Please make sure the backend is running.</p>";

        console.error(error);
    });
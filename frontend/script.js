const API = "http://127.0.0.1:5000";
const container = document.getElementById("vehicle-container");
let allVehicles = [];
const filterSection = document.createElement("div");
filterSection.className = "filter-box";
filterSection.innerHTML = '<input type="search" id="location-search" placeholder="Search by location (e.g. Chennai)" aria-label="Search by location"><button id="search-button">Search</button><button id="show-all-button" class="secondary">Show all</button>';
container.before(filterSection);
container.className = "vehicle-grid";
const searchInput = document.getElementById("location-search");

fetch(`${API}/vehicles`)
 .then(r => { if (!r.ok) throw new Error("Unable to load vehicles"); return r.json(); })
 .then(vehicles => { allVehicles = vehicles; displayVehicles(allVehicles); })
 .catch(error => { container.innerHTML = '<p class="notice">Unable to load vehicles. Please make sure the backend is running.</p>'; console.error(error); });

function displayVehicles(vehicles) {
 container.innerHTML = "";
 if (!vehicles.length) { container.innerHTML = '<p class="notice">No approved vehicles are available for this search yet. Try another location or check back soon.</p>'; return; }
 vehicles.forEach(vehicle => {
  const card = document.createElement("article"); card.className = "vehicle-card";
  const content = document.createElement("div"); content.className = "vehicle-content";
  const photo = document.createElement("div"); photo.className = "vehicle-photo"; photo.setAttribute("aria-hidden", "true"); photo.textContent = "🚘";
  const title = document.createElement("h3"); title.textContent = vehicle.vehicle_name || "Available vehicle";
  const price = document.createElement("p"); price.className = "vehicle-price"; price.textContent = `₹${vehicle.price_per_day} / day`;
  const details = document.createElement("p"); details.className = "vehicle-meta"; details.textContent = `⌖ ${vehicle.location || "Location not specified"}`;
  const year = document.createElement("p"); year.className = "vehicle-meta"; year.textContent = `Model year: ${vehicle.model_year || "Not specified"}`;
  const owner = document.createElement("p"); owner.className = "vehicle-meta"; owner.textContent = `Shared by ${vehicle.owner_name || "vehicle owner"}`;
  const bookButton = document.createElement("button"); bookButton.textContent = "Choose dates";
  const form = document.createElement("div"); form.className = "booking-form"; form.hidden = true;
  form.innerHTML = '<div><label>Pick-up date</label><input type="date" class="start-date" required></div><div><label>Return date</label><input type="date" class="end-date" required></div><button class="calculate-price-button secondary" type="button">Calculate total</button><p class="total-price"></p><button class="confirm-booking-button" type="button" hidden>Request booking</button><p class="booking-message" role="status"></p>';
  content.append(title, price, details, year, owner, bookButton, form); card.append(photo, content); container.append(card);
  const start = form.querySelector(".start-date"), end = form.querySelector(".end-date"), total = form.querySelector(".total-price"), confirm = form.querySelector(".confirm-booking-button"), message = form.querySelector(".booking-message");
  bookButton.addEventListener("click", async () => {
   try { const r = await fetch(`${API}/customer/me`, { credentials: "include" }); if (!r.ok) { message.innerHTML = 'Please <a href="customer-auth.html"><strong>log in</strong></a> or <a href="customer-register.html"><strong>create an account</strong></a> before booking.'; form.hidden = false; bookButton.hidden = true; return; } form.hidden = false; bookButton.hidden = true; }
   catch { message.textContent = "Unable to check your account. Please ensure the backend is running."; form.hidden = false; }
  });
  form.querySelector(".calculate-price-button").addEventListener("click", () => {
   if (!start.value || !end.value) { total.textContent = "Please select both dates."; return; }
   const days = (Date.parse(`${end.value}T00:00:00`) - Date.parse(`${start.value}T00:00:00`)) / 86400000;
   if (!Number.isFinite(days) || days <= 0) { total.textContent = "Return date must be after pick-up date."; confirm.hidden = true; return; }
   total.textContent = `Estimated total for ${days} day(s): ₹${days * Number(vehicle.price_per_day)}`; confirm.hidden = false;
  });
  confirm.addEventListener("click", async () => {
   message.textContent = "Submitting your booking request…";
   try { const r = await fetch(`${API}/bookings`, { method: "POST", credentials: "include", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ vehicle_id: vehicle.vehicle_id, start_date: start.value, end_date: end.value }) }); const d = await r.json();
    if (!r.ok) { message.textContent = d.error || "Unable to create booking."; if (r.status === 401) message.innerHTML = 'Please <a href="customer-auth.html">log in</a> before booking.'; return; }
    message.textContent = `Request submitted. Booking #${d.booking_id} · Total ₹${d.total_amount}.`; confirm.hidden = true;
   } catch (e) { console.error(e); message.textContent = "Unable to submit the request. Please try again."; }
  });
 });
}
document.getElementById("search-button").addEventListener("click", () => { const q = searchInput.value.trim().toLowerCase(); displayVehicles(q ? allVehicles.filter(v => String(v.location || "").toLowerCase().includes(q)) : allVehicles); });
document.getElementById("show-all-button").addEventListener("click", () => { searchInput.value = ""; displayVehicles(allVehicles); });

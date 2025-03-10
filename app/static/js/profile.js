document.addEventListener("DOMContentLoaded", function () {
    const logoutButton = document.getElementById("logout-btn");

    logoutButton.addEventListener("click", async function (event) {
        event.preventDefault();

        try {
            const response = await fetch("/logout", { method: "POST" });

            if (response.redirected) {
                window.location.href = response.url;
            } else {
                console.error("Logout failed");
            }
        } catch (error) {
            console.error("Error logging out:", error);
        }
    });
});

document.addEventListener("DOMContentLoaded", async function () {
    const deviceList = document.getElementById("device-list");
    const removeDeviceDropdown = document.getElementById("remove-device-dropdown");

    async function fetchDevices() {
        try {
            console.log("✅ Fetching devices...");
            const response = await fetch("/devices"); // Get devices from backend

            if (response.ok) {
                const devices = await response.json();
                console.log("✅ Devices received:", devices); // Debugging

                deviceList.innerHTML = ""; // Clear list before repopulating
                removeDeviceDropdown.innerHTML = '<option value="">Select Device</option>'; // Reset dropdown

                if (devices.length === 0) {
                    console.log("❌ No devices found.");
                }

                devices.forEach(device => addDeviceToUI(device.name, device.serial));
            } else {
                console.error("❌ Failed to fetch devices:", await response.text());
            }
        } catch (error) {
            console.error("❌ Error fetching devices:", error);
        }
    }

    function addDeviceToUI(deviceName, serial) {
        console.log(`✅ Adding Device: ${deviceName}, Serial: ${serial}`); // Debugging

        // ✅ Add Device to List
        const deviceElement = document.createElement("div");
        deviceElement.classList.add("device-item");
        deviceElement.innerHTML = `
            <img src="/static/images/device.png" alt="Device">
            <h3>${deviceName}</h3>
            <p class="device-id">Serial: ${serial}</p>
        `;
        deviceList.appendChild(deviceElement);

        // ✅ Add Device to Dropdown
        const option = document.createElement("option");
        option.value = serial;
        option.textContent = deviceName;
        removeDeviceDropdown.appendChild(option);
    }

    // ✅ Load Devices on Page Load
    fetchDevices();
    adjustDeviceContainerHeight();
    // checkEmptyDeviceList();
});









document.addEventListener("DOMContentLoaded", async function () {
    const greetingElement = document.getElementById("user-name");
    const greetingTextElement = document.getElementById("greeting-text");

    function getTimeBasedGreeting() {
        const currentHour = new Date().getHours();
        if (currentHour >= 5 && currentHour < 12) {
            return "Good Morning";
        } else if (currentHour >= 12 && currentHour < 18) {
            return "Good Afternoon";
        } else {
            return "Good Evening";
        }
    }

    try {
        // Fetch user info for greeting
        const userResponse = await fetch("/user-info");
        if (userResponse.ok) {
            const userData = await userResponse.json();
            greetingElement.textContent = userData.fullname.toUpperCase(); // Uppercase username
        }

        // Set time-based greeting
        greetingTextElement.textContent = getTimeBasedGreeting();
    } catch (error) {
        console.error("Failed to fetch user info:", error);
    }
});




document.addEventListener("DOMContentLoaded", async function () {
    const addDeviceBtn = document.getElementById("add-device-btn");
    const devicePopup = document.getElementById("device-popup");
    const submitDeviceBtn = document.getElementById("submit-device");
    const cancelDeviceBtn = document.getElementById("cancel-device");
    const deviceList = document.getElementById("device-list");
    const removeDeviceDropdown = document.getElementById("remove-device-dropdown");

    // ✅ Open the Add Device Popup
    addDeviceBtn.addEventListener("click", function () {
        console.log("🔵 Opening device popup...");
        devicePopup.style.display = "block";
    });

    // ✅ Close the Add Device Popup
    cancelDeviceBtn.addEventListener("click", function () {
        console.log("🔴 Closing device popup...");
        devicePopup.style.display = "none";
    });



    // ✅ Fetch Devices from the Database on Page Load
    async function fetchDevices() {
        try {
            console.log("✅ Fetching devices...");
            const response = await fetch("/devices");

            if (response.ok) {
                const devices = await response.json();
                console.log("✅ Devices received:", devices);

                deviceList.innerHTML = ""; // Clear list before repopulating
                removeDeviceDropdown.innerHTML = '<option value="">Select Device</option>'; // Reset dropdown

                if (devices.length === 0) {
                    console.log("❌ No devices found.");
                }

                devices.forEach(device => addDeviceToUI(device.name, device.serial));
            } else {
                console.error("❌ Failed to fetch devices:", await response.text());
            }
        } catch (error) {
            console.error("❌ Error fetching devices:", error);
        }
    }

    // ✅ Add a New Device to the Database and UI
    submitDeviceBtn.addEventListener("click", async function () {
        const deviceName = document.getElementById("device-name").value.trim();
        const serial = document.getElementById("device-id").value.trim();

        if (deviceName === "" || serial === "") {
            alert("Please fill in all fields.");
            return;
        }

        try {
            const response = await fetch("/devices", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ name: deviceName, serial: serial })
            });

            if (response.ok) {
                addDeviceToUI(deviceName, serial);
                alert("✅ Device added successfully!");
                fetchDevices(); // Refresh device list
            } else {
                alert("❌ Failed to add device.");
            }
        } catch (error) {
            console.error("❌ Error adding device:", error);
        }

        devicePopup.style.display = "none";
        document.getElementById("device-name").value = "";
        document.getElementById("device-id").value = "";
    });

    // ✅ Function to Add Device to the UI
    function addDeviceToUI(deviceName, serial) {
        console.log(`✅ Adding Device: ${deviceName}, Serial: ${serial}`);

        // ✅ Create device card
        const deviceElement = document.createElement("div");
        deviceElement.classList.add("device-item");
        deviceElement.innerHTML = `
            <img src="/static/images/device.png" alt="Device">
            <h3>${deviceName}</h3>
            <p class="device-id">Serial: ${serial}</p>
        `;
        deviceList.appendChild(deviceElement);

        // ✅ Add Device to Dropdown
        const option = document.createElement("option");
        option.value = serial;
        option.textContent = deviceName;
        removeDeviceDropdown.appendChild(option);
    }

    // ✅ Load Devices on Page Load
    fetchDevices();
    adjustDeviceContainerHeight();
});






























function adjustDeviceContainerHeight() {
    const deviceContainer = document.getElementById("device-container");
    const deviceItems = document.querySelectorAll(".device-item");

    // Calculate required height (each row takes about 200px, adjust as needed)
    const requiredHeight = Math.ceil(deviceItems.length / 3) * 200;

    // Only expand height, but do not shrink if it's already bigger
    const currentHeight = parseInt(window.getComputedStyle(deviceContainer).minHeight, 10);
    if (requiredHeight > currentHeight) {
        deviceContainer.style.minHeight = `${requiredHeight}px`;
    }
}

// function checkEmptyDeviceList() {
//     const deviceContainer = document.getElementById("device-container");
//     const deviceList = document.getElementById("device-list");
//     let emptyMessage = document.querySelector("#device-container .empty-message");

//     // Check if there are any actual device items inside the device list
//     if (deviceList.children.length === 0) {
//         if (!emptyMessage) {
//             emptyMessage = document.createElement("p");
//             emptyMessage.classList.add("empty-message");
//             emptyMessage.textContent = "No devices added yet.";
//             deviceContainer.appendChild(emptyMessage);
//         }
//         deviceContainer.style.justifyContent = "center"; 
//         deviceContainer.style.alignItems = "center";
//     } else {
//         // ✅ **If devices exist, remove the empty message**
//         if (emptyMessage) {
//             emptyMessage.remove();
//         }
//         deviceContainer.style.justifyContent = "flex-start"; 
//         deviceContainer.style.alignItems = "flex-start";
//     }
// }
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

document.addEventListener("DOMContentLoaded", checkEmptyDeviceList);

document.addEventListener("DOMContentLoaded", async function () {
    const greetingElement = document.getElementById("user-name");
    const greetingTextElement = document.getElementById("greeting-text");

    const addDeviceBtn = document.getElementById("add-device-btn");
    const devicePopup = document.getElementById("device-popup");
    const submitDeviceBtn = document.getElementById("submit-device");
    const cancelDeviceBtn = document.getElementById("cancel-device");
    const deviceList = document.getElementById("device-list");
    const removeDeviceDropdown = document.getElementById("remove-device-dropdown");

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

    // Open Popup
    addDeviceBtn.addEventListener("click", function () {
        devicePopup.style.display = "block";
    });

    // Close Popup
    cancelDeviceBtn.addEventListener("click", function () {
        devicePopup.style.display = "none";
    });

    // Submit Device
    submitDeviceBtn.addEventListener("click", function () {
        const deviceName = document.getElementById("device-name").value.trim();
        const deviceId = document.getElementById("device-id").value.trim();

        if (deviceName === "" || deviceId === "") {
            alert("Please fill in all fields.");
            return;
        }

        // Add Device to Device Container
        const deviceElement = document.createElement("div");
        deviceElement.classList.add("device-item");
        deviceElement.innerHTML = `
            <img src="/static/images/device.png" alt="Device">
            <h3>${deviceName}</h3>
            <p class="device-id">Device ID: ${deviceId}</p>
        `;

        deviceList.appendChild(deviceElement);

        // Add Device to Dropdown
        const option = document.createElement("option");
        option.value = deviceId;
        option.textContent = deviceName;
        removeDeviceDropdown.appendChild(option);

        // Close Popup
        devicePopup.style.display = "none";

        // Clear Input Fields
        document.getElementById("device-name").value = "";
        document.getElementById("device-id").value = "";

        checkEmptyDeviceList();
        adjustDeviceContainerHeight();
    });
    
    checkEmptyDeviceList();
}); // <-- Closing the DOMContentLoaded event listener

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

function checkEmptyDeviceList() {
    const deviceContainer = document.getElementById("device-container");
    const deviceList = document.getElementById("device-list");
    let emptyMessage = document.querySelector("#device-container .empty-message");

    // Check if there are any actual device items inside the device list
    if (deviceList.children.length === 0) {
        if (!emptyMessage) {
            emptyMessage = document.createElement("p");
            emptyMessage.classList.add("empty-message");
            emptyMessage.textContent = "No devices added yet.";
            deviceContainer.appendChild(emptyMessage);
        }
        deviceContainer.style.justifyContent = "center"; 
        deviceContainer.style.alignItems = "center";
    } else {
        // ✅ **If devices exist, remove the empty message**
        if (emptyMessage) {
            emptyMessage.remove();
        }
        deviceContainer.style.justifyContent = "flex-start"; 
        deviceContainer.style.alignItems = "flex-start";
    }
}
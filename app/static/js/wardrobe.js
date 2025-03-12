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
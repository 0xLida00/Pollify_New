document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll(".follow-form").forEach((form) => {
        form.addEventListener("submit", function (event) {
            event.preventDefault();

            const button = form.querySelector("button");
            const csrfToken = this.querySelector("input[name=csrfmiddlewaretoken]").value;

            button.disabled = true; // Prevent multiple clicks

            fetch(this.action, {
                method: "POST",
                headers: {
                    "X-CSRFToken": csrfToken,
                    "Content-Type": "application/json",
                    "Cache-Control": "no-cache", // Prevent caching
                },
                cache: "no-store",
            })
                .then((response) => response.json())
                .then((data) => {
                    if (data.success) {
                        fetch(window.location.href, { cache: "no-store" })  // Ensure latest follow state is fetched
                            .then(res => res.text())
                            .then((html) => {
                                let doc = new DOMParser().parseFromString(html, "text/html");
                                let newButton = doc.querySelector(".follow-form button");
                                button.outerHTML = newButton.outerHTML; // Replace button to reflect correct state
                            });
                    } else {
                        alert("An error occurred. Please try again.");
                    }
                })
                .catch((error) => {
                    console.error("Error:", error);
                    alert("An error occurred. Please try again.");
                })
                .finally(() => {
                    button.disabled = false;
                });
        });
    });
});
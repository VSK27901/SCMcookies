document.addEventListener("DOMContentLoaded", function (event) {
    // Function to toggle the navigation menu
    const showNavbar = (toggleId, navId, bodyId, headerId) => {
        const toggle = document.getElementById(toggleId),
            nav = document.getElementById(navId),
            bodypd = document.getElementById(bodyId),
            headerpd = document.getElementById(headerId)

        if (toggle && nav && bodypd && headerpd) {
            // Toggle the navigation menu visibility on click
            toggle.addEventListener('click', () => {
                nav.classList.toggle('show')
                toggle.classList.toggle('bx-x')
                bodypd.classList.toggle('body-pd')
                headerpd.classList.toggle('body-pd')
            })
        }
    }

    // Call the showNavbar function to enable the navigation menu toggle
    showNavbar('header-toggle', 'nav-bar', 'body-pd', 'header')

    // Get all navigation links
    const linkColor = document.querySelectorAll('.nav_link')

    // Function to handle link click and change its color
    function colorLink() {
        if (linkColor) {
            // Remove 'active' class from all links
            linkColor.forEach(l => l.classList.remove('active'))
            // Add 'active' class to the clicked link
            this.classList.add('active')
        }
    }

    // Add click event listener to navigation links
    linkColor.forEach(l => l.addEventListener('click', colorLink))

    // Check if the username element exists
    const usernameElement = document.querySelector('.username');
    if (usernameElement) {
        // Check if the username is empty (not logged in)
        if (usernameElement.textContent.trim() === '') {
            // Hide the user-info section
            document.querySelector('.user-info').style.display = 'none';
        }
    }

    // Get the 'Create Shipment' button and shipment iframe elements
    const createShipmentBtn = document.getElementById("create-shipment-btn");
    const createshipmentIframe = document.getElementById("createshipment-iframe");

    // Add click event listener to 'Create Shipment' button
    createShipmentBtn.addEventListener("click", function () {
        // Show the shipment iframe when the button is clicked
        createshipmentIframe.style.display = "block";
    });
});

document.addEventListener("DOMContentLoaded", function () {
    var errorMessage = document.getElementById("error-message");

    if (errorMessage) {
        errorMessage.style.display = "block";
        setTimeout(function () {
            errorMessage.style.display = "none"; 
        }, 5000); 
    }
});
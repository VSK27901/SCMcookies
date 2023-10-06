// Assuming you have a login form and a button with an ID "loginButton" to trigger the login request
const loginButton = document.getElementById("loginButton");

// Add an event listener to the login button
loginButton.addEventListener("click", () => {
    const username = document.getElementById("usernameInput").value;
    const password = document.getElementById("passwordInput").value;

    // Make an AJAX request to your FastAPI login endpoint
    // Replace 'YOUR_API_ENDPOINT' with the actual endpoint URL
    fetch('/login', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: `username=${username}&password=${password}`,
    })
        .then(response => response.json())
        .then(data => {
            if (data.access_token) {
                // Store the access token in local storage
                localStorage.setItem('access_token', data.access_token);

                // Redirect the user to the dashboard or perform any other actions
                window.location.href = '/dashboard'; // Replace with your dashboard URL
            } else {
                // Handle login errors, e.g., display an error message
                alert(data.error_message || 'Login failed');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('An error occurred during login');
        });
});

// Get the JWT token from local storage
const token = localStorage.getItem('access_token');

// Define a function to decode the JWT token
function decodeToken(token) {
    try {
        const payload = JSON.parse(atob(token.split('.')[1]));
        return payload;
    } catch (error) {
        console.error('Error decoding token:', error);
        return null;
    }
}

// Call the decodeToken function to get the user data
const userData = decodeToken(token);

// Check if userData contains the user information
if (userData) {
    const username = userData.sub; // Assuming 'sub' contains the username
    const email = userData.email; // Assuming 'email' contains the email
    console.log(`Current User: Username - ${username}, Email - ${email}`);
} else {
    console.log('No user data found. The token may be invalid or missing.');
}

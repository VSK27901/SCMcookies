// JavaScript variables to track current page and rows per page
let currentPage = 1;
const rowsPerPage = 10; // You can adjust this value as needed

// Function to update the table based on the current page
function updateTable() {
    const tableRows = document.querySelectorAll("#data-table tbody tr");
    const totalPages = Math.ceil(tableRows.length / rowsPerPage);

    // Hide all rows
    tableRows.forEach((row) => {
        row.style.display = "none";
    });

    // Calculate start and end indices for the current page
    const startIndex = (currentPage - 1) * rowsPerPage;
    const endIndex = startIndex + rowsPerPage;

    // Show rows for the current page
    for (let i = startIndex; i < endIndex; i++) {
        if (tableRows[i]) {
            tableRows[i].style.display = "table-row";
        }
    }

    // Update current page indicator
    document.getElementById("currentPage").textContent = `Page ${currentPage} of ${totalPages}`;
}

// Handle "Next" button click
document.getElementById("nextPage").addEventListener("click", () => {
    const tableRows = document.querySelectorAll("#data-table tbody tr");
    const totalPages = Math.ceil(tableRows.length / rowsPerPage);

    if (currentPage < totalPages) {
        currentPage++;
        updateTable();
    }
});

// Handle "Previous" button click
document.getElementById("prevPage").addEventListener("click", () => {
    if (currentPage > 1) {
        currentPage--;
        updateTable();
    }
});

// Initial table update
updateTable();

document.addEventListener("DOMContentLoaded", function () {
    var errorMessage = document.getElementById("error-message");

    if (errorMessage) {
        errorMessage.style.display = "block";
        setTimeout(function () {
            errorMessage.style.display = "none"; 
        }, 5000); 
    }
});
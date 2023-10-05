const tableScroll = document.querySelector('.table-scroll');

tableScroll.addEventListener('scroll', function () {
    const translate = `translate(0, ${this.scrollTop}px)`;
    this.querySelector('thead').style.transform = translate;
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
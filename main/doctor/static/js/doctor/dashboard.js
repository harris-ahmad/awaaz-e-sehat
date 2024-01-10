// remove the flashed messages after 5 seconds
setTimeout(function() {
    var messages = document.getElementById('flashed-messages');
    while (messages.firstChild) {
        messages.removeChild(messages.firstChild);
    }
}, 3000); // 3000 milliseconds = 3 seconds
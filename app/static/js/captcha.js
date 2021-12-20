
function enable_submit () {     // data-callback function
    document.getElementById("submit").disabled = false;
}

function disable_submit () {    // data-expired-callback function
    document.getElementById("submit").disabled = true;
}

disable_submit()

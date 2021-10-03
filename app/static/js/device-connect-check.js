
/* Check Internet connection every 2s until established */
async function check() {
    url = "https://www.google.com/"
    result = document.getElementById("result");
    spinner = document.getElementById("spinner");
    last = document.getElementById("last");
    connected = false;
    while (!connected) {
        console.log("ping " + url + "...")
        ping(url).then(function(delta) {
            // OK: connected!
            spinner.style.setProperty("transition", "all 1s");
            spinner.style.setProperty("border-right-color", "inherit");
            spinner.classList.replace("text-primary", "text-success");
            spinner.classList.add("bg-success");
            result.style.setProperty("transition", "all 1s");
            result.style.setProperty("opacity", "1", "important");
            last.style.setProperty("transition", "all 1s");
            last.classList.replace("bg-secondary", "bg-success");
            connected = true;
        }).catch(function(err) {
            // Error: not connected, retry
            console.log("err")
        });
        await new Promise(r => setTimeout(r, 2000));
    }
}

check();

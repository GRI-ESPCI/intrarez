
function reload() {
    var params = new URLSearchParams(window.location.search);
    step = params.get("step", 0);
    step = Number(step);
    if (isNaN(step)) {
        params.delete("step");
    } else {
        params.set("step", step + 1);
    }
    window.location.search = params.toString();
}

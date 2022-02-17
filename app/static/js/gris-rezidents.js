// Sort function
var table = document.getElementById("rezidents-table");
var rows = Array.prototype.slice.call(table.children);

var svgs = [];
svgs[1] = document.getElementById("icon-template-up");
svgs[-1] = document.getElementById("icon-template-down");

var sort_col = null;
var sort_way = 0;

function do_sort(col, way) {
    var svg = document.getElementById("sort-svg-" + col);
    var sort_fn;
    if (way) {      // 1 ou -1 : trier
        svg.innerHTML = svgs[way].innerHTML;
        rows = rows.sort(function (r1, r2) {
            // On trie selon col et way
            return (r1.dataset[col] == r2.dataset[col]) ? 0
                : (way * ((r1.dataset[col] > r2.dataset[col]) ? 1 : -1))
        });
        rows.forEach(row => table.appendChild(row));
        // appendChild va déplacer la ligne à la fin de la table
        // (pas de duplication implicite des nodes DOM)
    } else {        // 0 : effacer l'indicateur de tri
        svg.innerHTML = "";
    }
}

function sort(col) {
    if (col != sort_col) {
        // Pas de tri sur cette colonne -> efface autre tri, et croissant
        if (sort_col)  do_sort(sort_col, 0);
        sort_col = col;
        sort_way = 1;
        do_sort(col, sort_way)
    } else {
        // Tri croissant <-> décroissant
        sort_way = -sort_way;
        do_sort(col, sort_way)
    }
}


// Ban modal
var moBan = document.getElementById("mo-ban")
var title = moBan.querySelector('.modal-title')
var [template_new, template_update] = title.textContent.split(" || ")
var submit =  moBan.querySelector('#submit')
var [submit_text_new, submit_text_update] = submit.value.split(" || ")
moBan.addEventListener("show.bs.modal", function (event) {
    // Button that triggered the modal
    var button = event.relatedTarget
    // Update the modal's content.
    moBan.querySelector('#rezident').value = button.dataset["rezidentId"]
    moBan.querySelectorAll(".form-control").forEach(elem => elem.value = null)
    moBan.querySelector('#infinite').checked = true
    update_checkbox()
    if (button.dataset["banId"]) {
        // Update existing ban
        title.textContent = template_update
            .replace("_name_", button.dataset["rezidentName"])
        moBan.querySelector('#ban_id').value = button.dataset["banId"]
        if (button.dataset["banEnd"]) {
            moBan.querySelector('#infinite').checked = false
            update_checkbox()
            var end = moment.utc(new Number(button.dataset["banEnd"]) * 1000);
            var interval = moment.duration(end.diff());
            moBan.querySelector('#hours').value = interval.hours()
            moBan.querySelector('#days').value = interval.days()
            moBan.querySelector('#months').value = interval.months()
        }
        moBan.querySelector('#reason').value = button.dataset["banReason"]
        moBan.querySelector('#message').value = button.dataset["banMessage"]
        submit.value = submit_text_update
        moBan.querySelector('#unban').hidden = false
    } else {
        // New ban
        moBan.querySelector('#ban_id').value = null
        title.textContent = template_new
            .replace("_name_", button.dataset["rezidentName"])
        submit.value = submit_text_new
        moBan.querySelector('#unban').hidden = true
    }
})


function update_checkbox() {
    if (infiniteCheckbox.checked) {
        moBan.querySelectorAll(".duration-control").forEach(
            elem => elem.classList.add("text-muted")
            )
        moBan.querySelectorAll(".duration-input").forEach(
            elem => elem.disabled = true
        )
    } else {
        moBan.querySelectorAll(".duration-control").forEach(
            elem => elem.classList.remove("text-muted")
            )
        moBan.querySelectorAll(".duration-input").forEach(
            elem => elem.disabled = false
        )
    }
}

// Ban modal checkbox
var infiniteCheckbox = moBan.querySelector('#infinite')
infiniteCheckbox.addEventListener("change", update_checkbox)

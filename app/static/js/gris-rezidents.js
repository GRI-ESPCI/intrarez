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

// Enable tooltips
var tooltipTriggerList = [].slice.call(
    document.querySelectorAll('[data-bs-toggle="tooltip"]')
);
var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
    return new bootstrap.Tooltip(tooltipTriggerEl)
})

// Get cards and buttons
offer_cards = document.getElementsByName("offer_card");
method_cards = document.getElementsByName("method_card");
offer_buttons = document.getElementsByName("offer_button");
method_buttons = document.getElementsByName("method_button");

// Progression
methods_shown = false;
pay_shown = false;

// Selected options variables
base_href = document.getElementById("pay_button").href;
chosen_offer = "";
chosen_method = "";
price = "";
phrase = "";

function chose_offer(offer) {
    // Display option as selected
    chosen_offer = offer;
    card = document.getElementById("card_offer_" + offer);
    button = document.getElementById("offer_button_" + offer);
    for (i = 0; i < offer_cards.length; i++) {
        offer_cards[i].style.setProperty("transition", "all 0.2s");
        if (offer_cards[i] == card) {
            offer_cards[i].style.setProperty("opacity", "1", "important");
        } else {
            offer_cards[i].style.setProperty("opacity", "0.5", "important");
        }
    }
    for (i = 0; i < offer_buttons.length; i++) {
        offer_buttons[i].style.setProperty("transition", "all 0.2s");
        if (offer_buttons[i] == button) {
            offer_buttons[i].classList.replace("btn-outline-secondary",
                                               "btn-success");
        } else {
            offer_buttons[i].classList.replace("btn-success",
                                               "btn-outline-secondary");
        }
    }
    // Display methods section
    if (!methods_shown) {
        methods_shown = true;
        document.getElementById("methods_header").hidden = false;
        document.getElementById("methods_row").hidden = false;
    }
    // Scroll to next step
    if (pay_shown) {
        document.getElementById("pay_row").scrollIntoView();
        document.getElementById("pay_button").focus()
    } else {
        document.getElementById("methods_header").scrollIntoView();
    }
    // Prepare pay button
    price = button.dataset["price"];
    update_pay_button();
}

function chose_method(method) {
    // Display option as selected
    chosen_method = method;
    card = document.getElementById("card_method_" + method);
    button = document.getElementById("method_button_" + method);
    for (i = 0; i < method_cards.length; i++) {
        method_cards[i].style.setProperty("transition", "all 0.2s");
        if (method_cards[i] == card) {
            method_cards[i].style.setProperty("opacity", "1", "important");
        } else {
            method_cards[i].style.setProperty("opacity", "0.5", "important");
        }
    }
    for (i = 0; i < method_buttons.length; i++) {
        method_buttons[i].style.setProperty("transition", "all 0.2s");
        if (method_buttons[i] == button) {
            method_buttons[i].classList.replace("btn-outline-secondary", "btn-success");
        } else {
            method_buttons[i].classList.replace("btn-success", "btn-outline-secondary");
        }
    }
    // Prepare pay button
    phrase = button.dataset["phrase"];
    update_pay_button();
    // Display pay button
    if (!pay_shown) {
        pay_shown = true;
        document.getElementById("pay_header").hidden = false;
        document.getElementById("pay_row").hidden = false;
    }
    // Scroll to next step
    document.getElementById("pay_row").scrollIntoView();
    document.getElementById("pay_button").focus()
}

function update_pay_button() {
    pay_button = document.getElementById("pay_button")
    pay_button.innerHTML = phrase.replace("[]", price);
    params = new URLSearchParams({"method": chosen_method,
                                  "offer": chosen_offer});
    pay_button.href = "?" + params.toString();
}

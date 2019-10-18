let cardBody = document.getElementById("card-body")

function prepareUpdate() {
    let refresh_timeout = document.getElementById("refresh-timeout").innerText
    setTimeout(updateCardBody, parseInt(refresh_timeout, 10))
}


function updateCardBody() {
    fetch("http://localhost:8080/update")
        .then((response) => response.text())
        .then((text) => {
            if (cardBody.innerHTML.valueOf() != text.valueOf()) {
                cardBody.innerHTML = text
            }
        })
    prepareUpdate()
}

prepareUpdate()

let cardBody = document.getElementById("card-body")

function prepareUpdate() {
    let end = parseInt(document.getElementById("end").innerText, 10)
    let timeout = end - Date.now() > 0 ? end - Date.now() : 5000
    setTimeout(updateCardBody, timeout)
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

let cardBody = document.getElementById("card-body")
let updateUrl = document.getElementById("info-update").attributes["data-update-url"].value

function prepareUpdate() {
    let end = parseInt(document.getElementById("end").innerText, 10)
    let timeout = end - Date.now() > 0 ? end - Date.now() : 5000
    setTimeout(updateCardBody, timeout)
}


function updateCardBody() {
    fetch(updateUrl)
        .then((response) => response.text())
        .then((text) => {
            if (cardBody.innerHTML.valueOf() != text.valueOf()) {
                document.querySelector(".card-body").classList.add("fade-out")
                setTimeout(() => {
                    cardBody.innerHTML = text
                    document.querySelector(".card-body").classList.remove("fade-out")
                }, 200)
            }
        })
    prepareUpdate()
}

prepareUpdate()

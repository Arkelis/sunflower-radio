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
            // get current card body
            let cardBody = document.getElementById("card-body")

            // build dom element with fetched data
            let respNode = document.createElement("div")
            respNode.id = "card-body"
            respNode.classList.add("card-body")
            respNode.innerHTML = text

            let divsToCheck = [".thumbnail", ".station", ".broadcast-title", ".details", "#end"]
            let divsToUpdate = []
            
            divsToCheck.forEach(element => {
                let currentEl = cardBody.querySelector(element)
                let respEl = respNode.querySelector(element)
                if (!currentEl.isEqualNode(respEl)) {
                    divsToUpdate.push(element)
                }
            })

            divsToUpdate.forEach(element => {document.querySelector(element).classList.add("fade-out")})
            setTimeout(() => {
                divsToUpdate.forEach(element => {
                    cardBody.querySelector(element).replaceWith(respNode.querySelector(element))
                    // cardBody.querySelector(element).classList.remove("fade-out")
                })
            }, 400)
        })
    prepareUpdate()
}

document.getElementsByTagName("audio").play()
prepareUpdate()

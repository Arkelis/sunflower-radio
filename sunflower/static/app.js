let updateUrl = document.getElementById("info-update").attributes["data-update-url"].value

function prepareUpdate() {
    let end = parseInt(document.getElementById("current-broadcast-end").innerText, 10)
    let timeout = end - Date.now() > 0 ? end - Date.now() : 5000
    setTimeout(updateCardBody, timeout)
}


function updateCardBody(schedulePrepare = true) {
    fetch(updateUrl)
        .then((response) => response.json())
        .then((data) => {


            let textsToCheck = [
                "current-station",
                "current-broadcast-title",
                "current-show-title",
                "current-broadcast-summary",
                "current-broadcast-end"
            ]
            let thumbnailNode = document.getElementById("current-thumbnail")
            let thumbnailSrc = thumbnailNode.attributes.src.value
            let divsToUpdate = []

            // check text info
            textsToCheck.forEach(element => {
                let fetchedText = data[element.replace(/-/g, "_")]
                let nodeToUpdate = document.getElementById(element)
                let currentText = nodeToUpdate.innerHTML
                if (currentText != fetchedText){
                    divsToUpdate.push([nodeToUpdate, fetchedText])
                }
            })

            // check thumbnail src
            let thumbnailUpdated
            let fetchedThumbnailSrc = data.current_thumbnail
            if (thumbnailSrc != fetchedThumbnailSrc) {
                thumbnailNode.parentElement.classList.add("fade-out")
                thumbnailUpdated = true
            } else {
                thumbnailUpdated = false
            }


            divsToUpdate.forEach(element => {element[0].classList.add("fade-out")})
            setTimeout(() => {
                // update info
                divsToUpdate.forEach(element => {
                    element[0].innerText = element[1]
                    element[0].classList.remove("fade-out")
                })

                //update thumbnail if needed
                if (thumbnailUpdated) {
                    thumbnailNode.attributes.src.value = fetchedThumbnailSrc
                    thumbnailNode.parentElement.classList.remove("fade-out")
                }
            }, 400)
        })
    if (schedulePrepare) prepareUpdate()
}

// document.querySelector("audio").play()
prepareUpdate()

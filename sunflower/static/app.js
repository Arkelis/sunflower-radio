let updateUrl = document.getElementById("info-update").attributes["data-update-url"].value

function prepareUpdate() {
    let end = parseInt(document.getElementById("current-broadcast-end").innerText, 10)
    let timeout = end - Date.now() > 0 ? end - Date.now() : 5000
    setTimeout(updateCardBody, timeout)
}

class FlippedElement {
    y
    element

    get newY() {
        return this.element.getBoundingClientRect().y
    }

    constructor(element) {
        this.element = document.querySelector(element)
        this.y = this.newY
    }

    flip() {
        const newY = this.newY
        const deltaY = this.y - newY
        this.y = newY
        this.element.animate(
            [
                {
                    transform: `translateY(${deltaY}px)`
                },
                {
                    transform: "none"
                },
            ],
            {
                duration: 400,
                fill: "both",
                easing: "ease-in-out",
            })
        this.element.style.transform = `translateY(${deltaY}px)`
    }
}

let audioPlayer = new FlippedElement("audio")

function updateCardBody(schedulePrepare = true) {
    fetch(updateUrl)
        .then((response) => response.json())
        .then((data) => {


            let textsToCheck = [
                "current-station",
                "current-broadcast-title",
                "current-show-title",
                "current-broadcast-summary",
            ]
            let currentBroadcastEnd = document.getElementById("current-broadcast-end")
            let fetchedEnd = data.current_broadcast_end

            if (fetchedEnd <= currentBroadcastEnd.innerText) return

            let thumbnailNode = document.getElementById("current-thumbnail")
            let thumbnailSrc = thumbnailNode.attributes.src.value
            let divsToUpdate = []

            // check text info
            textsToCheck.forEach(element => {
                let fetchedText = data[element.replace(/-/g, "_")]
                let nodeToUpdate = document.getElementById(element)
                let currentText = nodeToUpdate.innerHTML
                if (currentText != fetchedText) {
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


            divsToUpdate.forEach(element => { element[0].classList.add("fade-out") })
            setTimeout(() => {
                // update info
                divsToUpdate.forEach(element => {
                    element[0].innerText = element[1]
                    element[0].classList.remove("fade-out")
                })
                audioPlayer.flip()

                currentBroadcastEnd.innerText = fetchedEnd

                //update thumbnail if needed
                if (thumbnailUpdated) {
                    thumbnailNode.attributes.src.value = fetchedThumbnailSrc
                    thumbnailNode.parentElement.classList.remove("fade-out")
                }
            }, 400)
        })
    if (schedulePrepare) prepareUpdate()
}

updateCardBody()

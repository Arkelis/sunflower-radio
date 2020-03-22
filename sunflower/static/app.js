let updateUrl = document.getElementById("info-update").attributes["data-update-url"].value
let eventsUrl = document.getElementById("info-update").attributes["data-listen-url"].value

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

/**
 * Update metadata which need to be updated according to divsToUpdata parameter.
 * Used by updateCardBody() function.
 * @param divsToUpdate : arry containing [node, newValueToUpdate]
 */
function updateCardInfos(divsToUpdate, thumbnailNode=null) {
    // update info
    divsToUpdate.forEach(element => {
        element[0].innerText = element[1]
        element[0].classList.remove("fade-out")
    })
    audioPlayer.flip()

    //update thumbnail if needed
    if (thumbnailNode !== null) {
        thumbnailNode.parentElement.classList.remove("fade-out")
    }
}

/**
 * Update metadata in card according to fetched data.
 */
function updateCardBody() {
    fetch(updateUrl)
        .then((response) => response.json())
        .then((data) => {

            let textsToCheck = [
                "current-station",
                "current-broadcast-title",
                "current-show-title",
                "current-broadcast-summary",
            ]

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

            divsToUpdate.forEach(element => { element[0].classList.add("fade-out") })

            // check thumbnail src
            let fetchedThumbnailSrc = data.current_thumbnail
            if (thumbnailSrc != fetchedThumbnailSrc) {
                thumbnailNode.parentElement.classList.add("fade-out")
                thumbnailNode.onload = updateCardInfos(divsToUpdate, thumbnailNode)
                setTimeout(() => {thumbnailNode.attributes.src.value = fetchedThumbnailSrc}, 200)
            } else {
                setTimeout(() => {updateCardInfos(divsToUpdate, thumbnailNode=null)}, 200)
            }
        })
}

es = new EventSource(eventsUrl)
es.onmessage = function(event) {
    if (event.data === "updated") {
        updateCardBody()
    }
}
es.onerror = err => console.log(err)

console.log("hello")
updateCardBody()

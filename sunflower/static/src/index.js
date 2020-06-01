import { CookieConsentElement } from "./elements/cookieConsent/CookieConsent";


const updateUrl = document.getElementById("info-update").attributes["data-update-url"].value
const eventsUrl = document.getElementById("info-update").attributes["data-listen-url"].value

/**
 * Class for supporting FLIP animation.
 */
class FlippedElement {


    get newY() {
        return this.element.getBoundingClientRect().y
    }

    get newX() {
        return this.element.getBoundingClientRect().x
    }

    // get newH() {
    //     return this.element.getBoundingClientRect().height
    // }

    // get newW() {
    //     return this.element.getBoundingClientRect().width
    // }


    constructor(selector) {
        this.element = document.querySelector(selector)
        this.y = this.newY
        this.x = this.newX
        // this.h = this.newH
        // this.w = this.newW
    }

    read() {
        this.x = this.newX
        this.y = this.newY
        // this.h = this.newH
        // this.w = this.newW
    }

    flip() {
        const newY = this.newY
        const newX = this.newX
        // const newH = this.newH
        // const newW = this.newW
        const deltaY = this.y - newY
        const deltaX = this.x - newX
        // const ratioH = this.w / newW
        // const ratioW = this.h / newH
        this.element.animate(
            [
                {
                    transform: `translate(${deltaX}px, ${deltaY}px)`
                },
                {
                    transform: "none"
                },
            ],
            {
                duration: Math.max(400, 3 * Math.abs(deltaY)),
                fill: "both",
                easing: "ease-in-out",
            }
        )
    }
}






/* ---------------------------- U P D A T E   C A R D   M E T A D A T A ---------------------------- */

let audioPlayer = new FlippedElement("audio")

/**
 * Update metadata which need to be updated according to divsToUpdata parameter.
 * Used by updateCardBody() function.
 * @param divsToUpdate : arry containing [node, newValueToUpdate]
 */
function updateCardInfos(divsToUpdate) {
    // update info
    audioPlayer.read()
    divsToUpdate.forEach((element, i) => {
        element[0].innerHTML = element[1]
    })
    audioPlayer.flip()

    divsToUpdate.forEach((element, i) => {
        setTimeout(() => {
            element[0].classList.remove("fade-out")
            element[0].classList.add("fade-in")
        }, 100*(i+1))
    })
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
            
            // fade out elements to update
            divsToUpdate.forEach((element, i) => { 
                if (element.innerText != "") {
                    setTimeout(() => {
                        element[0].classList.remove("fade-in")
                        element[0].classList.add("fade-out")
                    }, 100*i)
                }
            })
            
            // update divs to update and thumbnail src
            setTimeout(() => {
                document.getElementById("current-thumbnail").attributes.src.value = data.current_thumbnail
                updateCardInfos(divsToUpdate)
                if (document.getElementById("current-broadcast-summary").innerText == "") {
                    document.querySelector("body").classList.add("empty-summary")
                } else {
                    document.querySelector("body").classList.remove("empty-summary")
                }
            }, divsToUpdate.length*100 + 200)
        })
}

const es = new EventSource(eventsUrl)
es.onmessage = function(event) {
    if (event.data === "updated") {
        updateCardBody()
    }
}
es.onerror = err => console.log(err)

updateCardBody()









/* ---------------------------- T O G G L E   C H A N N E L S   M E N U ---------------------------- */

const channelsListHead = document.querySelector(".channels-list-head")
const channelsListChevron = document.querySelector(".hide-channels-list")
const channelsList = document.querySelector(".channels-list")

channelsListHead.onclick = () => { 
    channelsList.classList.add("show")
    channelsListHead.style.opacity = 0;
}
channelsListChevron.onclick = () => { 
    channelsList.classList.remove("show")
    channelsListHead.style.opacity = 1;
}












/* -------------------------------- T O G G L E   C O V E R   S I Z E -------------------------------- */

let thumbnailContainer = new FlippedElement("#current-thumbnail");
let headInfoChildren = document.querySelector("#head-info").children
let detailsChildren = document.querySelector("#details").children

document.querySelector("#current-thumbnail").onclick = () => {
    thumbnailContainer.read()

    if (window.innerWidth > 480) {
        for (let i = 0; i < headInfoChildren.length; i++) {
            setTimeout(() => {
                headInfoChildren[i].classList.remove("fade-in")
                headInfoChildren[i].classList.add("fade-out")
            }, 100*i);
        }
    }

    let detailDivsToMove = 0
    if (window.innerWidth > 720) {
        for (let i = 0; i < detailsChildren.length; i++) {
            if (detailsChildren[i].innerText == "") continue
            detailDivsToMove++
            setTimeout(() => {
                detailsChildren[i].classList.remove("fade-in")
                detailsChildren[i].classList.add("fade-out")
            }, 200 + 100*i);
        }
    }
    
    
    setTimeout(() => {
        document.querySelector("body").classList.toggle("big-cover");
        thumbnailContainer.flip()
    }, (window.innerWidth > 480 ? 400 : 0) + detailDivsToMove*100);
    
    
    for (let i = 0; i < headInfoChildren.length; i++) {
        setTimeout(() => {
            headInfoChildren[i].classList.remove("fade-out")
            headInfoChildren[i].classList.add("fade-in")
        }, 800 + 100*i + detailDivsToMove*100);
    }
    for (let i = 0; i < detailsChildren.length; i++) {
        setTimeout(() => {
            detailsChildren[i].classList.remove("fade-out")
            detailsChildren[i].classList.add("fade-in")
        }, 1000 + 100*i + detailDivsToMove*100);
    }
}


/* -------------------------------- C O O K I E   C O N S E N T -------------------------------- */


let cookieConsent = localStorage.cookieConsent
if (cookieConsent == undefined) {
    askCookieConsent()
}
function askCookieConsent() {
    document.querySelector("body").appendChild(new CookieConsentElement())
}


/* -------------------------------- R E M E M B E R   L A S T - V I S I T E D -------------------------------- */
function persistLastVisited() {
    if (cookieConsent === "true") {
        document.cookie = "lastVisitedChannel=" + window.location + ";path=/"
    }
}

persistLastVisited()

/* -------------------------------- D A R K   M O D E    -------------------------------- */

const themeSwitcher = document.querySelector(".theme-switcher");
const userTheme = localStorage.theme;

if (window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches &&  userTheme !== "light" ||
    userTheme === "dark") {
    document.body.className = "dark-mode";
    themeSwitcher.src = "/static/sun.svg";
}

themeSwitcher.onclick = () => {
    toggleDarkLight();
};

function toggleDarkLight() {
    let currentClass = document.body.className;
    document.body.className = currentClass === "dark-mode" ? "light-mode" : "dark-mode";
    themeSwitcher.src = currentClass === "dark-mode" ? "/static/moon.svg" : "/static/sun.svg";

    persistTheme(currentClass);
}

function persistTheme(currentClass) {
    if (localStorage.cookieConsent === "true") {
        localStorage.theme = currentClass === "dark-mode" ? "light" : "dark"
    }
}

const template = `<div class="container">
<p>Ce site web utilise un cookie afin de mémoriser la dernière chaîne visitée pour vous y rediriger automatiquement la prochaine fois que vous vous rendrez sur ${window.location.host}. Cliquez sur "Je refuse" pour annuler ce comportement. Votre choix est stocké sur votre navigateur et ne nous est pas communiqué.</p>
<button class="accept">J'accepte</button>
<button class="refuse">Je refuse</button>
</div>`

export class CookieConsentElement extends HTMLElement {
    constructor() {
        super()
        this.innerHTML = template
    }

    connectedCallback() {
        this.querySelector(".accept").onclick = () => {
            localStorage.cookieConsent = "true"
            this.remove()
        }
        this.querySelector(".refuse").onclick = () => {
            localStorage.cookieConsent = "false"
            this.remove()
        }
    }

    disconnectedCakllback () {
        if (localStorage.cookieConsent === "true") document.cookie = "lastVisitedChannel=" + window.location + ";path=/"
    }
}

customElements.define("sunflower-cookie-consent", CookieConsentElement)

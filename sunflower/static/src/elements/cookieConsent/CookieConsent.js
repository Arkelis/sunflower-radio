const template = `
<div class="container">
    <p>Ce site web peut mémoriser la dernière chaîne écoutée pour vous y rediriger automatiquement lors de votre prochaine visite sur ${window.location.host}. Cliquez sur "Je refuse" pour annuler ce comportement. Votre choix est stocké sur votre navigateur et ne nous est pas communiqué.</p>
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

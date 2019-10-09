var currentBroadcastCard = new Vue({
    el: '#current-broadcast-card',
    template: `
<div class="current-broadcast-card">
    <div class="card-body">
        <div v-if="thumbnailSrc" class="thumbnail">
            <img :src="thumbnailSrc" alt="Current broadcast thumbail.">
        </div>
        <div v-else class="loader">
        </div>
        <div class="broadcast-info">
            <div class="head-info">
                <div class="station">{{ station }}</div>
                <h2 class="broadcast-title">{{ cardTitle }}</h2>
            </div>
            <div class="details">
                <div v-if="showTitle" class="show-title">{{ showTitle }}</div>
                <p v-if="summary" class="broadcast-summary">{{ summary }}</p>
            </div>
        </div>
    </div>
    <div class="card-footer">
        <audio autoplay controls>
            Your browser does not support the <code>audio</code> element.
        </audio>
    </div>
</div>`,
    data: {
      thumbnailSrc: "",
      station: "",
      cardTitle: "",
      showTitle: "",
      summary: "",
      timer: null,
    },
    created() {
        fetch("http://localhost:8000/on-air")
            .then((response) => response.json())
            .then((data) => this.formatData(data))
    },
    methods: {
        formatData(data) {
            // basic data
            this.station = data.station
            this.thumbnailSrc = data.thumbnail_src
            this.summary = data.summary ? data.summary : ""
            this.showTitle = data.show_title ? data.show_title : ""
            this.end = data.end ? data.end : null

            // format card title
            if (this.station == "RTL 2") {
                if (data.type == "Musique") {
                    this.cardTitle = data.artist + " &bull; " + data.title
                } else {
                    this.cardTitle = data.type
                }
            } else if (this.station.includes("France ")) {
                if (data.diffusion_title) {
                    this.cardTitle = data.diffusion_title
                } else {
                    this.cardTitle = data.show_title
                }
            }
            this.planNextFetch()
        },
        planNextFetch() {
            if (this.end == null) {
                this.timer = setInterval(this.fetchData, 2000)
            } else {
                this.timer = setInterval(this.fetchData, this.end * 1000 - Date.now())
            }
        },
        fetchData() {
            clearInterval(this.timer)
            fetch("http://localhost:8000/on-air")
            .then((response) => response.json())
            .then((data) => this.formatData(data))
        }
    }
  })

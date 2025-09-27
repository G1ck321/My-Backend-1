const searchForm = document.getElementById("searchForm");
const artistInput = document.getElementById("artistInput");
const countrySelect = document.getElementById("countrySelect");
const statusEl = document.getElementById("status");
const resultsEl = document.getElementById("results");
const tracksEl = document.getElementById("tracks");
const resultsTitle = document.getElementById("resultsTitle");
const clearBtn = document.getElementById("clearBtn");
const searchBtn = document.getElementById("searchBtn");

function setStatus(text, isError = false) {
    statusEl.textContent = text;
    statusEl.style.color = isError ? "#ff6b6b" : "";
}

function clearResults() {
    tracksEl.innerHTML = "";
    resultsEl.classList.add("hidden");
    setStatus("Enter an artist and press Search.");
}

clearBtn.addEventListener("click", (e) => {
    e.preventDefault();
    artistInput.value = "";
    clearResults();
});

async function handleSearch(e) {
    e.preventDefault();
    const artist = artistInput.value.trim();
    const country = countrySelect.value || "US";
    if (!artist) {
        setStatus("Please enter an artist name.", true);
        return;
    }

    setStatus("Searching...", false);
    searchBtn.disabled = true;
    try {
        const resp = await fetch("/api/search-top-tracks", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ artist, country })
        });

        const data = await resp.json();

        if (!resp.ok) {
            setStatus(data.message || data.error || "Failed to fetch results", true);
            console.error("API error:", data);
            searchBtn.disabled = false;
            return;
        }

        renderTracks(data);
        setStatus(`Showing top tracks for ${data.artist}`);
    } catch (err) {
        console.error(err);
        setStatus("Network error. Check console.", true);
    } finally {
        searchBtn.disabled = false;
    }
}

function renderTracks(data) {
    tracksEl.innerHTML = "";
    resultsTitle.textContent = `Top Tracks — ${data.artist}`;
    const tracks = data.tracks || [];
    if (tracks.length === 0) {
        setStatus("No top tracks available.", true);
        resultsEl.classList.remove("hidden");
        return;
    }

    tracks.forEach((t, i) => {
        const card = document.createElement("div");
        card.className = "card";

        const thumb = document.createElement("div");
        thumb.className = "thumb";
        if (t.album_image) {
            const img = document.createElement("img");
            img.src = t.album_image;
            img.alt = `${t.album} cover`;
            thumb.appendChild(img);
        } else {
            thumb.textContent = "♪";
        }

        const meta = document.createElement("div");
        meta.className = "track-meta";
        const title = document.createElement("div");
        title.className = "track-title";
        title.textContent = `${i + 1}. ${t.name}`;
        const album = document.createElement("div");
        album.className = "track-album";
        album.textContent = t.album || "";

        meta.appendChild(title);
        meta.appendChild(album);

        const actions = document.createElement("div");
        actions.className = "track-actions";

        if (t.preview_url) {
            const previewBtn = document.createElement("button");
            previewBtn.className = "icon-btn";
            previewBtn.textContent = "Preview";
            previewBtn.addEventListener("click", () => {
                playPreview(t.preview_url, previewBtn);
            });
            actions.appendChild(previewBtn);
        } else {
            const noPreview = document.createElement("div");
            noPreview.className = "small-muted";
            noPreview.textContent = "No preview";
            actions.appendChild(noPreview);
        }

        if (t.spotify_url) {
            const openBtn = document.createElement("a");
            openBtn.className = "icon-btn";
            openBtn.textContent = "Open";
            openBtn.href = t.spotify_url;
            openBtn.target = "_blank";
            openBtn.rel = "noopener noreferrer";
            actions.appendChild(openBtn);
        }

        card.appendChild(thumb);
        card.appendChild(meta);
        card.appendChild(actions);
        tracksEl.appendChild(card);
    });

    resultsEl.classList.remove("hidden");
}

let currentAudio = null;
function playPreview(url, btn) {
    // simple toggle play/pause, ensures only one preview at a time
    if (currentAudio && currentAudio.src === url) {
        currentAudio.pause();
        currentAudio = null;
        btn.textContent = "Preview";
        return;
    }
    if (currentAudio) {
        currentAudio.pause();
        currentAudio = null;
        // reset all preview buttons text (simple approach)
        document.querySelectorAll(".icon-btn").forEach(b => {
            if (b.textContent === "Pause") b.textContent = "Preview";
        });
    }
    currentAudio = new Audio(url);
    currentAudio.play();
    btn.textContent = "Pause";
    currentAudio.onended = () => {
        btn.textContent = "Preview";
        currentAudio = null;
    };
}

searchForm.addEventListener("submit", handleSearch);

// accessibility: Enter to search while focused in input
artistInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter") handleSearch(e);
});

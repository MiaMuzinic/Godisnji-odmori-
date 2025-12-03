document.addEventListener("DOMContentLoaded", function () {

    const restoranSelect = document.getElementById("restoran");
    const pozicijaSelect = document.getElementById("pozicija");
    const weekCheckboxes = document.querySelectorAll("input[name='weeks']");

    const ROLES_BY_RESTAURANT = {
        "Kampus": ["Poslovođa", "Kuhar", "Konobar", "Pomoćni radnik", "Slastičar", "Blagajnik", "Skladištar"],
        "Index": ["Voditelj", "Poslovođa","Šef smjene", "Blagajnik", "Konobar", "Kuhar", "Pomoćni radnik"],
        "SOS": ["Voditelj", "Konobar", "Kuhar", "Pomoćni radnik"],
        "MEFST": ["Poslovođa", "Kuhar", "Pomoćni kuhar", "Konobar", "Pomoćni radnik"],
        "STOP": ["Kuhar", "Pomoćni kuhar", "Pizza majstor", "Pomoćni radnik", "Blagajnik", "Poslovođa", "Voditelj objekta"],
        "FGAG": ["Pizza majstor", "Konobar", "Pomoćni radnik"],
        "Ekonomija": ["Poslovođa", "Kuhar", "Pomoćni kuhar", "Konobar", "Pomoćni radnik"],
        "BB": ["Poslovođa", "Pizza majstor", "Kuhar", "Konobar", "Blagajnik", "Pomoćni radnik"],
        "Spinut": ["Voditelj", "Poslovođa", "Kuhar", "Blagajnik", "Konobar", "Pomoćni radnik"]
    };

    let globalStatus = {};
    let limitMap = {};

    // --- 1) UČITAJ STVARNE LIMITE IZ BACKENDA ---
    async function fetchLimits() {
        const res = await fetch("/limits");
        limitMap = await res.json();
    }

    // --- 2) UČITAJ POPUNJENOST ---
    async function fetchStatus() {
    const res = await fetch("/status_all");
    globalStatus = await res.json();
    enforceLimit();
}


    restoranSelect.addEventListener("change", function () {
        const restoran = restoranSelect.value;

        pozicijaSelect.innerHTML = `<option value="">-- Odaberi poziciju --</option>`;

        if (restoran) {
            ROLES_BY_RESTAURANT[restoran].forEach(role => {
                const option = document.createElement("option");
                option.value = role;
                option.textContent = role;
                pozicijaSelect.appendChild(option);
            });
        }

        resetCheckboxes();
        enforceLimit();
    });

    pozicijaSelect.addEventListener("change", enforceLimit);

    function resetCheckboxes() {
        weekCheckboxes.forEach(cb => {
            cb.checked = false;
            cb.disabled = false;
            cb.parentElement.style.opacity = 1;
        });
    }

    // --- 3) PRAVILNA LOGIKA DISABLE-A ---
    function enforceLimit() {
        const restoran = restoranSelect.value;
        const pozicija = pozicijaSelect.value;

        weekCheckboxes.forEach(cb => {
            cb.disabled = false;
            cb.parentElement.style.opacity = 1;
        });

        if (!restoran || !pozicija) return;

        const realLimit = limitMap[restoran][pozicija];

        weekCheckboxes.forEach(cb => {
            const week = cb.value;
            const filled = globalStatus[restoran]?.[pozicija]?.[week] || 0;

            if (filled >= realLimit) {
                cb.disabled = true;
                cb.parentElement.style.opacity = 0.5;
            }
        });
    }

    weekCheckboxes.forEach(cb =>
        cb.addEventListener("change", enforceLimit)
    );

    // 🔥 prvo učitaj limite, onda status
    fetchLimits().then(fetchStatus);
});


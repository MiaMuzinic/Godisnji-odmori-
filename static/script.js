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

    const DEFAULT_LIMITS = {
        "Kuhar": 1,
        "Pomoćni radnik": 2,
        "Spremačica": 3,
        "Recepcija": 1
    };

    let globalStatus = {};

    async function fetchStatus() {
        const res = await fetch("/status");
        globalStatus = await res.json();
        enforceLimit();
    }

    restoranSelect.addEventListener("change", function () {
        const restoran = restoranSelect.value;

        // reset pozicija
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

    function enforceLimit() {
        const restoran = restoranSelect.value;
        const pozicija = pozicijaSelect.value;

        weekCheckboxes.forEach(cb => {
            cb.disabled = false;
            cb.parentElement.style.opacity = 1;
        });

        if (!restoran || !pozicija) return;

        weekCheckboxes.forEach(cb => {
            const week = cb.value;
            const limit = DEFAULT_LIMITS[pozicija] || 1;

            const count =
                globalStatus[restoran]?.[pozicija]?.[week] || 0;

            if (count >= limit) {
                cb.disabled = true;
                cb.parentElement.style.opacity = 0.5;
            }
        });
    }

    weekCheckboxes.forEach(cb =>
        cb.addEventListener("change", enforceLimit)
    );

    fetchStatus();
});

/* main.js — live search & filter for F1 Driver Database */

function filterDrivers() {
  const q    = document.getElementById("search").value.toLowerCase().trim();
  const nat  = document.getElementById("natFilter").value.toLowerCase();
  const team = document.getElementById("teamFilter").value.toLowerCase();

  const rows = document.querySelectorAll("#tbody tr");
  let visible = 0;

  rows.forEach(row => {
    const name    = row.dataset.name    || "";
    const natData = row.dataset.nat     || "";
    const teamData= row.dataset.team    || "";

    const show = (!q    || name.includes(q))
              && (!nat  || natData.includes(nat))
              && (!team || teamData.includes(team));

    row.style.display = show ? "" : "none";
    if (show) {
      visible++;
      const idx = row.querySelector(".idx");
      if (idx) idx.textContent = visible;
    }
  });

  const badge = document.getElementById("result-count");
  if (badge) badge.textContent = `${visible} result${visible !== 1 ? "s" : ""}`;
}

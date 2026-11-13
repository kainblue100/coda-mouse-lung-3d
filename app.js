async function loadStats() {
  const el = document.getElementById("stats");
  if (!el) return;
  try {
    const res = await fetch("assets/class_stats.csv", { cache: "no-store" });
    if (!res.ok) return;
    const text = await res.text();
    const rows = text.trim().split(/\r?\n/).slice(1).map((line) => line.split(","));
    if (!rows.length) return;
    const table = document.createElement("table");
    table.innerHTML =
      "<thead><tr><th>Class</th><th>Name</th><th>Voxels</th><th>Volume (mm³)</th></tr></thead>" +
      "<tbody>" +
      rows
        .map(
          ([c, name, vox, mm3]) =>
            `<tr><td>${c}</td><td>${name}</td><td>${Number(vox).toLocaleString()}</td><td>${mm3}</td></tr>`
        )
        .join("") +
      "</tbody>";
    el.innerHTML = "";
    el.appendChild(table);
  } catch (_) {
    /* assets appear after pipeline finishes */
  }
}

loadStats();

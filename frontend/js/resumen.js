(function () {
  if (!iniciarPantalla(["coordinacion"])) return;
  const cont = document.getElementById("contenido");
  function tarjetaNumero(valor, etiqueta) {
    const t = el("div", { class: "tarjeta" });
    t.appendChild(el("div", { class: "valor" }, String(valor))); t.appendChild(el("div", { class: "etiqueta" }, etiqueta));
    return t;
  }
  function tablaSimple(titulo, columnas, filas) {
    const t = el("div", { class: "tarjeta" }); t.appendChild(el("h2", {}, titulo));
    if (!filas.length) { t.appendChild(el("p", { class: "vacio" }, "Sin datos.")); return t; }
    const tabla = el("table"), cab = el("tr");
    for (const c of columnas) cab.appendChild(el("th", {}, c));
    tabla.appendChild(el("thead")).appendChild(cab);
    const cuerpo = el("tbody");
    for (const f of filas) { const tr = el("tr"); for (const c of f) { const td = el("td"); if (c instanceof Node) td.appendChild(c); else td.textContent = c; tr.appendChild(td); } cuerpo.appendChild(tr); }
    tabla.appendChild(cuerpo); t.appendChild(tabla); return t;
  }
  async function cargar() {
    ocultarMensaje();
    const q = new URLSearchParams();
    const d = document.getElementById("desde").value, h = document.getElementById("hasta").value;
    if (d) q.set("desde", d); if (h) q.set("hasta", h);
    try {
      const r = await api("/api/resumen" + (q.toString() ? "?" + q : ""));
      vaciar(cont);
      const nums = el("div", { class: "numeros" });
      nums.appendChild(tarjetaNumero(r.total, "Solicitudes en total"));
      nums.appendChild(tarjetaNumero(r.por_estado.finalizada, "Finalizadas"));
      nums.appendChild(tarjetaNumero(r.tiempo_promedio_atencion_dias === null ? "—" : r.tiempo_promedio_atencion_dias + " días", "Tiempo promedio de atención"));
      cont.appendChild(nums);
      const max = Math.max(1, ...Object.values(r.por_estado));
      cont.appendChild(tablaSimple("Solicitudes por estado", ["Estado", "Total", ""],
        Object.entries(r.por_estado).map(([k, v]) => {
          const barra = el("div", { class: "barra-datos" }); const s = el("span"); s.style.width = (100 * v / max) + "%"; barra.appendChild(s);
          return [insignia(k, ESTADOS[k]), String(v), barra];
        })));
      cont.appendChild(tablaSimple("Por servicio", ["Servicio", "Total"], r.por_servicio.map((x) => [x.servicio, String(x.total)])));
      cont.appendChild(tablaSimple("Por responsable", ["Responsable", "Total"], r.por_responsable.map((x) => [x.responsable, String(x.total)])));
      cont.appendChild(tablaSimple("Pendientes más antiguas", ["Radicado", "Asunto", "Estado", "Responsable", "Días pendientes"],
        r.pendientes_mas_antiguas.map((x) => {
          const a = el("a", { href: "solicitud.html?id=" + x.id }, x.radicado);
          return [a, x.asunto, insignia(x.estado, ESTADOS[x.estado]), x.responsable || "Sin asignar", String(x.dias_pendientes)];
        })));
    } catch (err) { mostrarMensaje("error", err.message); }
  }
  document.getElementById("aplicar").addEventListener("click", cargar);
  cargar();
})();

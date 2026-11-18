(function () {
  const usuario = iniciarPantalla(["atencion", "coordinacion"]); if (!usuario) return;
  const LIMITE = 10; let desplazamiento = 0, total = 0;
  const fe = document.getElementById("f-estado"), fp = document.getElementById("f-prioridad"),
        fs = document.getElementById("f-servicio"), fm = document.getElementById("f-mias");
  for (const [k, v] of Object.entries(ESTADOS)) fe.appendChild(el("option", { value: k }, v));
  async function cargar() {
    ocultarMensaje();
    const q = new URLSearchParams({ limite: LIMITE, desplazamiento });
    if (fe.value) q.set("estado", fe.value);
    if (fp.value) q.set("prioridad", fp.value);
    if (fs.value) q.set("servicio_id", fs.value);
    if (fm.value === "mias") q.set("responsable_id", usuario.id);
    try {
      const datos = await api("/api/solicitudes?" + q);
      total = datos.total;
      const lista = document.getElementById("lista"); vaciar(lista);
      lista.appendChild(tablaSolicitudes(datos.items, true));
      const ult = Math.min(desplazamiento + LIMITE, total);
      document.getElementById("pagina").textContent = total ? (desplazamiento + 1) + "–" + ult + " de " + total : "";
      document.getElementById("anterior").disabled = desplazamiento === 0;
      document.getElementById("siguiente").disabled = desplazamiento + LIMITE >= total;
    } catch (err) { mostrarMensaje("error", err.message); }
  }
  for (const f of [fe, fp, fs, fm]) f.addEventListener("change", () => { desplazamiento = 0; cargar(); });
  document.getElementById("anterior").addEventListener("click", () => { desplazamiento = Math.max(0, desplazamiento - LIMITE); cargar(); });
  document.getElementById("siguiente").addEventListener("click", () => { desplazamiento += LIMITE; cargar(); });
  api("/api/servicios").then((servicios) => {
    for (const s of servicios) fs.appendChild(el("option", { value: s.id }, s.nombre));
  }).catch(() => {});
  cargar().then(() => { if (new URLSearchParams(window.location.search).get("aviso")) mostrarMensaje("ok", "Acción registrada. La solicitud quedó asignada a otra persona y ya no aparece en tu bandeja."); });
})();

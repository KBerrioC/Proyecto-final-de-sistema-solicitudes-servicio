(function () {
  if (!iniciarPantalla(["solicitante"])) return;
  const select = document.getElementById("servicio"), ayuda = document.getElementById("ayuda-servicio");
  let servicios = [];
  function actualizarAyuda() {
    const s = servicios.find((x) => String(x.id) === select.value);
    ayuda.textContent = s ? s.descripcion + (s.requiere_adjunto ? " Este servicio exige adjuntar al menos un documento." : "") : "";
  }
  api("/api/servicios").then((lista) => {
    servicios = lista;
    for (const s of lista) select.appendChild(el("option", { value: s.id }, s.nombre));
    actualizarAyuda();
  }).catch((err) => mostrarMensaje("error", err.message));
  select.addEventListener("change", actualizarAyuda);

  document.getElementById("form-nueva").addEventListener("submit", async (e) => {
    e.preventDefault(); ocultarMensaje();
    const archivos = Array.from(document.getElementById("archivos").files);
    const s = servicios.find((x) => String(x.id) === select.value);
    if (s && s.requiere_adjunto && !archivos.length) return mostrarMensaje("error", "Este servicio requiere al menos un documento adjunto");
    const problema = validarArchivos(archivos);
    if (problema) return mostrarMensaje("error", problema);
    const datos = new FormData();
    datos.append("servicio_id", select.value);
    datos.append("asunto", document.getElementById("asunto").value.trim());
    datos.append("descripcion", document.getElementById("descripcion").value.trim());
    for (const f of archivos) datos.append("archivos", f);
    const boton = document.getElementById("enviar"); boton.disabled = true;
    try {
      const creada = await api("/api/solicitudes", { method: "POST", form: datos });
      window.location.href = "solicitud.html?id=" + creada.id + "&nueva=1";
    } catch (err) { mostrarMensaje("error", err.message); boton.disabled = false; }
  });
})();

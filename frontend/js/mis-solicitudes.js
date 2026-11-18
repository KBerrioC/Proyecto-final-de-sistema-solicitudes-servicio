(function () {
  if (!iniciarPantalla(["solicitante"])) return;
  const LIMITE = 10; let desplazamiento = 0, total = 0;
  const filtro = document.getElementById("f-estado");
  for (const [k, v] of Object.entries(ESTADOS)) filtro.appendChild(el("option", { value: k }, v));
  async function cargar() {
    ocultarMensaje();
    const q = new URLSearchParams({ limite: LIMITE, desplazamiento });
    if (filtro.value) q.set("estado", filtro.value);
    try {
      const datos = await api("/api/solicitudes?" + q);
      total = datos.total;
      const lista = document.getElementById("lista"); vaciar(lista);
      lista.appendChild(tablaSolicitudes(datos.items, false));
      const ult = Math.min(desplazamiento + LIMITE, total);
      document.getElementById("pagina").textContent = total ? (desplazamiento + 1) + "–" + ult + " de " + total : "";
      document.getElementById("anterior").disabled = desplazamiento === 0;
      document.getElementById("siguiente").disabled = desplazamiento + LIMITE >= total;
    } catch (err) { mostrarMensaje("error", err.message); }
  }
  filtro.addEventListener("change", () => { desplazamiento = 0; cargar(); });
  document.getElementById("anterior").addEventListener("click", () => { desplazamiento = Math.max(0, desplazamiento - LIMITE); cargar(); });
  document.getElementById("siguiente").addEventListener("click", () => { desplazamiento += LIMITE; cargar(); });
  cargar();
})();

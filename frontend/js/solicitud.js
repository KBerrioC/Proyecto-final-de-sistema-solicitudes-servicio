(function () {
  const usuario = iniciarPantalla(); if (!usuario) return;
  const id = new URLSearchParams(window.location.search).get("id");
  const cont = document.getElementById("contenido");
  document.getElementById("volver").addEventListener("click", (e) => { e.preventDefault(); window.location.href = inicioPara(usuario.rol); });
  if (!id || !/^\d+$/.test(id)) { mostrarMensaje("error", "Solicitud no indicada"); return; }
  const esPersonal = usuario.rol !== "solicitante";
  let personalAtencion = null;

  function dato(lista, titulo, valor) {
    const par = el("div"); par.appendChild(el("dt", {}, titulo));
    const dd = el("dd"); if (valor instanceof Node) dd.appendChild(valor); else dd.textContent = valor;
    par.appendChild(dd); lista.appendChild(par);
  }
  // Construye un formulario de acción. campos: [{id, etiqueta, tipo, opciones, requerido, ...}]
  let contadorFormularios = 0;
  function formulario(titulo, campos, textoBoton, alEnviar, clase = "") {
    const prefijo = "f" + (++contadorFormularios);
    const f = el("form"); f.appendChild(el("h2", {}, titulo));
    for (const c of campos) {
      const inputId = "campo-" + prefijo + "-" + c.id;
      if (c.tipo === "checkbox") {
        const l = el("label"); const i = el("input", { type: "checkbox", id: inputId }); l.appendChild(i); l.appendChild(document.createTextNode(" " + c.etiqueta)); f.appendChild(l); continue;
      }
      f.appendChild(el("label", { for: inputId }, c.etiqueta));
      let campo;
      if (c.tipo === "select") { campo = el("select", { id: inputId }); for (const [v, t] of c.opciones) campo.appendChild(el("option", { value: v }, t)); }
      else if (c.tipo === "textarea") campo = el("textarea", { id: inputId, maxlength: c.max || 1000 });
      else if (c.tipo === "file") { campo = el("input", { type: "file", id: inputId, accept: ".pdf,.jpg,.jpeg,.png" }); if (c.multiple) campo.multiple = true; }
      else campo = el("input", { type: "text", id: inputId });
      if (c.requerido) campo.required = true;
      f.appendChild(campo);
    }
    const b = el("button", { type: "submit", class: "btn " + clase }, textoBoton); f.appendChild(b);
    f.addEventListener("submit", async (e) => {
      e.preventDefault(); ocultarMensaje(); b.disabled = true;
      const valores = {};
      for (const c of campos) {
        const campo = f.querySelector("#campo-" + prefijo + "-" + c.id);
        valores[c.id] = c.tipo === "checkbox" ? campo.checked : c.tipo === "file" ? Array.from(campo.files) : campo.value.trim();
      }
      try { await alEnviar(valores); await cargar("Acción registrada correctamente"); }
      catch (err) { mostrarMensaje("error", err.message); b.disabled = false; }
    });
    return f;
  }
  const json = (ruta, metodo, cuerpo) => api(ruta, { method: metodo, json: cuerpo });

  function acciones(s) {
    const caja = el("div", { class: "acciones" });
    const base = "/api/solicitudes/" + s.id;
    const esResponsable = s.responsable && s.responsable.id === usuario.id;
    const sel = (lista) => lista.map((p) => [String(p.id), p.nombre]);
    const prioridades = [["alta", "Alta"], ["media", "Media"], ["baja", "Baja"]];
    if (usuario.rol === "solicitante") {
      if (s.estado === "pendiente_informacion") {
        caja.appendChild(formulario("Responder la petición de información", [
          { id: "texto", etiqueta: "Respuesta", tipo: "textarea", max: 2000 },
          { id: "archivos", etiqueta: "Documentos", tipo: "file", multiple: true }], "Enviar información", async (v) => {
            if (!v.texto && !v.archivos.length) throw new Error("Escriba una respuesta o adjunte un archivo");
            const problema = validarArchivos(v.archivos); if (problema) throw new Error(problema);
            const d = new FormData(); if (v.texto) d.append("texto", v.texto); for (const f of v.archivos) d.append("archivos", f);
            await api(base + "/informacion", { method: "POST", form: d });
          }));
      }
      if (["recibida", "en_evaluacion", "pendiente_informacion"].includes(s.estado)) {
        caja.appendChild(formulario("Cancelar la solicitud", [{ id: "motivo", etiqueta: "Motivo (opcional)", tipo: "textarea" }],
          "Cancelar solicitud", (v) => json(base + "/cancelacion", "POST", v.motivo ? { motivo: v.motivo } : {}), "peligro"));
      }
      return caja;
    }
    if (s.estado === "recibida") {
      caja.appendChild(formulario("Iniciar la evaluación", [], "Iniciar evaluación", () => json(base + "/estado", "PATCH", { estado: "en_evaluacion" })));
    }
    if (s.estado === "en_evaluacion") {
      caja.appendChild(formulario("Aceptar y asignar", [
        { id: "responsable", etiqueta: "Responsable", tipo: "select", opciones: sel(personalAtencion), requerido: true },
        { id: "prioridad", etiqueta: "Prioridad", tipo: "select", opciones: prioridades },
        { id: "motivo", etiqueta: "Motivo del cambio de prioridad (opcional)", tipo: "textarea" }], "Aceptar y asignar", (v) =>
          json(base + "/estado", "PATCH", { estado: "en_gestion", responsable_id: Number(v.responsable), prioridad: v.prioridad, motivo: v.motivo || null })));
      caja.appendChild(formulario("Solicitar información", [{ id: "motivo", etiqueta: "¿Qué información necesita?", tipo: "textarea", requerido: true }],
        "Solicitar información", (v) => json(base + "/estado", "PATCH", { estado: "pendiente_informacion", motivo: v.motivo })));
      caja.appendChild(formulario("Rechazar", [{ id: "motivo", etiqueta: "Motivo del rechazo", tipo: "textarea", requerido: true }],
        "Rechazar solicitud", (v) => json(base + "/estado", "PATCH", { estado: "rechazada", motivo: v.motivo }), "peligro"));
    }
    const puedeGestionar = usuario.rol === "coordinacion" || esResponsable;
    if (puedeGestionar && !["finalizada", "rechazada", "cancelada"].includes(s.estado)) {
      caja.appendChild(formulario("Registrar una nota", [
        { id: "texto", etiqueta: "Nota", tipo: "textarea", requerido: true },
        { id: "visible", etiqueta: "Visible para el solicitante", tipo: "checkbox" }], "Guardar nota",
        (v) => json(base + "/notas", "POST", { texto: v.texto, visible_solicitante: v.visible })));
      caja.appendChild(formulario("Ajustar la prioridad", [
        { id: "prioridad", etiqueta: "Nueva prioridad", tipo: "select", opciones: prioridades },
        { id: "motivo", etiqueta: "Motivo", tipo: "textarea", requerido: true }], "Cambiar prioridad",
        (v) => json(base + "/prioridad", "PATCH", { prioridad: v.prioridad, motivo: v.motivo }), "secundario"));
    }
    if (puedeGestionar && s.estado === "en_gestion") {
      caja.appendChild(formulario("Reasignar el responsable", [
        { id: "responsable", etiqueta: "Nuevo responsable", tipo: "select", opciones: sel(personalAtencion), requerido: true },
        { id: "motivo", etiqueta: "Motivo (opcional)", tipo: "textarea" }], "Reasignar",
        (v) => json(base + "/responsable", "PATCH", { responsable_id: Number(v.responsable), motivo: v.motivo || null }), "secundario"));
      caja.appendChild(formulario("Finalizar con una respuesta", [
        { id: "respuesta", etiqueta: "Respuesta para el solicitante (10 a 2000 caracteres)", tipo: "textarea", requerido: true, max: 2000 },
        { id: "archivo", etiqueta: "Archivo de respuesta (opcional)", tipo: "file" }], "Finalizar solicitud", async (v) => {
          const problema = validarArchivos(v.archivo); if (problema) throw new Error(problema);
          const d = new FormData(); d.append("respuesta", v.respuesta); if (v.archivo[0]) d.append("archivo", v.archivo[0]);
          await api(base + "/finalizacion", { method: "POST", form: d });
        }));
    }
    return caja;
  }

  async function cargar(mensajeOk) {
    try {
      const [s, eventos] = await Promise.all([api("/api/solicitudes/" + id), api("/api/solicitudes/" + id + "/eventos")]);
      if (esPersonal && personalAtencion === null) personalAtencion = await api("/api/usuarios/atencion");
      vaciar(cont);
      cont.appendChild(el("h1", {}, s.radicado + " · " + s.asunto));
      const t = el("div", { class: "tarjeta" }); const dl = el("dl", { class: "rejilla" });
      dato(dl, "Estado", insignia(s.estado, ESTADOS[s.estado])); dato(dl, "Prioridad", insignia(s.prioridad, PRIORIDADES[s.prioridad]));
      dato(dl, "Servicio", s.servicio.nombre); dato(dl, "Solicitante", s.solicitante.nombre);
      dato(dl, "Responsable", s.responsable ? s.responsable.nombre : "Sin asignar"); dato(dl, "Creada", fecha(s.creado_en));
      dato(dl, "Tiempo", s.dias_pendientes !== null ? s.dias_pendientes + " día(s) pendiente" : s.dias_atencion + " día(s) de atención");
      t.appendChild(dl); t.appendChild(el("h2", {}, "Descripción")); t.appendChild(el("p", {}, s.descripcion));
      cont.appendChild(t);
      if (s.respuesta) { const r = el("div", { class: "tarjeta" }); r.appendChild(el("h2", {}, "Respuesta")); r.appendChild(el("p", {}, s.respuesta)); cont.appendChild(r); }
      if (s.adjuntos.length) {
        const a = el("div", { class: "tarjeta" }); a.appendChild(el("h2", {}, "Documentos"));
        const ul = el("ul");
        for (const adj of s.adjuntos) {
          const li = el("li"); const b = el("button", { type: "button", class: "btn secundario" }, "Descargar " + adj.nombre_original);
          b.style.marginTop = "0"; b.addEventListener("click", () => descargar(adj).catch((err) => mostrarMensaje("error", err.message)));
          li.appendChild(b); li.appendChild(el("span", { class: "ayuda" }, " " + ({ solicitud: "adjunto de la solicitud", informacion: "información entregada", respuesta: "archivo de respuesta" })[adj.proposito] + " · " + Math.ceil(adj.tamano_bytes / 1024) + " KB"));
          ul.appendChild(li);
        }
        a.appendChild(ul); cont.appendChild(a);
      }
      const acc = acciones(s);
      if (acc.children.length) { const w = el("div", { class: "tarjeta" }); w.appendChild(el("h2", {}, "Acciones")); w.appendChild(acc); cont.appendChild(w); }
      const h = el("div", { class: "tarjeta" }); h.appendChild(el("h2", {}, "Historial")); const ul = el("ul", { class: "linea-tiempo" });
      for (const e of eventos) {
        const li = el("li"); li.appendChild(el("strong", {}, EVENTOS[e.tipo] || e.tipo));
        if (e.estado_nuevo) li.appendChild(document.createTextNode(" → " + ESTADOS[e.estado_nuevo]));
        if (esPersonal && e.visible_solicitante === false) li.appendChild(el("span", { class: "interna" }, "  (interno)"));
        li.appendChild(el("div", { class: "meta" }, e.autor.nombre + " · " + fecha(e.creado_en)));
        if (e.detalle) li.appendChild(el("div", {}, e.detalle));
        ul.appendChild(li);
      }
      h.appendChild(ul); cont.appendChild(h);
      if (mensajeOk) mostrarMensaje("ok", mensajeOk);
      else if (new URLSearchParams(window.location.search).get("nueva")) mostrarMensaje("ok", "Solicitud registrada con el radicado " + s.radicado);
    } catch (err) {
      // Tras asignar a otra persona, la solicitud en gestión deja de ser visible para quien la asignó (SUP-10).
      if (mensajeOk && esPersonal) { window.location.href = "bandeja.html?aviso=1"; return; }
      vaciar(cont); mostrarMensaje("error", err.message);
    }
  }
  cargar();
})();

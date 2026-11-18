// Cliente de la API: token de sesión, manejo de errores y utilidades de interfaz.
// Todo el texto del usuario se inserta con textContent, nunca con innerHTML (diseno.md, sección 2.3).
const ESTADOS = {
  recibida: "Recibida", en_evaluacion: "En evaluación", pendiente_informacion: "Pendiente de información",
  en_gestion: "En gestión", finalizada: "Finalizada", rechazada: "Rechazada", cancelada: "Cancelada",
};
const PRIORIDADES = { alta: "Alta", media: "Media", baja: "Baja" };
const ROLES = { solicitante: "Solicitante", atencion: "Personal de atención", coordinacion: "Coordinación" };
const EVENTOS = {
  creada: "Solicitud creada", evaluacion_iniciada: "Evaluación iniciada", informacion_solicitada: "Información solicitada",
  informacion_recibida: "Información recibida", aceptada: "Solicitud aceptada", rechazada: "Solicitud rechazada",
  asignada: "Responsable asignado", reasignada: "Responsable reasignado", prioridad_cambiada: "Prioridad cambiada",
  nota: "Nota", finalizada: "Solicitud finalizada", cancelada: "Solicitud cancelada",
};

function el(etiqueta, atributos = {}, texto = "") {
  const nodo = document.createElement(etiqueta);
  for (const [k, v] of Object.entries(atributos)) {
    if (k === "class") nodo.className = v; else nodo.setAttribute(k, v);
  }
  if (texto !== "") nodo.textContent = texto;
  return nodo;
}
function vaciar(nodo) { while (nodo.firstChild) nodo.removeChild(nodo.firstChild); }
function insignia(clase, texto) { return el("span", { class: "badge " + clase }, texto); }
function fecha(iso) {
  if (!iso) return "—";
  return new Date(iso + (iso.endsWith("Z") ? "" : "Z")).toLocaleString("es-CO", { dateStyle: "medium", timeStyle: "short" });
}

const sesion = {
  token: () => sessionStorage.getItem("token"),
  usuario: () => { try { return JSON.parse(sessionStorage.getItem("usuario")); } catch { return null; } },
  guardar(token, usuario) { sessionStorage.setItem("token", token); sessionStorage.setItem("usuario", JSON.stringify(usuario)); },
  cerrar() { sessionStorage.clear(); window.location.href = "index.html"; },
};
function inicioPara(rol) {
  return { solicitante: "mis-solicitudes.html", atencion: "bandeja.html", coordinacion: "resumen.html" }[rol] || "index.html";
}

function mensajeDeError(cuerpo, estado) {
  const d = cuerpo && cuerpo.detail;
  if (typeof d === "string") return d;
  if (Array.isArray(d)) return d.map((e) => (e.loc ? e.loc.slice(1).join(".") + ": " : "") + e.msg).join(" · ");
  return "Error " + estado;
}

// opciones: { method, json, form (FormData o URLSearchParams), blob }
async function api(ruta, opciones = {}) {
  const cabeceras = {};
  const token = sesion.token();
  if (token) cabeceras["Authorization"] = "Bearer " + token;
  let cuerpo;
  if (opciones.json !== undefined) { cabeceras["Content-Type"] = "application/json"; cuerpo = JSON.stringify(opciones.json); }
  else if (opciones.form) cuerpo = opciones.form;
  let respuesta;
  try {
    respuesta = await fetch(ruta, { method: opciones.method || "GET", headers: cabeceras, body: cuerpo });
  } catch {
    throw new Error("No se pudo conectar con el servidor");
  }
  if (respuesta.status === 401 && !opciones.sinRedireccion) { sesion.cerrar(); throw new Error("Sesión vencida"); }
  if (opciones.blob && respuesta.ok) return respuesta;
  let datos = null;
  try { datos = await respuesta.json(); } catch { /* sin cuerpo */ }
  if (!respuesta.ok) throw new Error(mensajeDeError(datos, respuesta.status));
  return datos;
}

function mostrarMensaje(tipo, texto, id = "mensaje") {
  const caja = document.getElementById(id);
  if (!caja) return;
  caja.className = "msg visible " + tipo;
  caja.textContent = texto;
  caja.scrollIntoView({ block: "nearest" });
}
function ocultarMensaje(id = "mensaje") {
  const caja = document.getElementById(id);
  if (caja) { caja.className = "msg"; caja.textContent = ""; }
}

// Comprueba sesión y rol; dibuja la barra superior. Devuelve el usuario o null si redirige.
function iniciarPantalla(rolesPermitidos) {
  const usuario = sesion.usuario();
  if (!sesion.token() || !usuario) { window.location.href = "index.html"; return null; }
  if (rolesPermitidos && !rolesPermitidos.includes(usuario.rol)) { window.location.href = inicioPara(usuario.rol); return null; }
  const barra = el("header", { class: "barra" });
  barra.appendChild(el("span", { class: "marca" }, "Solicitudes de servicio"));
  const enlaces = usuario.rol === "solicitante"
    ? [["mis-solicitudes.html", "Mis solicitudes"], ["nueva-solicitud.html", "Nueva solicitud"]]
    : usuario.rol === "atencion" ? [["bandeja.html", "Bandeja"]]
    : [["resumen.html", "Resumen"], ["bandeja.html", "Bandeja"]];
  for (const [href, texto] of enlaces) barra.appendChild(el("a", { href }, texto));
  barra.appendChild(el("span", { class: "usuario" }, usuario.nombre + " · " + ROLES[usuario.rol]));
  const salir = el("button", { type: "button" }, "Cerrar sesión");
  salir.addEventListener("click", () => sesion.cerrar());
  barra.appendChild(salir);
  document.body.insertBefore(barra, document.body.firstChild);
  return usuario;
}

function validarArchivos(lista) {
  if (lista.length > 5) return "Se permiten como máximo 5 archivos";
  for (const f of lista) {
    if (!/\.(pdf|jpe?g|png)$/i.test(f.name)) return "«" + f.name + "» no es PDF, JPG ni PNG";
    if (f.size === 0) return "«" + f.name + "» está vacío";
    if (f.size > 5 * 1024 * 1024) return "«" + f.name + "» supera los 5 MB";
  }
  return null;
}

async function descargar(adjunto) {
  const r = await api("/api/adjuntos/" + adjunto.id, { blob: true });
  const url = URL.createObjectURL(await r.blob());
  const a = el("a", { href: url, download: adjunto.nombre_original });
  document.body.appendChild(a); a.click(); a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 5000);
}

function tablaSolicitudes(solicitudes, conSolicitante) {
  const wrap = el("div", { class: "tabla-wrap" });
  if (!solicitudes.length) { wrap.appendChild(el("p", { class: "vacio" }, "No hay solicitudes para mostrar.")); return wrap; }
  const tabla = el("table"), cab = el("tr");
  const cols = ["Radicado", "Asunto", "Servicio"].concat(conSolicitante ? ["Solicitante"] : [])
    .concat(["Estado", "Prioridad", "Responsable", "Días pendientes", "Creada"]);
  for (const c of cols) cab.appendChild(el("th", {}, c));
  tabla.appendChild(el("thead")).appendChild(cab);
  const cuerpo = el("tbody");
  for (const s of solicitudes) {
    const fila = el("tr");
    const celdaRad = el("td"); celdaRad.appendChild(el("a", { href: "solicitud.html?id=" + s.id }, s.radicado));
    fila.appendChild(celdaRad);
    fila.appendChild(el("td", {}, s.asunto));
    fila.appendChild(el("td", {}, s.servicio.nombre));
    if (conSolicitante) fila.appendChild(el("td", {}, s.solicitante ? s.solicitante.nombre : ""));
    const e = el("td"); e.appendChild(insignia(s.estado, ESTADOS[s.estado])); fila.appendChild(e);
    const p = el("td"); p.appendChild(insignia(s.prioridad, PRIORIDADES[s.prioridad])); fila.appendChild(p);
    fila.appendChild(el("td", {}, s.responsable ? s.responsable.nombre : "Sin asignar"));
    fila.appendChild(el("td", {}, s.dias_pendientes === null ? "—" : String(s.dias_pendientes)));
    fila.appendChild(el("td", {}, fecha(s.creado_en)));
    cuerpo.appendChild(fila);
  }
  tabla.appendChild(cuerpo); wrap.appendChild(tabla);
  return wrap;
}

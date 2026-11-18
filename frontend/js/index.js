(function () {
  const usuario = sesion.usuario();
  if (sesion.token() && usuario) { window.location.href = inicioPara(usuario.rol); return; }
  const fl = document.getElementById("form-login"), fr = document.getElementById("form-registro");
  const tl = document.getElementById("tab-login"), tr = document.getElementById("tab-registro");
  function pestana(login) {
    fl.hidden = !login; fr.hidden = login; ocultarMensaje();
    tl.className = "btn" + (login ? "" : " secundario"); tr.className = "btn" + (login ? " secundario" : "");
  }
  tl.addEventListener("click", () => pestana(true));
  tr.addEventListener("click", () => pestana(false));

  async function ingresar(correo, password) {
    const form = new URLSearchParams({ username: correo, password });
    const datos = await api("/api/auth/login", { method: "POST", form, sinRedireccion: true });
    sesion.guardar(datos.access_token, datos.usuario);
    window.location.href = inicioPara(datos.usuario.rol);
  }
  fl.addEventListener("submit", async (e) => {
    e.preventDefault(); ocultarMensaje();
    try { await ingresar(document.getElementById("login-correo").value.trim(), document.getElementById("login-password").value); }
    catch (err) { mostrarMensaje("error", err.message); }
  });
  fr.addEventListener("submit", async (e) => {
    e.preventDefault(); ocultarMensaje();
    const correo = document.getElementById("reg-correo").value.trim(), password = document.getElementById("reg-password").value;
    try {
      await api("/api/auth/registro", { method: "POST", sinRedireccion: true, json: {
        nombre: document.getElementById("reg-nombre").value.trim(), correo, password,
        tipo_solicitante: document.getElementById("reg-tipo").value } });
      await ingresar(correo, password);
    } catch (err) { mostrarMensaje("error", err.message); }
  });
})();

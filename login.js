const params = new URLSearchParams(window.location.search);
if (params.get("error")) {
  const el = document.getElementById("login-error");
  if (el) el.style.display = "block";
}

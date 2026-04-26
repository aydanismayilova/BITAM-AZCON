async function login() {
  const username = document.getElementById("username").value.trim();
  const password = document.getElementById("password").value;
  const msg = document.getElementById("loginMsg");
  msg.textContent = "Signing in...";

  try {
    const res = await fetch("/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password }),
    });
    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.detail || "Login failed");
    }

    localStorage.setItem("azcon_user", JSON.stringify(data));
    window.location.href = "/app";
  } catch (err) {
    msg.textContent = `Login failed: ${String(err.message || err)}`;
  }
}

async function loadCompanies() {
  const res = await fetch("/companies-public");
  const companies = await res.json();
  const select = document.getElementById("regCompany");
  select.innerHTML = companies.map((c) => `<option value="${c.name}">${c.name}</option>`).join("");
}

async function registerRequest() {
  const msg = document.getElementById("regMsg");
  msg.textContent = "Submitting request...";
  try {
    const payload = {
      full_name: document.getElementById("regFullName").value.trim(),
      username: document.getElementById("regUsername").value.trim(),
      email: document.getElementById("regEmail").value.trim(),
      password: document.getElementById("regPassword").value,
      company_name: document.getElementById("regCompany").value,
      requested_role: document.getElementById("regRole").value,
    };
    const res = await fetch("/auth/register-request", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.detail || "Registration failed");
    }
    msg.textContent = data.message;
  } catch (err) {
    msg.textContent = `Registration failed: ${String(err.message || err)}`;
  }
}

document.getElementById("btnLogin").addEventListener("click", login);
document.getElementById("btnRegister").addEventListener("click", registerRequest);
loadCompanies();

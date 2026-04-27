let departmentsByCompany = {};

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
  const [companiesRes, departmentsRes] = await Promise.all([fetch("/companies-public"), fetch("/meta/company-departments")]);
  const companies = await companiesRes.json();
  departmentsByCompany = await departmentsRes.json();
  const select = document.getElementById("regCompany");
  select.innerHTML = companies.map((c) => `<option value="${c.name}">${c.name}</option>`).join("");
  renderDepartments();
}

function renderDepartments() {
  const role = document.getElementById("regRole").value;
  const depSelect = document.getElementById("regDepartment");
  const depWrap = document.getElementById("regDepartmentWrap");
  if (role === "company_admin") {
    depSelect.innerHTML = `<option value="Administration">Administration</option>`;
    depSelect.value = "Administration";
    depSelect.disabled = true;
    depWrap.style.opacity = "0.7";
    return;
  }
  const departments = [
    "IT & Tech",
    "Construction & Heavy",
    "Logistics & Aviation",
    "Maritime",
    "Others",
  ];
  depSelect.disabled = false;
  depWrap.style.opacity = "1";
  depSelect.innerHTML = departments.map((d) => `<option value="${d}">${d}</option>`).join("");
}

async function registerRequest() {
  const msg = document.getElementById("regMsg");
  msg.textContent = "Submitting request...";
  msg.classList.remove("success");
  try {
    const payload = {
      full_name: document.getElementById("regFullName").value.trim(),
      username: document.getElementById("regUsername").value.trim(),
      email: document.getElementById("regEmail").value.trim(),
      password: document.getElementById("regPassword").value,
      company_name: document.getElementById("regCompany").value,
      department: document.getElementById("regDepartment").value,
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
    msg.classList.add("success");
  } catch (err) {
    msg.textContent = `Registration failed: ${String(err.message || err)}`;
  }
}

const loginPanel = document.getElementById("loginPanel");
const registerPanel = document.getElementById("registerPanel");

document.getElementById("showRegister").addEventListener("click", () => {
  loginPanel.style.display = "none";
  registerPanel.classList.add("visible");
});

document.getElementById("showLogin").addEventListener("click", () => {
  registerPanel.classList.remove("visible");
  registerPanel.style.display = "";
  loginPanel.style.display = "block";
  requestAnimationFrame(() => {
    registerPanel.style.display = "";
  });
});

document.getElementById("btnLogin").addEventListener("click", login);
document.getElementById("btnRegister").addEventListener("click", registerRequest);
document.getElementById("regRole").addEventListener("change", renderDepartments);
loadCompanies();

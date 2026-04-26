const user = JSON.parse(localStorage.getItem("azcon_user") || "null");

if (!user?.id) window.location.href = "/";

async function api(path, method = "GET", body = null) {
  const res = await fetch(path, {
    method,
    headers: { "Content-Type": "application/json", "x-user-id": String(user.id) },
    body: body ? JSON.stringify(body) : null,
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || "Request failed");
  return data;
}

function esc(x) {
  return String(x ?? "").replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;");
}


function applyRoleView() {
  document.querySelectorAll(".role-view").forEach((el) => {
    const roles = (el.dataset.roles || "").split(",");
    el.classList.toggle("hidden", !roles.includes(user.role));
  });
}

async function loadVendors() {
  const rows = await api("/vendors-marketplace");
  document.getElementById("vendorsOut").innerHTML = `<table class="table"><thead><tr><th>Vendor</th><th>Success Rate</th><th></th></tr></thead><tbody>${rows
    .map((v) => `<tr><td>${esc(v.vendor_name)}</td><td>${esc(v.success_rate)}%</td><td><button class="btn btn-small" onclick="loadVendorProfile(${v.vendor_id})">Bax</button></td></tr>`)
    .join("")}</tbody></table>`;
  const vendorSelect = document.getElementById("reqVendorId");
  vendorSelect.innerHTML = rows.map((v) => `<option value="${v.vendor_id}">${esc(v.vendor_name)}</option>`).join("");
}

window.loadVendorProfile = async function (vendorId) {
  const p = await api(`/vendors/${vendorId}/profile`);
  document.getElementById("vendorProfileOut").innerHTML = `
    <h4>${esc(p.vendor_name)}</h4>
    <p><strong>About:</strong> ${esc(p.about)}</p>
    <p><strong>Feedback:</strong> ${p.feedback.map((f) => `${esc(f.buyer)} (${f.rating}/5) - ${esc(f.comment)}`).join(" | ")}</p>
    <p><strong>Əvvəlki satışlar:</strong> ${p.previous_sales.map((s) => `${esc(s.company)} → ${esc(s.what_sold)}`).join(" | ")}</p>
  `;
};

async function refreshRequestOptions() {
  const rows = await api("/requests");
  const sel = document.getElementById("recommendReqId");
  sel.innerHTML = rows.map((r) => `<option value="${r.request_id}">${esc(r.title)} - ${esc(r.company_name)}</option>`).join("");
}


document.getElementById("btnManualNeed").onclick = async () => {
  const response = await api(`/catalog/expensive-items?company_name=${encodeURIComponent(user.company_name)}&department=${encodeURIComponent(user.department || "Satınalma")}`);
  document.getElementById("reqOut").innerHTML = `${response.items.map((x) => `• ${esc(x)}`).join("<br>")}<br><strong>${esc(response.manual_input_label)}</strong>`;
};

document.getElementById("btnCreateRequest").onclick = async () => {
  const payload = {
    title: document.getElementById("reqTitle").value,
    description: document.getElementById("reqDescription").value,
    quantity: Number(document.getElementById("reqQty").value),
    required_by: document.getElementById("reqDeliveryDate").value,
    budget_min: 0,
    budget_max: 0,
    item_type: document.getElementById("reqItemType").value,
    vendor_id: Number(document.getElementById("reqVendorId").value),
    delivery_date: document.getElementById("reqDeliveryDate").value,
    department: user.department,
  };
  const out = await api("/requests", "POST", payload);
  document.getElementById("reqOut").innerHTML = `Sifariş #${out.request_id} yaradıldı. Shipping: ${esc(out.shipping_cost)} ${
    out.shared_logistics_badge ? `<span class="badge ok">${esc(out.shared_logistics_badge)}</span>` : ""
  }`;
  await refreshRequestOptions();
};

document.getElementById("btnRecommend").onclick = async () => {
  const reqId = Number(document.getElementById("recommendReqId").value);
  const topN = Number(document.getElementById("topN").value);
  const out = await api(`/requests/${reqId}/recommend?top_n=${topN}`, "POST");
  document.getElementById("recommendOut").innerHTML = `<table class="table"><thead><tr><th>Vendor</th><th>Qiymət</th><th>Müddət</th><th>Score</th><th>İzah</th></tr></thead><tbody>${out.results
    .map((r) => `<tr><td>${esc(r.vendor_name)}</td><td>${esc(r.price)} ${esc(r.currency)}</td><td>${esc(r.lead_time_days)} gün</td><td>${esc(r.scores.total)}</td><td>${esc(r.reasoning)}</td></tr>`)
    .join("")}</tbody></table>`;
};

document.getElementById("btnLoadAnalytics").onclick = async () => {
  const c = user.company_name || "Bakı Metropoliteni QSC";
  const out = await api(`/analytics/company-expenses?company_name=${encodeURIComponent(c)}`);
  document.getElementById("analyticsOut").innerHTML = `<pre>${esc(JSON.stringify(out, null, 2))}</pre>`;
};


document.getElementById("btnLogout").onclick = () => {
  localStorage.removeItem("azcon_user");
  window.location.href = "/";
};

document.getElementById("userName").textContent = user.full_name;
document.getElementById("userRole").textContent = user.role;
document.getElementById("userCompany").textContent = user.company_name || "-";
document.getElementById("userDepartment").textContent = user.department || "-";
applyRoleView();
loadVendors();
refreshRequestOptions();

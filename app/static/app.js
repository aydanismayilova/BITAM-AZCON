const user = JSON.parse(localStorage.getItem("azcon_user") || "null");

if (!user || !user.id) {
  window.location.href = "/";
}

function headerUser() {
  return user.id;
}

async function api(path, method = "GET", body = null) {
  const res = await fetch(path, {
    method,
    headers: {
      "Content-Type": "application/json",
      "x-user-id": headerUser(),
    },
    body: body ? JSON.stringify(body) : null,
  });
  const parsed = await res.json();
  if (!res.ok) {
    const detail =
      typeof parsed?.detail === "string"
        ? parsed.detail
        : parsed?.detail
        ? JSON.stringify(parsed.detail)
        : JSON.stringify(parsed);
    throw new Error(detail || "Request failed");
  }
  return parsed;
}

function esc(value) {
  return String(value ?? "").replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;");
}

function write(id, html) {
  document.getElementById(id).innerHTML = html;
}

function notify(id, message) {
  write(id, `<span class="badge">${esc(message)}</span>`);
}

function errorText(err, fallback) {
  if (err && typeof err.message === "string" && err.message.trim()) {
    return err.message;
  }
  if (typeof err === "string") {
    return err;
  }
  try {
    return JSON.stringify(err);
  } catch {
    return fallback;
  }
}

const ROLE_SUBTITLE = {
  storage_holder: "Warehouse operations and shortage alerts.",
  procurement_decider: "Procurement decisions and AI-assisted supplier selection.",
  company_admin: "Company-wide operations and vendor onboarding.",
  platform_admin: "Cross-company governance and full operational visibility.",
};

let activeSectionId = "";

function updateSectionVisibility(preferredSectionId = "") {
  const sections = Array.from(document.querySelectorAll(".section-group")).filter(
    (section) => section.dataset.roleVisible === "true"
  );
  if (!sections.length) return;

  const allowedIds = sections.map((section) => section.id);
  const nextActiveId = allowedIds.includes(preferredSectionId)
    ? preferredSectionId
    : allowedIds.includes(activeSectionId)
    ? activeSectionId
    : allowedIds[0];

  activeSectionId = nextActiveId;

  document.querySelectorAll(".section-group").forEach((section) => {
    const shouldShow = section.dataset.roleVisible === "true" && section.id === activeSectionId;
    section.classList.toggle("hidden", !shouldShow);
  });

  document.querySelectorAll(".section-link").forEach((link) => {
    const target = document.getElementById(link.dataset.target);
    const isAllowed = target && target.dataset.roleVisible === "true";
    link.classList.toggle("hidden", !isAllowed);
    link.classList.toggle("active", isAllowed && link.dataset.target === activeSectionId);
  });
}

function applyRoleToSections() {
  document.querySelectorAll(".section-group").forEach((section) => {
    const hasVisibleCards = Array.from(section.querySelectorAll(".role-view")).some(
      (card) => !card.classList.contains("hidden")
    );
    section.dataset.roleVisible = hasVisibleCards ? "true" : "false";
  });
}

function updateSectionNavVisibility(selectedId = "") {
  document.querySelectorAll(".section-link").forEach((link) => {
    const target = document.getElementById(link.dataset.target);
    const isVisible = target && target.dataset.roleVisible === "true";
    link.classList.toggle("hidden", !isVisible);
  });
  updateSectionVisibility(selectedId);
}

function bindSectionNavigation() {
  document.querySelectorAll(".section-link").forEach((link) => {
    link.addEventListener("click", () => {
      const target = document.getElementById(link.dataset.target);
      if (!target || target.dataset.roleVisible !== "true") return;
      updateSectionVisibility(target.id);
    });
  });
}

function applyRoleView(role) {
  document.querySelectorAll(".role-view").forEach((el) => {
    const allowed = (el.dataset.roles || "").split(",");
    el.classList.toggle("hidden", !allowed.includes(role));
  });
  applyRoleToSections();
  updateSectionNavVisibility();
  document.getElementById("roleSubtitle").textContent = ROLE_SUBTITLE[role] || "";
}

async function refreshInventoryOptions() {
  const items = await api("/inventory");
  const select = document.getElementById("invItemName");
  if (!select) return;
  select.innerHTML = items
    .map((i) => `<option value="${esc(i.item_name)}">${esc(i.item_name)} (${esc(i.company_name)})</option>`)
    .join("");
}

async function refreshRequestOptions() {
  const requests = await api("/requests");
  const select = document.getElementById("recommendReqId");
  if (!select) return;
  select.innerHTML = requests
    .map(
      (r) =>
        `<option value="${esc(r.request_id)}">${esc(r.title)} - ${esc(r.company_name)} - ${esc(
          r.status
        )}</option>`
    )
    .join("");
}

async function refreshPendingRegistrations() {
  if (user.role !== "platform_admin") return;
  const outEl = document.getElementById("adminRequestsOut");
  if (!outEl) return;
  try {
    const rows = await api("/admin/registration-requests");
    if (!rows.length) {
      outEl.innerHTML = "No pending registration requests.";
      return;
    }
    outEl.innerHTML = `<table class="table"><thead><tr><th>Name</th><th>Username</th><th>Company</th><th>Role</th><th></th></tr></thead><tbody>${rows
      .map(
        (r) =>
          `<tr>
            <td>${esc(r.full_name)}</td>
            <td>${esc(r.username)}</td>
            <td>${esc(r.company_name)}</td>
            <td>${esc(r.requested_role)}</td>
            <td><button class="btn btn-primary btn-approve" data-id="${esc(r.request_id)}">Approve</button></td>
          </tr>`
      )
      .join("")}</tbody></table>`;
    document.querySelectorAll(".btn-approve").forEach((btn) => {
      btn.addEventListener("click", async () => {
        const requestId = btn.getAttribute("data-id");
        await api(`/admin/registration-requests/${requestId}/approve`, "POST");
        await refreshPendingRegistrations();
      });
    });
  } catch (err) {
    outEl.innerHTML = `Could not load requests. ${esc(errorText(err, "Unable to load requests"))}`;
  }
}

document.getElementById("btnCreateInventory").onclick = async () => {
  notify("invOut", "Creating inventory item...");
  try {
    const out = await api("/inventory", "POST", {
      name: document.getElementById("invName").value,
      quantity: Number(document.getElementById("invQty").value),
      min_threshold: Number(document.getElementById("invThreshold").value),
      unit: document.getElementById("invUnit").value,
    });
    write(
      "invOut",
      `<strong>${esc(out.name)}</strong> is created with stock <strong>${esc(out.quantity)}</strong> ${esc(out.unit)}.`
    );
    await refreshInventoryOptions();
  } catch (err) {
    write("invOut", `Action failed. ${esc(errorText(err, "Unable to create inventory item."))}`);
  }
};

document.getElementById("btnUpdateInventory").onclick = async () => {
  notify("invOut", "Updating stock...");
  try {
    const itemName = document.getElementById("invItemName").value;
    const out = await api("/inventory/update-by-name", "PATCH", {
      item_name: itemName,
      quantity: Number(document.getElementById("invNewQty").value),
    });
    write(
      "invOut",
      `<strong>${esc(out.item_name)}</strong> at <strong>${esc(out.company_name)}</strong> updated to <strong>${esc(
        out.quantity
      )}</strong>. ${
        out.shortage_alert_created
          ? '<span class="badge warn">Shortage alert sent to procurement</span>'
          : '<span class="badge ok">Stock level is healthy</span>'
      }`
    );
  } catch (err) {
    write("invOut", `Action failed. ${esc(errorText(err, "Unable to update inventory."))}`);
  }
};

document.getElementById("btnListShortages").onclick = async () => {
  notify("shortageOut", "Loading shortages...");
  try {
    const out = await api("/shortages");
    if (!out.length) {
      write("shortageOut", "No open shortages right now.");
      return;
    }
    write(
      "shortageOut",
      `<table class="table"><thead><tr><th>Item</th><th>Company</th><th>Current</th><th>Minimum</th></tr></thead><tbody>${out
        .map(
          (x) =>
            `<tr><td>${esc(x.item_name)}</td><td>${esc(x.company_name)}</td><td>${esc(
              x.current_quantity
            )}</td><td>${esc(x.minimum_quantity)}</td></tr>`
        )
        .join("")}</tbody></table>`
    );
  } catch (err) {
    write("shortageOut", `Could not load shortages. ${esc(errorText(err, "Unable to load shortages."))}`);
  }
};

document.getElementById("btnCreateRequest").onclick = async () => {
  notify("reqOut", "Creating purchase request...");
  try {
    const out = await api("/requests", "POST", {
      title: document.getElementById("reqTitle").value,
      description: document.getElementById("reqDescription").value,
      quantity: Number(document.getElementById("reqQty").value),
      budget_min: Number(document.getElementById("reqBudgetMin").value),
      budget_max: Number(document.getElementById("reqBudgetMax").value),
      required_by: document.getElementById("reqRequiredBy").value,
    });
    write("reqOut", `<strong>Request created:</strong> ${esc(out.title)} (${esc(out.quantity)} units).`);
    await refreshRequestOptions();
  } catch (err) {
    write("reqOut", `Could not create request. ${esc(errorText(err, "Unable to create request."))}`);
  }
};

document.getElementById("btnRecommend").onclick = async () => {
  notify("recommendOut", "Running AI recommendation...");
  try {
    const reqId = Number(document.getElementById("recommendReqId").value);
    const out = await api(`/requests/${reqId}/recommend`, "POST");
    if (!out.results.length) {
      write("recommendOut", "No matching options found.");
      return;
    }
    write(
      "recommendOut",
      `<div><strong>Recommended suppliers</strong> <span class="badge ok">${esc(out.source)}</span></div>
      <table class="table"><thead><tr><th>Supplier</th><th>Trusted</th><th>Price</th><th>Lead Time</th><th>Score</th></tr></thead><tbody>${out.results
        .map(
          (r) =>
            `<tr><td>${esc(r.vendor_name)}</td><td>${r.trusted ? "Yes" : "No"}</td><td>${esc(r.price)} ${esc(
              r.currency
            )}</td><td>${esc(r.lead_time_days)} days</td><td>${esc(r.scores.total)}</td></tr>`
        )
        .join("")}</tbody></table>`
    );
  } catch (err) {
    write("recommendOut", `Could not run recommendations. ${esc(errorText(err, "Unable to run recommendations."))}`);
  }
};

document.getElementById("btnCreateVendor").onclick = async () => {
  notify("vendorOut", "Creating vendor profile...");
  try {
    const out = await api("/vendors", "POST", {
      company_name: document.getElementById("vendorName").value,
      is_trusted: document.getElementById("vendorTrusted").value === "true",
      reliability_score: Number(document.getElementById("vendorReliability").value),
      quality_score: Number(document.getElementById("vendorQuality").value),
      delivery_score: 75,
      commercial_score: 75,
    });
    write(
      "vendorOut",
      `<strong>Vendor created:</strong> ${esc(out.company_name)} ${
        out.is_trusted ? '<span class="badge ok">Trusted</span>' : '<span class="badge">Standard</span>'
      }`
    );
    if (out.id) {
      document.getElementById("offerVendorId").value = out.id;
    }
  } catch (err) {
    write("vendorOut", `Could not create vendor. ${esc(errorText(err, "Unable to create vendor."))}`);
  }
};

document.getElementById("btnCreateOffer").onclick = async () => {
  notify("vendorOut", "Creating vendor offer...");
  try {
    const vendorId = Number(document.getElementById("offerVendorId").value);
    if (!vendorId) {
      throw new Error("Please provide a valid vendor ID.");
    }
    const out = await api("/vendor-offers", "POST", {
      vendor_id: vendorId,
      category: document.getElementById("offerCategory").value,
      title: document.getElementById("offerTitle").value,
      price: Number(document.getElementById("offerPrice").value),
      lead_time_days: Number(document.getElementById("offerLeadTime").value),
      quality_score: 80,
      currency: "USD",
    });
    write(
      "vendorOut",
      `<strong>Offer created:</strong> ${esc(out.title)} for ${esc(out.category)} at ${esc(out.price)} ${esc(
        out.currency
      )}`
    );
  } catch (err) {
    write("vendorOut", `Could not create offer. ${esc(errorText(err, "Unable to create offer."))}`);
  }
};
document.getElementById("btnLogout").addEventListener("click", () => {
  localStorage.removeItem("azcon_user");
  window.location.href = "/";
});

document.getElementById("userName").textContent = user.full_name;
document.getElementById("userRole").textContent = user.role.replaceAll("_", " ");
document.getElementById("userCompany").textContent = user.company_name || "All Companies";
bindSectionNavigation();
applyRoleView(user.role);
refreshInventoryOptions();
refreshRequestOptions();
refreshPendingRegistrations();

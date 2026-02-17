const outputEl = document.getElementById("output");
const statusEl = document.getElementById("status");
const refreshBtn = document.getElementById("refreshBtn");

const API_ROUTE = "/api/machine-info";
const RAW_API_BASE_URL = (window.APP_CONFIG?.API_URL || "").trim();

function resolveApiBaseUrl(value) {
  if (!value) {
    return "";
  }

  const trimmed = value.replace(/\/+$/, "");

  try {
    const parsed = new URL(trimmed, window.location.origin);

    // `haproxy` is a Docker-internal DNS name, not reachable from the browser.
    if (parsed.hostname === "haproxy") {
      return window.location.origin;
    }
  } catch (_error) {
    return trimmed;
  }

  return trimmed;
}

const API_BASE_URL = resolveApiBaseUrl(RAW_API_BASE_URL);
const API_URL = API_BASE_URL
  ? `${API_BASE_URL.replace(/\/+$/, "")}${API_ROUTE}`
  : API_ROUTE;

async function loadMachineInfo() {
  statusEl.classList.remove("error");
  statusEl.textContent = "Chargement...";

  try {
    const response = await fetch(API_URL);

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    const data = await response.json();
    outputEl.textContent = JSON.stringify(data, null, 2);
    statusEl.textContent = "OK";
  } catch (error) {
    statusEl.classList.add("error");
    statusEl.textContent = `Erreur: ${error.message}`;
    outputEl.textContent = "Impossible de recuperer la reponse du backend.";
  }
}

refreshBtn.addEventListener("click", loadMachineInfo);
loadMachineInfo();

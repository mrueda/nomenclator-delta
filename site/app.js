(function () {
  "use strict";

  const state = {
    metadata: null,
    summary: null,
    events: [],
    products: [],
    eventsByCn: new Map(),
    view: "changes",
    selectedCn: null,
  };

  const els = {};
  document.addEventListener("DOMContentLoaded", init);

  async function init() {
    ["comparisonPeriod", "datasetStatus", "searchInput", "clearSearch", "changeFilter",
      "presenceFilter", "addedCount", "removedCount", "changedCount", "priceCount",
      "viewEyebrow", "resultsTitle", "resultCount", "results", "detailPanel", "disclaimer"
    ].forEach(function (id) { els[id] = document.getElementById(id); });
    bindEvents();
    try {
      state.metadata = await fetchJson("data/metadata.json");
      const transition = state.metadata.transitions[0];
      const payloads = await Promise.all([
        fetchJson(`data/changes/${transition}.json`),
        fetchJson("data/indexes/products.json"),
      ]);
      state.summary = payloads[0].summary;
      state.events = payloads[0].events;
      state.products = payloads[1];
      indexEvents();
      populateFilters();
      renderHeader();
      render();
      openLinkedProduct();
    } catch (error) {
      els.datasetStatus.textContent = "No se pudieron cargar los datos";
      els.results.innerHTML = '<p class="error">Los datos estáticos no están disponibles. Vuelve a intentarlo más tarde.</p>';
    }
  }

  function bindEvents() {
    els.searchInput.addEventListener("input", render);
    els.clearSearch.addEventListener("click", function () {
      els.searchInput.value = "";
      els.changeFilter.value = "";
      els.presenceFilter.value = "";
      els.searchInput.focus();
      render();
    });
    els.changeFilter.addEventListener("change", render);
    els.presenceFilter.addEventListener("change", render);
    document.querySelectorAll(".nav-button").forEach(function (button) {
      button.addEventListener("click", function () {
        state.view = button.dataset.view;
        document.querySelectorAll(".nav-button").forEach(function (item) {
          item.classList.toggle("is-active", item === button);
        });
        render();
      });
    });
  }

  function indexEvents() {
    state.events.forEach(function (event) {
      if (!state.eventsByCn.has(event.cn)) state.eventsByCn.set(event.cn, []);
      state.eventsByCn.get(event.cn).push(event);
    });
  }

  function populateFilters() {
    const labels = new Map();
    state.events.forEach(function (event) { labels.set(event.change_type, event.change_label_es); });
    Array.from(labels.entries()).sort(function (a, b) { return a[1].localeCompare(b[1], "es"); })
      .forEach(function (entry) {
        const option = document.createElement("option");
        option.value = entry[0];
        option.textContent = entry[1];
        els.changeFilter.appendChild(option);
      });
  }

  function renderHeader() {
    const from = formatMonth(state.summary.from_snapshot);
    const to = formatMonth(state.summary.to_snapshot);
    els.comparisonPeriod.textContent = `${from} → ${to}`;
    els.datasetStatus.textContent = `${formatNumber(state.summary.to_product_count)} presentaciones en el último mes`;
    els.addedCount.textContent = formatNumber(state.summary.added);
    els.removedCount.textContent = formatNumber(state.summary.removed);
    els.changedCount.textContent = formatNumber(state.summary.changed_products);
    els.priceCount.textContent = formatNumber(state.summary.counts_by_type.PRICE_CHANGED || 0);
    els.disclaimer.textContent = state.metadata.disclaimer_es;
  }

  function render() {
    const query = normalizeSearch(els.searchInput.value);
    const changeType = els.changeFilter.value;
    const presence = els.presenceFilter.value;
    const filtered = state.products.filter(function (product) {
      const events = state.eventsByCn.get(product.cn) || [];
      if (!matchesView(events)) return false;
      if (changeType && !events.some(function (event) { return event.change_type === changeType; })) return false;
      if (presence === "present" && !product.present_in_latest) return false;
      if (presence === "absent" && product.present_in_latest) return false;
      if (!query) return true;
      const haystack = normalizeSearch([
        product.cn, product.medicine_name, product.laboratory,
        (product.active_ingredients || []).join(" "), product.status,
      ].join(" "));
      return query.split(/\s+/).every(function (term) { return haystack.includes(term); });
    });
    filtered.sort(sortProducts);
    renderViewHeading(filtered.length);
    renderResults(filtered);
  }

  function matchesView(events) {
    if (state.view === "added") return events.some(function (event) { return event.change_type === "PRODUCT_ADDED"; });
    if (state.view === "removed") return events.some(function (event) { return event.change_type === "PRODUCT_REMOVED"; });
    return events.length > 0;
  }

  function sortProducts(a, b) {
    const aEvents = state.eventsByCn.get(a.cn) || [];
    const bEvents = state.eventsByCn.get(b.cn) || [];
    const priority = function (events) {
      if (events.some(function (event) { return event.change_type === "PRODUCT_ADDED"; })) return 0;
      if (events.some(function (event) { return event.change_type === "PRODUCT_REMOVED"; })) return 1;
      if (events.some(function (event) { return event.change_type === "PRICE_CHANGED"; })) return 2;
      return 3;
    };
    return priority(aEvents) - priority(bEvents) || String(a.medicine_name).localeCompare(String(b.medicine_name), "es");
  }

  function renderViewHeading(count) {
    const labels = {
      changes: ["Cambios materiales", "Presentaciones con cambios"],
      added: ["Nuevas en el último mes", "Altas en la comparación"],
      removed: ["Ausentes en el último mes", "Bajas en la comparación"],
    };
    els.viewEyebrow.textContent = labels[state.view][0];
    els.resultsTitle.textContent = labels[state.view][1];
    els.resultCount.textContent = `${formatNumber(count)} ${count === 1 ? "resultado" : "resultados"}`;
  }

  function renderResults(products) {
    els.results.innerHTML = "";
    if (!products.length) {
      els.results.innerHTML = '<p class="empty">No hay presentaciones que coincidan con la búsqueda y los filtros seleccionados.</p>';
      return;
    }
    products.slice(0, 100).forEach(function (product) {
      const events = state.eventsByCn.get(product.cn) || [];
      const button = document.createElement("button");
      button.type = "button";
      button.className = `result-card${state.selectedCn === product.cn ? " is-selected" : ""}`;
      button.innerHTML = [
        `<span class="cn-badge">CN ${escapeHtml(product.cn)}</span>`,
        '<span class="result-main">',
        `<h3>${escapeHtml(product.medicine_name || "Presentación sin nombre")}</h3>`,
        `<p>${escapeHtml(product.laboratory || "Laboratorio no indicado")} · ${escapeHtml(formatIngredients(product.active_ingredients))}</p>`,
        "</span>",
        `<span class="change-chips">${eventChips(events)}</span>`,
      ].join("");
      button.setAttribute("aria-label", `Abrir historial del Código Nacional ${product.cn}`);
      button.addEventListener("click", function () { openProduct(product); });
      els.results.appendChild(button);
    });
    if (products.length > 100) {
      const note = document.createElement("p");
      note.className = "empty";
      note.textContent = `Se muestran los primeros 100 de ${formatNumber(products.length)} resultados. Acota la búsqueda para ver una presentación concreta.`;
      els.results.appendChild(note);
    }
  }

  async function openProduct(product) {
    state.selectedCn = product.cn;
    window.history.replaceState(null, "", `#cn=${product.cn}`);
    render();
    els.detailPanel.innerHTML = '<div class="detail-placeholder"><p>Cargando historial…</p></div>';
    try {
      const detail = await fetchJson(`data/products/${product.cn}.json`);
      renderDetail(product, detail);
      if (window.innerWidth < 920) els.detailPanel.scrollIntoView({ behavior: "smooth", block: "start" });
    } catch (error) {
      els.detailPanel.innerHTML = '<p class="error">No se pudo cargar el historial de esta presentación.</p>';
    }
  }

  function openLinkedProduct() {
    const match = window.location.hash.match(/^#cn=(\d{6})$/);
    if (!match) return;
    const product = state.products.find(function (item) { return item.cn === match[1] && item.has_changes; });
    if (product) openProduct(product);
  }

  function renderDetail(product, detail) {
    const current = detail.current;
    const events = detail.events.slice().sort(function (a, b) {
      return a.change_label_es.localeCompare(b.change_label_es, "es");
    });
    els.detailPanel.innerHTML = [
      '<div class="detail-content">',
      `<div class="detail-kicker"><span>Código Nacional ${escapeHtml(product.cn)}</span><span>${product.present_in_latest ? "Presente en el último mes" : "Ausente en el último mes"}</span></div>`,
      `<h2>${escapeHtml(current.medicine_name || product.medicine_name)}</h2>`,
      `<p class="detail-lab">${escapeHtml((current.laboratory && current.laboratory.name) || "Laboratorio no indicado")}</p>`,
      '<dl class="current-state">',
      stateField("Estado", current.status),
      stateField("Aportación", current.contribution),
      stateField("Principio activo", formatIngredients(current.active_ingredients)),
      stateField("PVP con IVA", formatPrice(current.prices && current.prices.retail_with_vat)),
      "</dl>",
      `<h3 class="timeline-title">Historial · ${events.length} ${events.length === 1 ? "cambio" : "cambios"}</h3>`,
      `<div class="timeline">${events.map(renderEvent).join("")}</div>`,
      renderProvenance(detail.sources),
      "</div>",
    ].join("");
  }

  function stateField(label, value) {
    return `<div><dt>${escapeHtml(label)}</dt><dd>${escapeHtml(displayValue(value))}</dd></div>`;
  }

  function renderEvent(event) {
    const simplePresence = event.change_type === "PRODUCT_ADDED" || event.change_type === "PRODUCT_REMOVED";
    const before = simplePresence && event.change_type === "PRODUCT_ADDED" ? "No figuraba" : formatEventValue(event, event.before);
    const after = simplePresence && event.change_type === "PRODUCT_REMOVED" ? "No figura" : formatEventValue(event, event.after);
    return [
      '<article class="event">',
      `<header><strong>${escapeHtml(event.change_label_es)}</strong><time>${escapeHtml(formatMonth(event.to_snapshot))}</time></header>`,
      `<p class="event-field">${escapeHtml(event.field_label_es)}</p>`,
      '<div class="value-change">',
      `<span class="value">${escapeHtml(before)}</span><span class="arrow">→</span>`,
      `<span class="value value--after">${escapeHtml(after)}</span>`,
      "</div></article>",
    ].join("");
  }

  function formatEventValue(event, value) {
    if (event.change_type === "PRICE_CHANGED" && value !== null && value !== undefined) {
      return formatPrice(value);
    }
    if (["listed_from", "listed_until"].includes(event.field) && value) {
      return formatDate(value);
    }
    return displayValue(value);
  }

  function renderProvenance(sources) {
    const sourceItems = Object.keys(sources || {}).sort().map(function (snapshot) {
      const source = sources[snapshot];
      const retrieved = source.retrieved_at ? formatDateTime(source.retrieved_at) : "fecha de recuperación no indicada";
      return `${formatMonth(snapshot)}: recuperada el ${retrieved}, SHA-256 ${String(source.sha256 || "").slice(0, 12)}…`;
    });
    return [
      '<div class="provenance"><strong>Procedencia</strong>',
      `<p>${escapeHtml(sourceItems.join(" · "))}</p>`,
      '<p>Exportaciones del <a href="https://www.sanidad.gob.es/profesionales/nomenclator.do" target="_blank" rel="noopener noreferrer">Nomenclátor de facturación del Ministerio de Sanidad</a>. Consulta siempre la fuente oficial para verificar la situación vigente.</p></div>',
    ].join("");
  }

  function eventChips(events) {
    const unique = [];
    const seen = new Set();
    events.forEach(function (event) {
      if (!seen.has(event.change_type)) { seen.add(event.change_type); unique.push(event); }
    });
    return unique.slice(0, 3).map(function (event) {
      const kind = event.change_type === "PRODUCT_ADDED" ? "added" :
        event.change_type === "PRODUCT_REMOVED" ? "removed" :
          event.change_type === "PRICE_CHANGED" ? "price" : "default";
      return `<span class="chip chip--${kind}">${escapeHtml(shortChangeLabel(event.change_type, event.change_label_es))}</span>`;
    }).join("") + (unique.length > 3 ? `<span class="chip">+${unique.length - 3}</span>` : "");
  }

  function shortChangeLabel(type, label) {
    if (type === "PRODUCT_ADDED") return "Alta";
    if (type === "PRODUCT_REMOVED") return "Baja";
    if (type === "PRICE_CHANGED") return "Precio";
    if (type === "STATUS_CHANGED") return "Estado";
    if (type === "LABORATORY_CHANGED") return "Laboratorio";
    return label.replace(/^Cambio de /, "");
  }

  function displayValue(value) {
    if (value === null || value === undefined || value === "") return "Sin dato";
    if (typeof value === "boolean") return value ? "Sí" : "No";
    if (Array.isArray(value)) return formatIngredients(value);
    if (typeof value === "object") {
      if (value.name || value.code) return [value.name, value.code ? `(${value.code})` : ""].filter(Boolean).join(" ");
      if (value.medicine_name) return value.medicine_name;
      return Object.values(value).filter(function (item) { return item !== null && item !== ""; }).map(displayValue).join(" · ") || "Sin dato";
    }
    return String(value);
  }

  function formatIngredients(values) { return values && values.length ? values.join(" + ") : "Principio activo no indicado"; }
  function formatPrice(value) { return value === null || value === undefined ? "Sin dato" : `${String(value).replace(".", ",")} €`; }
  function formatDate(value) {
    const date = new Date(`${value}T00:00:00`);
    return Number.isNaN(date.getTime()) ? String(value) : new Intl.DateTimeFormat("es-ES").format(date);
  }
  function formatDateTime(value) {
    const date = new Date(value);
    return Number.isNaN(date.getTime()) ? String(value) : new Intl.DateTimeFormat("es-ES", {
      dateStyle: "short", timeStyle: "short", timeZone: "Europe/Madrid",
    }).format(date);
  }
  function normalizeSearch(value) { return String(value || "").normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase().trim(); }
  function formatNumber(value) { return new Intl.NumberFormat("es-ES").format(Number(value || 0)); }
  function formatMonth(value) {
    const parts = String(value).split("-");
    if (parts.length !== 2) return String(value);
    const date = new Date(Number(parts[0]), Number(parts[1]) - 1, 1);
    const label = new Intl.DateTimeFormat("es-ES", { month: "long", year: "numeric" }).format(date);
    return label.charAt(0).toUpperCase() + label.slice(1);
  }
  function escapeHtml(value) {
    return String(value === null || value === undefined ? "" : value)
      .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;").replace(/'/g, "&#039;");
  }
  async function fetchJson(url) {
    const response = await fetch(url);
    if (!response.ok) throw new Error(`Error al cargar ${url}`);
    return response.json();
  }
}());

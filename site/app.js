(function () {
  "use strict";

  const state = {
    metadata: null,
    summary: null,
    events: [],
    products: [],
    eventsByCn: new Map(),
    transition: null,
    transitions: [],
    transitionPayloads: new Map(),
    transitionPromises: new Map(),
    loadingTransition: null,
    view: "changes",
    selectedCn: null,
    filteredProducts: [],
    visibleCount: 100,
    resultsKey: null,
  };

  const els = {};
  document.addEventListener("DOMContentLoaded", init);

  async function init() {
    ["periodSelect", "datasetStatus", "searchInput", "clearSearch", "changeFilter",
      "changesNavCount", "addedNavCount", "removedNavCount",
      "viewEyebrow", "resultsTitle", "resultCount", "results", "detailPanel", "disclaimer"
    ].forEach(function (id) { els[id] = document.getElementById(id); });
    try {
      bindEvents();
      const payloads = await Promise.all([
        fetchJson("data/metadata.json"),
        fetchJson("data/indexes/products.json"),
      ]);
      state.metadata = payloads[0];
      state.products = payloads[1];
      state.transitions = (state.metadata.transitions || []).slice().sort(compareTransitionIds);
      if (!state.transitions.length) throw new Error("No hay comparaciones publicadas");
      renderPeriodSelect();
      await loadTransition(state.transitions[state.transitions.length - 1]);
      if (!state.summary) return;
      openLinkedProduct();
    } catch (error) {
      els.datasetStatus.textContent = "No se pudieron cargar los datos";
      if (els.periodSelect) els.periodSelect.setAttribute("aria-busy", "false");
      els.results.innerHTML = '<p class="error">No se pudo iniciar la aplicación. Recarga la página; si el problema continúa, vuelve a intentarlo más tarde.</p>';
    }
  }

  function bindEvents() {
    document.getElementById("showMore").addEventListener("click", function () {
      const previousCount = state.visibleCount;
      state.visibleCount += 100;
      renderResults(state.filteredProducts);
      const firstNew = els.results.querySelectorAll(".result-card")[previousCount];
      if (firstNew) firstNew.focus({ preventScroll: true });
    });
    document.getElementById("exportCsv").addEventListener("click", exportFilteredCsv);
    els.searchInput.addEventListener("input", render);
    els.clearSearch.addEventListener("click", resetApplication);
    els.changeFilter.addEventListener("change", render);
    els.periodSelect.addEventListener("change", function () {
      loadTransition(els.periodSelect.value);
    });
    document.querySelectorAll(".nav-button").forEach(function (button) {
      button.addEventListener("click", function () {
        setView(button.dataset.view);
        render();
      });
    });
  }

  async function resetApplication() {
    state.visibleCount = 100;
    const latestTransition = state.transitions[state.transitions.length - 1];
    els.searchInput.value = "";
    els.changeFilter.value = "";
    state.selectedCn = null;
    setView("changes");
    window.history.replaceState(null, "", window.location.pathname + window.location.search);
    renderDetailPlaceholder();
    els.searchInput.focus();
    if (latestTransition && state.transition !== latestTransition) {
      await loadTransition(latestTransition);
      return;
    }
    if (state.summary) {
      renderHeader();
      renderPeriodSelect();
      render();
    }
  }

  function setView(view) {
    state.view = view;
    document.querySelectorAll(".nav-button").forEach(function (button) {
      const active = button.dataset.view === view;
      button.classList.toggle("is-active", active);
      button.setAttribute("aria-pressed", active ? "true" : "false");
    });
  }

  async function loadTransition(transition) {
    if (!state.transitions.includes(transition)) return;
    const previous = state.transition;
    state.loadingTransition = transition;
    document.getElementById("exportCsv").disabled = true;
    els.periodSelect.setAttribute("aria-busy", "true");
    els.datasetStatus.textContent = "Cargando la comparación…";
    renderPeriodSelect();
    try {
      const payload = await fetchTransition(transition);
      if (state.loadingTransition !== transition) return;
      state.transition = transition;
      state.summary = payload.summary;
      state.events = payload.events;
      state.selectedCn = null;
      if (previous && window.location.hash.match(/^#cn=\d{6}$/)) {
        window.history.replaceState(null, "", window.location.pathname + window.location.search);
      }
      indexEvents();
      populateFilters();
      renderHeader();
      renderPeriodSelect();
      render();
      renderDetailPlaceholder();
    } catch (error) {
      if (state.loadingTransition !== transition) return;
      state.transition = previous;
      if (previous && state.summary) {
        renderHeader();
        render();
        els.datasetStatus.textContent = "No se pudo cargar el periodo elegido; se mantiene la comparación anterior";
      } else {
        els.datasetStatus.textContent = "No se pudo cargar la comparación seleccionada";
        els.results.innerHTML = '<p class="error">No se pudo cargar este periodo. Vuelve a intentarlo más tarde.</p>';
      }
      renderPeriodSelect();
    } finally {
      if (state.loadingTransition === transition) {
        state.loadingTransition = null;
        document.getElementById("exportCsv").disabled = !state.filteredProducts.length;
        els.periodSelect.setAttribute("aria-busy", "false");
        renderPeriodSelect();
      }
    }
  }

  function fetchTransition(transition) {
    if (state.transitionPayloads.has(transition)) {
      return Promise.resolve(state.transitionPayloads.get(transition));
    }
    if (state.transitionPromises.has(transition)) return state.transitionPromises.get(transition);
    const promise = fetchJson(`data/changes/${transition}.json`).then(function (payload) {
      state.transitionPayloads.set(transition, payload);
      return payload;
    }).finally(function () {
      state.transitionPromises.delete(transition);
    });
    state.transitionPromises.set(transition, promise);
    return promise;
  }

  function renderPeriodSelect() {
    if (!state.transitions.length) return;
    const latest = state.transitions[state.transitions.length - 1];
    els.periodSelect.innerHTML = state.transitions.slice().reverse().map(function (transition) {
      const label = compactTransitionLabel(transition) + (transition === latest ? " · Último disponible" : "");
      return `<option value="${escapeHtml(transition)}">${escapeHtml(label)}</option>`;
    }).join("");
    els.periodSelect.value = state.loadingTransition || state.transition || latest;
    els.periodSelect.disabled = Boolean(state.loadingTransition);
  }

  function indexEvents() {
    state.eventsByCn = new Map();
    state.events.forEach(function (event) {
      if (!state.eventsByCn.has(event.cn)) state.eventsByCn.set(event.cn, []);
      state.eventsByCn.get(event.cn).push(event);
    });
  }

  function populateFilters() {
    const selected = els.changeFilter.value;
    els.changeFilter.innerHTML = '<option value="">Todos los cambios</option>';
    const labels = new Map();
    state.events.forEach(function (event) { labels.set(event.change_type, event.change_label_es); });
    Array.from(labels.entries()).sort(function (a, b) { return a[1].localeCompare(b[1], "es"); })
      .forEach(function (entry) {
        const option = document.createElement("option");
        option.value = entry[0];
        option.textContent = entry[1];
        els.changeFilter.appendChild(option);
      });
    if (Array.from(els.changeFilter.options).some(function (option) { return option.value === selected; })) {
      els.changeFilter.value = selected;
    }
  }

  function renderHeader() {
    const missing = [];
    const [year, month] = state.summary.from_snapshot.split("-").map(Number);
    const cursor = new Date(Date.UTC(year, month, 1));
    while (cursor.toISOString().slice(0, 7) < state.summary.to_snapshot) {
      missing.push(formatMonth(cursor.toISOString().slice(0, 7)));
      cursor.setUTCMonth(cursor.getUTCMonth() + 1);
    }
    const warning = document.getElementById("coverageWarning");
    warning.hidden = missing.length === 0;
    document.getElementById("coverageSummary").textContent = missing.length ? `Sin datos de ${missing.join(", ")}. Comparación acumulada: ${formatMonth(state.summary.from_snapshot)} → ${formatMonth(state.summary.to_snapshot)}.` : "";
    warning.querySelector("details").open = false;
    document.getElementById("dataFreshness").textContent = `Última publicación disponible: ${formatMonth(state.metadata.latest_snapshot)}`;
    const visibleChanges = state.summary.added + state.summary.removed + state.summary.changed_products;
    const priceChanges = (state.summary.counts_by_type || {}).PRICE_CHANGED || 0;
    els.datasetStatus.textContent = `${formatNumber(state.summary.to_product_count)} presentaciones en ${formatMonth(state.summary.to_snapshot)} · ${formatNumber(state.summary.changed_products)} modificadas · ${formatNumber(priceChanges)} cambios de precio`;
    els.changesNavCount.textContent = formatNumber(visibleChanges);
    els.addedNavCount.textContent = formatNumber(state.summary.added);
    els.removedNavCount.textContent = formatNumber(state.summary.removed);
    els.disclaimer.textContent = state.metadata.disclaimer_es;
  }

  function render() {
    if (!state.summary) return;
    const query = normalizeSearch(els.searchInput.value);
    const changeType = els.changeFilter.value;
    const resultsKey = JSON.stringify([state.transition, state.view, query, changeType]);
    if (resultsKey !== state.resultsKey) state.visibleCount = 100;
    state.resultsKey = resultsKey;
    const filtered = state.products.filter(function (product) {
      const events = state.eventsByCn.get(product.cn) || [];
      if (!matchesView(events, Boolean(query))) return false;
      if (changeType && !events.some(function (event) { return event.change_type === changeType; })) return false;
      if (!query) return true;
      const haystack = normalizeSearch([
        product.cn, product.medicine_name, product.laboratory,
        (product.active_ingredients || []).join(" "), product.status,
      ].join(" "));
      return query.split(/\s+/).every(function (term) { return haystack.includes(term); });
    });
    filtered.sort(sortProducts);
    state.filteredProducts = filtered;
    document.getElementById("exportCsv").disabled = !filtered.length || Boolean(state.loadingTransition);
    renderViewHeading(filtered.length, Boolean(query));
    document.getElementById("resultsPeriod").textContent = `${formatMonth(state.summary.from_snapshot)} → ${formatMonth(state.summary.to_snapshot)}`;
    renderResults(filtered);
  }

  function exportFilteredCsv() {
    if (state.loadingTransition || !state.summary || !state.filteredProducts.length) return;
    const rows = [["Código Nacional", "Nombre (índice más reciente)", "Laboratorio (índice más reciente)", "Periodo inicial", "Periodo final", "Cambios observados", "Advertencia de cobertura"]];
    state.filteredProducts.forEach(function (product) {
      const labels = (state.eventsByCn.get(product.cn) || [])
        .filter(function (event) { return !els.changeFilter.value || event.change_type === els.changeFilter.value; })
        .map(function (event) { return event.change_label_es; });
      rows.push([product.cn, product.medicine_name, product.laboratory,
        state.summary.from_snapshot, state.summary.to_snapshot,
        Array.from(new Set(labels)).join("; ") || "Sin cambios observados",
        document.getElementById("coverageSummary").textContent]);
    });
    const csv = rows.map(function (row) {
      return row.map(function (value) {
        let text = String(value == null ? "" : value);
        // Prevent spreadsheet formula execution in source-controlled text fields.
        if (/^[\s]*[=+@-]/.test(text) || /^[\t\r\n]/.test(text)) text = "'" + text;
        return '"' + text.replace(/"/g, '""') + '"';
      }).join(";");
    }).join("\r\n");
    const url = URL.createObjectURL(new Blob(["\uFEFF", csv], { type: "text/csv;charset=utf-8" }));
    const link = document.createElement("a");
    link.href = url;
    link.download = `nomenclator-${state.summary.from_snapshot}-${state.summary.to_snapshot}.csv`;
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.setTimeout(function () { URL.revokeObjectURL(url); }, 1000);
  }

  function matchesView(events, hasQuery) {
    if (state.view === "added") return events.some(function (event) { return event.change_type === "PRODUCT_ADDED"; });
    if (state.view === "removed") return events.some(function (event) { return event.change_type === "PRODUCT_REMOVED"; });
    return events.length > 0 || hasQuery;
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

  function renderViewHeading(count, hasQuery) {
    const labels = {
      changes: ["Cambios materiales", "Presentaciones con cambios"],
      added: ["Nuevas en el periodo seleccionado", "Altas en la comparación"],
      removed: ["Ausentes en el periodo seleccionado", "Bajas en la comparación"],
    };
    const searchingAll = hasQuery && state.view === "changes";
    els.viewEyebrow.textContent = searchingAll ? "Índice y cambios observados" : labels[state.view][0];
    els.resultsTitle.textContent = searchingAll ? "Resultados de búsqueda" : labels[state.view][1];
    els.resultCount.textContent = `${formatNumber(count)} ${count === 1 ? "resultado" : "resultados"}`;
  }

  function renderResults(products) {
    const shown = Math.min(state.visibleCount, products.length);
    document.getElementById("showMore").hidden = shown >= products.length;
    document.getElementById("shownCount").textContent = products.length ? `Se muestran ${formatNumber(shown)} de ${formatNumber(products.length)} resultados.` : "";
    els.results.innerHTML = "";
    if (!products.length) {
      els.results.innerHTML = '<p class="empty">No hay presentaciones que coincidan con la búsqueda y los filtros seleccionados.</p>';
      return;
    }
    products.slice(0, state.visibleCount).forEach(function (product) {
      const events = state.eventsByCn.get(product.cn) || [];
      const button = document.createElement("button");
      button.type = "button";
      button.className = `result-card${state.selectedCn === product.cn ? " is-selected" : ""}`;
      button.setAttribute("aria-pressed", state.selectedCn === product.cn ? "true" : "false");
      button.innerHTML = [
        `<span class="cn-badge">CN ${escapeHtml(product.cn)}</span>`,
        '<span class="result-main">',
        `<h3>${escapeHtml(product.medicine_name || "Presentación sin nombre")}</h3>`,
        `<p>${escapeHtml(product.laboratory || "Laboratorio no indicado")} · ${escapeHtml(formatIngredients(product.active_ingredients))}</p>`,
        "</span>",
        `<span class="change-chips">${eventChips(events)}</span>`,
      ].join("");
      button.setAttribute("aria-label", events.length ?
        `Abrir cambios del Código Nacional ${product.cn}` :
        `Abrir detalle sin cambios observados del Código Nacional ${product.cn}`);
      button.addEventListener("click", function () { openProduct(product); });
      els.results.appendChild(button);
    });
  }

  async function openProduct(product) {
    state.selectedCn = product.cn;
    window.history.replaceState(null, "", `#cn=${product.cn}`);
    render();
    const selectedEvents = state.eventsByCn.get(product.cn) || [];
    if (!selectedEvents.length) {
      renderUnchangedDetail(product);
      if (window.innerWidth < 920) els.detailPanel.scrollIntoView({ behavior: "smooth", block: "start" });
      return;
    }
    els.detailPanel.innerHTML = '<div class="detail-placeholder"><p>Cargando cambios…</p></div>';
    const requestedTransition = state.transition;
    const requestedCn = product.cn;
    try {
      const detail = await fetchJson(`data/products/${product.cn}.json`);
      if (state.transition !== requestedTransition || state.selectedCn !== requestedCn) return;
      renderDetail(product, detail);
      if (window.innerWidth < 920) els.detailPanel.scrollIntoView({ behavior: "smooth", block: "start" });
    } catch (error) {
      if (state.transition !== requestedTransition || state.selectedCn !== requestedCn) return;
      els.detailPanel.innerHTML = '<p class="error">No se pudo cargar el historial de esta presentación.</p>';
    }
  }

  function openLinkedProduct() {
    const match = window.location.hash.match(/^#cn=(\d{6})$/);
    if (!match) return;
    const product = state.products.find(function (item) { return item.cn === match[1]; });
    if (product) openProduct(product);
  }

  function renderDetail(product, detail) {
    const events = detail.events.filter(function (event) {
      return event.from_snapshot === state.summary.from_snapshot && event.to_snapshot === state.summary.to_snapshot;
    }).sort(function (a, b) {
      return a.change_label_es.localeCompare(b.change_label_es, "es");
    });
    let snapshot = (detail.snapshots || []).find(function (item) {
      return item.snapshot === state.summary.to_snapshot;
    });
    const removed = events.some(function (event) { return event.change_type === "PRODUCT_REMOVED"; });
    if (!snapshot && removed) {
      snapshot = (detail.snapshots || []).find(function (item) {
        return item.snapshot === state.summary.from_snapshot;
      });
    }
    const current = (snapshot && snapshot.state) || detail.current || {};
    const presentLabel = removed ? `Ausente en ${formatMonth(state.summary.to_snapshot)}` : `Presente en ${formatMonth(state.summary.to_snapshot)}`;
    els.detailPanel.innerHTML = [
      '<div class="detail-content">',
      `<div class="detail-kicker"><span>Código Nacional ${escapeHtml(product.cn)}</span><span>${escapeHtml(presentLabel)}</span></div>`,
      `<h2>${escapeHtml(current.medicine_name || product.medicine_name)}</h2>`,
      `<p class="detail-lab">${escapeHtml((current.laboratory && current.laboratory.name) || "Laboratorio no indicado")}</p>`,
      '<dl class="current-state">',
      stateField("Estado", current.status),
      stateField("Aportación", current.contribution),
      stateField("Principio activo", formatIngredients(current.active_ingredients)),
      stateField("PVP con IVA", formatPrice(current.prices && current.prices.retail_with_vat)),
      "</dl>",
      `<h3 class="timeline-title">Cambios observados · ${events.length} ${events.length === 1 ? "cambio" : "cambios"}</h3>`,
      `<div class="timeline">${events.map(renderEvent).join("")}</div>`,
      renderProvenance(detail.sources, [state.summary.from_snapshot, state.summary.to_snapshot]),
      "</div>",
    ].join("");
  }

  function renderUnchangedDetail(product) {
    const latest = state.metadata.latest_snapshot || state.metadata.data_as_of;
    const comparison = `${formatMonth(state.summary.from_snapshot)} → ${formatMonth(state.summary.to_snapshot)}`;
    els.detailPanel.innerHTML = [
      '<div class="detail-content">',
      `<div class="detail-kicker"><span>Código Nacional ${escapeHtml(product.cn)}</span><span>${product.present_in_latest ? "Presente en el último índice" : "Ausente en el último índice"}</span></div>`,
      `<h2>${escapeHtml(product.medicine_name || "Presentación sin nombre")}</h2>`,
      `<p class="detail-lab">${escapeHtml(product.laboratory || "Laboratorio no indicado")}</p>`,
      '<div class="unchanged-notice"><strong>Sin cambios observados</strong>',
      `<p>No se han detectado diferencias para este Código Nacional en la comparación ${escapeHtml(comparison)}.</p></div>`,
      '<dl class="current-state">',
      stateField("Estado", product.status),
      stateField("Situación", product.present_in_latest ? "Presente" : "Ausente"),
      stateField("Principio activo", formatIngredients(product.active_ingredients)),
      stateField("PVP con IVA", formatPrice(product.prices && product.prices.retail_with_vat)),
      "</dl>",
      '<div class="provenance"><strong>Procedencia y vigencia</strong>',
      `<p>Se muestra el estado del índice más reciente disponible (${escapeHtml(formatMonth(latest))}), que puede ser posterior al periodo comparado.</p>`,
      '<p>Datos procedentes del <a href="https://www.sanidad.gob.es/profesionales/nomenclator.do" target="_blank" rel="noopener noreferrer">Nomenclátor de facturación del Ministerio de Sanidad</a>. La ausencia de diferencias no confirma la situación vigente; consulta siempre la fuente oficial.</p></div>',
      "</div>",
    ].join("");
  }

  function renderDetailPlaceholder() {
    els.detailPanel.innerHTML = '<div class="detail-placeholder"><span aria-hidden="true">Δ</span><h2>Selecciona una presentación</h2><p>Aquí verás su estado y los cambios observados en el periodo seleccionado.</p></div>';
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
      `<header><strong>${escapeHtml(event.change_label_es)}</strong><span>${escapeHtml(formatMonth(event.from_snapshot))} → ${escapeHtml(formatMonth(event.to_snapshot))}</span></header>`,
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

  function renderProvenance(sources, snapshots) {
    const selected = new Set(snapshots || []);
    const sourceItems = Object.keys(sources || {}).filter(function (snapshot) {
      return !selected.size || selected.has(snapshot);
    }).sort().map(function (snapshot) {
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
    if (!events.length) return '<span class="chip chip--unchanged">Sin cambios observados</span>';
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
    return new Intl.DateTimeFormat("es-ES", { month: "long", year: "numeric" }).format(date);
  }
  function transitionParts(transition) {
    const parts = String(transition).split("_to_");
    return { from: parts[0] || "", to: parts[1] || "" };
  }
  function compareTransitionIds(a, b) {
    const aParts = transitionParts(a);
    const bParts = transitionParts(b);
    return aParts.to.localeCompare(bParts.to) || aParts.from.localeCompare(bParts.from);
  }
  function compactTransitionLabel(transition) {
    const parts = transitionParts(transition);
    const from = compactMonth(parts.from);
    const to = compactMonth(parts.to);
    const fromYear = parts.from.split("-")[0];
    const toYear = parts.to.split("-")[0];
    return fromYear === toYear ? `${from} → ${to} ${toYear}` : `${from} ${fromYear} → ${to} ${toYear}`;
  }
  function compactMonth(value) {
    const parts = String(value).split("-");
    const date = new Date(Number(parts[0]), Number(parts[1]) - 1, 1);
    const label = new Intl.DateTimeFormat("es-ES", { month: "short" }).format(date).replace(/\.$/, "");
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
